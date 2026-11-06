#!/usr/bin/env python3
"""Public text check for vois-so repositories.

Vois Studio does not name the third-party parts inside its engines on public
surfaces. This check stops a commit that names one of them. The list holds
salted SHA-256 hashes, not the names, so that the check itself does not
publish the list.

Usage:
    python3 public_text_check.py            # every file that git tracks
    python3 public_text_check.py FILE ...   # only these files

Put glob patterns, one for each line, in `.public-text-allow` at the
repository root to skip a file (for example a legal NOTICE file).

Exit codes: 0 = no finding, 1 = one or more findings, 2 = usage error.
"""

from __future__ import annotations

import fnmatch
import hashlib
import re
import subprocess
import sys
from pathlib import Path

SALT = "vois-public-text:v1:"

# Salted SHA-256 of each blocked term, normalized: lower case, letters and
# digits only, trailing digits removed. Ask the Vois Studio team to change it.
BLOCKED = {
    "b46a0c560f491950f8899599c4e3cf11cff9e7c784ed477e3ab7c958fb8b9135",
    "22ea7237e09342caa652ac9fec8c378189db627da79c15a8de47ffbccf340650",
    "1d5fadd30e6550e4e074401d3eeb08ba3821703dc8deba55e79ebc9ddca30291",
    "57697ff16436b4398c756f7bc4592156f680dba66f95fd3a1cef2325db1f898c",
    "c7158b13477c37ffb800da1b710ba7f91d9f71b1f13b8da47b19aa39fdd6b2a7",
    "2bea65a25c5d5c4a0a4f60c6e663b2d07df26d02ff3a052af5fbd1f90dc4355a",
    "ead1760215ccc81c8bea96050122203cef3ca9cbf4f952777464f7359d794e5c",
    "c3df5162c6ed4a81e0cd8ce2bba55d84fe59fcc6912dc8b93cc5be61f34c2cfb",
    "fada52c033a3292afdefc20a8941278eb02fad6bdae92f11c9db7d7a5069dd57",
    "2772f847542d23b4b119daf710ea5d64a6992c3b7e92fd53362755dc257d9075",
    "844c78d2277030d059464f8871bd7dbcda5393993047396efb08e6e88c90208e",
    "9785a650e740be1d83bde135522563284352c36e0587357e68c61d3c2f25b5fc",
    "be74e050773ae851db99165f2e7e9053958b521ccbcf5a55165404eab75a3caf",
}

TOKEN = re.compile(r"[a-z0-9]+")
MAX_BYTES = 2_000_000


def digest(term: str) -> str:
    return hashlib.sha256((SALT + term).encode("utf-8")).hexdigest()


def candidates(tokens: list[str]):
    """Yield (index, candidate) for each token and each pair of tokens."""
    for i, tok in enumerate(tokens):
        yield i, tok
        yield i, tok.rstrip("0123456789")
        if i + 1 < len(tokens):
            pair = tok + tokens[i + 1]
            yield i, pair
            yield i, pair.rstrip("0123456789")


def scan_line(line: str):
    lowered = line.lower()
    matches = list(TOKEN.finditer(lowered))
    tokens = [m.group(0) for m in matches]
    seen: set[int] = set()
    for i, cand in candidates(tokens):
        if i not in seen and cand and digest(cand) in BLOCKED:
            seen.add(i)
            yield matches[i].start() + 1, line[matches[i].start():matches[i].end()]


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True
    ).stdout.decode("utf-8", "replace")
    return [root / p for p in out.split("\0") if p]


def allow_patterns(root: Path) -> list[str]:
    allow = root / ".public-text-allow"
    if not allow.is_file():
        return []
    lines = allow.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.lstrip().startswith("#")]


def main(argv: list[str]) -> int:
    root = Path.cwd()
    try:
        files = [Path(a) for a in argv] if argv else tracked_files(root)
    except (OSError, subprocess.CalledProcessError) as err:
        print(f"public-text-check: cannot list files: {err}", file=sys.stderr)
        return 2
    patterns = allow_patterns(root)
    findings = 0
    for path in files:
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = path.as_posix()
        if any(fnmatch.fnmatch(rel, p) for p in patterns):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) > MAX_BYTES or b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", "replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for col, word in scan_line(line):
                findings += 1
                print(
                    f"{rel}:{lineno}:{col}: '{word}' names a part inside a Vois Studio "
                    "engine. Public text names the engine (Fast, Expressive, "
                    "Multilingual, Omni, Sonic or Craft), not its parts."
                )
    if findings:
        print(f"public-text-check: {findings} finding(s).", file=sys.stderr)
        return 1
    print("public-text-check: no findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
