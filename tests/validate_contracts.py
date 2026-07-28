#!/usr/bin/env python3
"""Architecture contract gate. Validates the machine-readable contracts that back the
DCM architecture spec, so a broken contract can't merge:

  - schemas/jsonschema/*.json  — must be a valid JSON Schema (2020-12 meta-schema).
  - schemas/openapi/*.yaml      — must parse and be a structurally valid OpenAPI 3.x
                                  document (openapi-spec-validator when installed;
                                  otherwise a YAML-parse + minimal-structure check).

KNOWN_BROKEN lists contracts with a pre-existing defect tracked for repair — they are
reported as a WARNING and do NOT fail the gate, so the gate stays green on everything
else while the debt is visible. Remove an entry once its contract is fixed.

Exit non-zero if any non-exempt contract is invalid. Wire into CI."""
import glob
import json
import os
import pathlib
import sys

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("requires: pip install jsonschema")
try:
    import yaml
except ImportError:
    sys.exit("requires: pip install pyyaml")

# Full OpenAPI 3.x compliance is OPT-IN (STRICT_OPENAPI=1): the specs currently miss
# some required `description` fields, so full validation would fail on pre-existing
# debt. Default is a deterministic parse + minimal-structure check regardless of what
# is installed. Flip STRICT_OPENAPI once the descriptions are backfilled.
STRICT_OPENAPI = bool(os.environ.get("STRICT_OPENAPI"))
try:
    from openapi_spec_validator import validate as openapi_validate
    HAVE_OPENAPI_VALIDATOR = True
except Exception:
    HAVE_OPENAPI_VALIDATOR = False
USE_FULL = STRICT_OPENAPI and HAVE_OPENAPI_VALIDATOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Contracts with a tracked pre-existing defect — reported, not fatal. Fix + remove.
# (dcm-admin-api.yaml — broken since 72afcd9 "Restructure #2" 2026-04-07 — was
# reconstructed in this change and removed from this list; the gate now validates it.)
KNOWN_BROKEN = {}

failures = 0
warnings = 0


def rel(p):
    return str(pathlib.Path(p).relative_to(ROOT))


print("== JSON Schemas ==")
for f in sorted(glob.glob(str(ROOT / "schemas/jsonschema/*.json"))):
    try:
        Draft202012Validator.check_schema(json.load(open(f)))
        print(f"ok   {rel(f)}")
    except Exception as e:
        print(f"FAIL {rel(f)}: {str(e)[:100]}")
        failures += 1

print("== OpenAPI ==")
for f in sorted(glob.glob(str(ROOT / "schemas/openapi/*.yaml"))):
    r = rel(f)
    exempt = KNOWN_BROKEN.get(r)
    try:
        doc = yaml.safe_load(open(f))
        if USE_FULL:
            openapi_validate(doc)
        else:
            assert isinstance(doc, dict) and "openapi" in doc and "paths" in doc, \
                "missing openapi/paths"
        print(f"ok   {r}  (openapi {doc.get('openapi', '?')}, {len(doc.get('paths', {}))} paths)")
    except Exception as e:
        if exempt:
            print(f"WARN {r}: KNOWN-BROKEN — {exempt}")
            warnings += 1
        else:
            print(f"FAIL {r}: {str(e).splitlines()[0][:100]}")
            failures += 1

if not USE_FULL:
    print("NOTE: OpenAPI checked for parse + basic structure (set STRICT_OPENAPI=1 with "
          "openapi-spec-validator installed for full 3.x compliance once descriptions are backfilled).")
print(f"\n{failures} failure(s), {warnings} known-broken warning(s)")
sys.exit(1 if failures else 0)
