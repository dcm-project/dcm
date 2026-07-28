#!/usr/bin/env python3
"""UC persona-vocabulary gate (mirror of udlm's PER-001/PER-002). Every use case's persona
references must resolve to the canonical persona set in dav/use-cases/PERSONAS.yaml (a canonical
id or a folded alias):
  - PER-001  scenario.actor.persona   — the persona that drives the use case (required)
  - PER-002  scenario.perspectives[]  — the additional personas it must be analyzed FROM (optional)
Also prints a non-failing COVERAGE line: canonical personas on no UC here. See the udlm copy for
the full rationale."""
import glob, os, sys, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB = os.path.join(ROOT, "dav", "use-cases", "PERSONAS.yaml")

def main():
    spec = yaml.safe_load(open(VOCAB, encoding="utf-8"))
    canon = {p["id"] for p in spec["personas"]}
    aliases = spec.get("folded_aliases") or {}
    resolvable = canon | set(aliases)
    c = lambda v: v if v in canon else aliases.get(v)
    fails, n, seen = [], 0, set()
    for path in sorted(glob.glob(os.path.join(ROOT, "dav", "use-cases", "**", "*.yaml"), recursive=True)):
        doc = yaml.safe_load(open(path, encoding="utf-8")) or {}
        sc = doc.get("scenario") or {}
        actor = (sc.get("actor") or {}).get("persona")
        if actor is None:
            continue
        n += 1
        rel = os.path.relpath(path, ROOT)
        if str(actor) not in resolvable:
            fails.append(f"[PER-001] {rel}: actor.persona={actor!r} off-vocabulary — add to PERSONAS.yaml first")
        else:
            seen.add(c(str(actor)))
        for p in (sc.get("perspectives") or []):
            if str(p) not in resolvable:
                fails.append(f"[PER-002] {rel}: perspective {p!r} off-vocabulary — add to PERSONAS.yaml first")
            else:
                seen.add(c(str(p)))
    for f in fails: print("FAIL " + f)
    uncovered = sorted(canon - seen)
    print(f"{n} use case(s) checked, {len(fails)} unresolved persona reference(s)")
    if uncovered:
        print(f"COVERAGE (informational): {len(uncovered)} persona(s) on no use case here — " + ", ".join(uncovered))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
