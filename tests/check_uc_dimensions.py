#!/usr/bin/env python3
"""UC dimension-vocabulary gate (mirror of udlm's DIM-001). Every use case's
scenario.dimensions.* value must be in dav/use-cases/DIMENSION-VOCABULARY.yaml — the closed,
single-sourced vocabulary. See the udlm copy for the full rationale (2026-07-28 sweep F1)."""
import glob, os, sys, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB = os.path.join(ROOT, "dav", "use-cases", "DIMENSION-VOCABULARY.yaml")

def main():
    spec = yaml.safe_load(open(VOCAB, encoding="utf-8"))
    allowed = {k: set(v) for k, v in spec["dimensions"].items()}
    aliases = spec.get("folded_aliases") or {}
    fails, n = [], 0
    for path in sorted(glob.glob(os.path.join(ROOT, "dav", "use-cases", "**", "*.yaml"), recursive=True)):
        doc = yaml.safe_load(open(path, encoding="utf-8")) or {}
        dims = ((doc.get("scenario") or {}).get("dimensions")) or {}
        if not dims:
            continue  # not a use-case file (README, vocabulary, taxonomy)
        n += 1
        rel = os.path.relpath(path, ROOT)
        for dim, val in dims.items():
            if dim not in allowed:
                fails.append(f"{rel}: unknown dimension {dim!r}"); continue
            if str(val) not in allowed[dim]:
                hint = aliases.get(dim, {}).get(str(val))
                tip = f" — use {hint!r} (folded alias)" if hint else " — add to DIMENSION-VOCABULARY.yaml first if real"
                fails.append(f"{rel}: {dim}={val!r} off-vocabulary{tip}")
    for f in fails: print("FAIL [DIM-001] " + f)
    print(f"{n} use case(s) checked, {len(fails)} off-vocabulary value(s)")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
