#!/usr/bin/env python3
"""Regression test: the corpus vocabulary checks fail closed, with a message, when their
vocabulary file is missing (review finding 4041895169). Each check is copied into a temp tree
that has a use case but no vocabulary file; it must exit 1, print a FAIL line naming the
missing file, and print no traceback."""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = [
    ("check_uc_dimensions.py", "DIMENSION-VOCABULARY.yaml"),
    ("check_uc_personas.py", "PERSONAS.yaml"),
]
UC = "scenario:\n  actor: {persona: platform-operator}\n  dimensions: {failure_mode: happy_path}\n"

def main():
    fails = []
    for script, vocab in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "tests"))
            os.makedirs(os.path.join(tmp, "dav", "use-cases", "compute"))
            shutil.copy(os.path.join(HERE, script), os.path.join(tmp, "tests", script))
            with open(os.path.join(tmp, "dav", "use-cases", "compute", "uc.yaml"), "w") as f:
                f.write(UC)
            r = subprocess.run([sys.executable, os.path.join(tmp, "tests", script)],
                               capture_output=True, text=True)
            out = r.stdout + r.stderr
            if r.returncode != 1:
                fails.append(f"{script}: exit {r.returncode}, want 1")
            if "Traceback" in out:
                fails.append(f"{script}: printed a traceback")
            if not ("FAIL" in out and vocab in out):
                fails.append(f"{script}: no FAIL line naming {vocab}")
    for f in fails:
        print("FAIL " + f)
    print(f"{len(CASES)} check(s) tested for fail-closed on a missing vocabulary, {len(fails)} failure(s)")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
