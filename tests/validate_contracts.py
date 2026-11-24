#!/usr/bin/env python3
"""Architecture contract gate. Validates the machine-readable contracts that back the
DCM architecture spec, so a broken contract can't merge:

  - schemas/jsonschema/*.json  must be a valid JSON Schema (2020-12 meta-schema).
  - schemas/openapi/*.yaml     must be a valid OpenAPI 3.x document
                               (openapi-spec-validator, required).
  - every $ref in either set must resolve: local "#/..." pointers and relative
    file references ("dcm-common.json#/$defs/...").
  - every security requirement in an OpenAPI document must name a scheme defined
    in components.securitySchemes (names are case-sensitive; the spec validator
    does not check this).
  - every name in a schema's `required` list must be one of its `properties`
    (when the schema lists properties and composes nothing), so a payload can
    actually satisfy it.

The gate fails closed:
  - every file in EXPECTED must exist, and each directory must yield at least one
    contract, so a moved or emptied directory cannot produce a green run that
    validated nothing;
  - a missing validator library is a failure, not a fallback to a weaker check.

Exit non-zero on any failure. Wired into CI (.github/workflows/validate.yml,
.gitlab-ci.yml)."""
import glob
import json
import pathlib
import sys
import urllib.parse

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("FAIL requires: pip install jsonschema")
try:
    import yaml
except ImportError:
    sys.exit("FAIL requires: pip install pyyaml")
try:
    from openapi_spec_validator import validate as openapi_validate
except ImportError:
    sys.exit("FAIL requires: pip install openapi-spec-validator")

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The contract set this repo ships. A file listed here that is missing fails the gate.
# Add a new contract here when it lands; extra files found by the globs are validated too.
EXPECTED = {
    "schemas/jsonschema": [
        "dcm-common.json",
        "dcm-entities.json",
        "dcm-events.json",
        "dcm-policies.json",
        "dcm-providers.json",
        "resource-type-spec-template.json",
    ],
    "schemas/openapi": [
        "dcm-admin-api.yaml",
        "dcm-consumer-api.yaml",
        "dcm-operator-api.yaml",
        "dcm-provider-callback-api.yaml",
    ],
}
PATTERNS = {"schemas/jsonschema": "*.json", "schemas/openapi": "*.yaml"}

failures = 0
_docs = {}


def rel(p):
    return str(pathlib.Path(p).resolve().relative_to(ROOT))


def fail(msg):
    global failures
    print(f"FAIL {msg}")
    failures += 1


def load(path):
    path = pathlib.Path(path).resolve()
    if path not in _docs:
        with open(path) as fh:
            _docs[path] = json.load(fh) if path.suffix == ".json" else yaml.safe_load(fh)
    return _docs[path]


def walk_refs(node, where=""):
    """Yield (location, ref) for every $ref string in a document."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str):
                yield where or "/", v
            else:
                yield from walk_refs(v, f"{where}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_refs(v, f"{where}/{i}")


def resolve_pointer(doc, fragment):
    node = doc
    if fragment in ("", "/"):
        return node
    for part in fragment.lstrip("/").split("/"):
        part = urllib.parse.unquote(part).replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            node = node[int(part)]
        else:
            node = node[part]
    return node


def unresolved_refs(path):
    """Return a list of "location -> ref" strings that do not resolve."""
    bad = []
    for where, ref in walk_refs(load(path)):
        target, _, fragment = ref.partition("#")
        if target.startswith(("http://", "https://")):
            bad.append(f"{where}: {ref} (remote refs are not allowed in this repo)")
            continue
        try:
            doc = load(pathlib.Path(path).parent / target) if target else load(path)
            resolve_pointer(doc, fragment)
        except (OSError, KeyError, IndexError, ValueError, TypeError):
            bad.append(f"{where}: {ref}")
    return bad


def report_refs(r, path):
    bad = unresolved_refs(path)
    for b in bad[:20]:
        print(f"       unresolved $ref {b}")
    if len(bad) > 20:
        print(f"       ... and {len(bad) - 20} more")
    if bad:
        fail(f"{r}: {len(bad)} unresolved $ref(s)")
    return not bad


COMPOSITION = ("allOf", "anyOf", "oneOf", "$ref", "if", "dependentSchemas")


def unsatisfiable_required(node, where=""):
    """Yield "location: name" for required names missing from the sibling properties."""
    if isinstance(node, dict):
        props, req = node.get("properties"), node.get("required")
        if (isinstance(props, dict) and isinstance(req, list)
                and not any(k in node for k in COMPOSITION)):
            for name in req:
                if name not in props:
                    yield f"{where or '/'}: {name}"
        for k, v in node.items():
            yield from unsatisfiable_required(v, f"{where}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from unsatisfiable_required(v, f"{where}/{i}")


def report_required(r, doc):
    bad = list(unsatisfiable_required(doc))
    for b in bad[:20]:
        print(f"       required property not defined {b}")
    if bad:
        fail(f"{r}: {len(bad)} required name(s) missing from properties")
    return not bad


def undefined_security(doc):
    """Return security requirement names that components.securitySchemes lacks."""
    defined = set((doc.get("components") or {}).get("securitySchemes") or {})
    used = []
    reqs = [("/security", doc.get("security") or [])]
    for path, item in (doc.get("paths") or {}).items():
        for method, op in (item or {}).items():
            if isinstance(op, dict) and "security" in op:
                reqs.append((f"{method.upper()} {path}", op["security"] or []))
    for where, req_list in reqs:
        for req in req_list:
            for name in req:
                if name not in defined:
                    used.append(f"{where}: {name}")
    return used


def collect(directory):
    found = sorted(glob.glob(str(ROOT / directory / PATTERNS[directory])))
    names = {pathlib.Path(f).name for f in found}
    for name in EXPECTED[directory]:
        if name not in names:
            fail(f"{directory}/{name}: expected contract is missing")
    if not found:
        fail(f"{directory}: no contracts found, refusing to pass on an empty set")
    return found


validated = 0

print("== JSON Schemas ==")
for f in collect("schemas/jsonschema"):
    r = rel(f)
    try:
        Draft202012Validator.check_schema(load(f))
    except Exception as e:
        fail(f"{r}: {str(e).splitlines()[0][:120]}")
        continue
    refs_ok = report_refs(r, f)
    if report_required(r, load(f)) and refs_ok:
        print(f"ok   {r}")
    validated += 1

print("== OpenAPI ==")
for f in collect("schemas/openapi"):
    r = rel(f)
    try:
        doc = load(f)
        assert isinstance(doc, dict) and "openapi" in doc, "not an OpenAPI document"
    except Exception as e:
        fail(f"{r}: does not parse: {str(e).splitlines()[0][:120]}")
        continue
    refs_ok = report_refs(r, f)
    required_ok = report_required(r, doc)
    bad_sec = undefined_security(doc)
    for b in bad_sec[:20]:
        print(f"       undefined security scheme {b}")
    if bad_sec:
        fail(f"{r}: {len(bad_sec)} security requirement(s) name an undefined scheme")
    try:
        openapi_validate(doc, base_uri=pathlib.Path(f).resolve().as_uri())
        spec_ok = True
    except Exception as e:
        spec_ok = False
        fail(f"{r}: {str(e).splitlines()[0][:160]}")
    if refs_ok and required_ok and spec_ok and not bad_sec:
        print(f"ok   {r}  (openapi {doc['openapi']}, {len(doc.get('paths', {}))} paths)")
    validated += 1

print(f"\n{validated} contract(s) checked, {failures} failure(s)")
sys.exit(1 if failures or not validated else 0)
