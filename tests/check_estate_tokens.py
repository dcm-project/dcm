#!/usr/bin/env python3
"""Estate-token guard: no personal-infrastructure identifiers in the public specs.

The specs are estate-neutral by policy — personal host/site names belong only in the private
estate-data repo. This gate scans every tracked text file, tokenizes on [a-z0-9]+ (lowercased),
and compares each token's sha256 against a denylist of HASHES (so the denylist itself leaks
nothing). A hit fails CI with the file/line; the plaintext token is NOT printed.

Wired into .github/workflows/validate.yml. Purge performed + gate added 2026-07-05.
"""
import hashlib
import re
import subprocess
import sys

DENY = {
    "14d3337700f95b77f60b30dd2a0948d232bff5d10df716101e1f5c321a50784c",
    "16f5107edd52050d007b73ec4e548be222959b20245f38012cbb4d8e2a542e74",
    "17e44715bf16ba1c9ff7c482c279f11bdb5749159ee3ea1060e50b295bfa5c2f",
    "1a5e497a2bfa7bfd8aab38a1d576ed882f4a82e855ec610880b4c186ec3f4e73",
    "234d6d31ecb9d31204f97fa13cf7c5af2dd45a1bdb862311e3ac259e98e8f796",
    "3b8c9f270579816f8675538796f438d7b25705ea9b0a77a78d81e0a30240827f",
    "446af8cff106a0b2fbac22a09ea0123f5c46a40b0666fed937ce49a6a9fdb0b2",
    "4f56851c1b69a1ee591be7f525910fb1bfaee89095c06ef1a90e9cfbe7ac20c9",
    "6cadf2f0f34dc55acde751c0f5e4b7cae56694f304c41bbd77ae351421884008",
    "7e7d8c699ee576ce17f16a12a4eae22b8b01a4e64ce15128c796e0a96c9cb704",
    "81ca6e9019679c4cf5073ede5f8a28527c869565b5d4725466978d459ae82d65",
    "9078e43e365a0d2849587c33e1623ccdbd92ad1ea81c5762414e9fbee6f20c03",
    "9f566c001b95e0357886c0a7dd79cadbde47a87fc5ed8c5137c9c939b6d5bf3c",
    "b1bf957a6f16444d406d7ff4e261dec297850777e865298822a19a7c9a78d4a3",
    "bb44bf07cf9a2db0554bba63a03d822c927deae77df101874496df5a6a3e896d",
    "d5a747cf10fc537e7b8ca64306fab4203f3c652b00ffab7cdb610e7ee6d5e63c",
    "e2284dc3b5535645288cde2bad818404be728fb8c9f70b055c0b52023b0ff0a0",
}

def main() -> int:
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.splitlines()
    hits = 0
    for f in files:
        try:
            text = open(f, encoding="utf-8", errors="ignore").read()
        except (IsADirectoryError, FileNotFoundError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for tok in re.findall(r"[a-z0-9]+", line.lower()):
                if hashlib.sha256(tok.encode()).hexdigest() in DENY:
                    print(f"FAIL [PII-001] {f}:{i}: contains a denylisted estate token (redacted)")
                    hits += 1
    print(f"\n{len(files)} files scanned, {hits} estate-token hit(s)")
    return 1 if hits else 0

if __name__ == "__main__":
    sys.exit(main())
