#!/usr/bin/env python3
"""Referential integrity gate (repo-cleanliness Q8): every relative markdown link resolves.

Scans all tracked *.md files; checks `](path)` targets (fragments allowed, http/mailto skipped)
resolve to an existing file or directory. Exit 1 on any broken link.
"""
import os, re, subprocess, sys

def main() -> int:
    files = subprocess.run(["git", "ls-files", "*.md"], capture_output=True, text=True).stdout.split()
    link = re.compile(r"\]\(([^)#\s]+)(#[^)\s]*)?\)")
    broken = 0
    for f in files:
        base = os.path.dirname(f)
        try:
            text = open(f, encoding="utf-8").read()
        except OSError:
            continue
        for m in link.finditer(text):
            p = m.group(1)
            if p.startswith(("http://", "https://", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(base, p))
            if not os.path.exists(target):
                print(f"BROKEN {f}: {p}")
                broken += 1
    print(f"{len(files)} files scanned, {broken} broken link(s)")
    return 1 if broken else 0

if __name__ == "__main__":
    sys.exit(main())
