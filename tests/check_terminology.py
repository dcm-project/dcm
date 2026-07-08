#!/usr/bin/env python3
"""Terminology guard: enforce the locked terminology decisions (AGENTS.md, 2026-06-30).

The DCM architecture converged on a small set of naming decisions. This gate keeps the
normative spec from drifting back to the retired terms. It scans tracked text files and
fails CI on a forbidden term, UNLESS the hit is (a) in a decision/history document that
legitimately discusses the retired term, or (b) on a line that explicitly documents the
change (carries a history marker like "formerly", "merged into", "superseded").

Decisions enforced (see AGENTS.md "Terminology decisions (locked 2026-06-30)"):
  - "Gating Policy" is NOT a standalone type — it merged into Validation Policy
    (enforcement_class: compliance is the hard gate).
  - "gatekeeper policy" is not used (OPA Gatekeeper collision).
  - "resource provider" is not used (proposed rename was reversed).
  - "fulfilled" is not the lifecycle state — the state is "Realized".
  - "likeC4" is not a DCM-native concept (customer-specific format).

Wired into .github/workflows/validate.yml and .gitlab-ci.yml.
"""
import re
import subprocess
import sys

# (label, compiled pattern). Patterns are matched case-insensitively per line.
RULES = [
    ("gating policy (merged into Validation Policy)", re.compile(r"gating\s+polic(?:y|ies)", re.I)),
    ("gatekeeper policy (OPA Gatekeeper collision)", re.compile(r"gatekeeper\s+polic(?:y|ies)", re.I)),
    ("resource provider (rename was reversed)", re.compile(r"resource\s+provider", re.I)),
    # "fulfilled" only as the lifecycle STATE — NOT the English verb ("a role is fulfilled by")
    # and NOT the act noun "fulfillment" (the verb "fulfill a request" is blessed by the anti-vocabulary).
    ("fulfilled (lifecycle state → use 'Realized')",
     re.compile(r"fulfilled\s+service|been\s+fulfilled|fulfilled\s+at\s+the\s+request", re.I)),
    ("likeC4 (customer-specific format, not DCM-native)", re.compile(r"likec4", re.I)),
]

# Whole-file exemptions: documents whose PURPOSE is to record decisions / proposals /
# open questions, and therefore legitimately name the retired terms as history.
EXEMPT_FILES = {
    "AGENTS.md",                                        # the terminology decisions themselves
    "CLAUDE.md",                                        # mirror of AGENTS.md
    "architecture/DISCUSSION-TOPICS.md",                # open-questions / decision log (historical)
    "docs/engineering/service-taxonomy-reconciliation.md",  # engineering proposal record (Service/Resource rename)
    "tests/check_terminology.py",                       # this gate names the forbidden terms
}

# Per-line exemption: a hit is allowed if the line explicitly documents the change.
HISTORY_MARKER = re.compile(
    r"formerly|previously|no longer|merged into|renamed|renames|reversed|superseded|"
    r"deprecat|was called|do not use|proposed but|2026-06-30|process provider|convert",
    re.I,
)

TEXT_SUFFIXES = (".md", ".json", ".yaml", ".yml")


def main() -> int:
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.splitlines()
    hits = 0
    for f in files:
        if f in EXEMPT_FILES or not f.endswith(TEXT_SUFFIXES):
            continue
        try:
            text = open(f, encoding="utf-8", errors="ignore").read()
        except (IsADirectoryError, FileNotFoundError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if HISTORY_MARKER.search(line):
                continue
            for label, pat in RULES:
                if pat.search(line):
                    print(f"FAIL [TERM-001] {f}:{i}: uses retired term — {label}")
                    hits += 1
    print(f"\n{len(files)} files scanned, {hits} terminology violation(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
