#!/usr/bin/env python3
"""High-confidence tracked-file secret scan for CI.

This is intentionally narrow: it catches real token/private-key shapes while
avoiding noisy matches such as branch names containing "task-status".
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github_pat", re.compile("github_" + "pat_" + r"[A-Za-z0-9_]{20,}")),
    ("github_ghp", re.compile(r"(?<![A-Za-z0-9_])" + "ghp_" + r"[A-Za-z0-9_]{30,}")),
    ("openai_sk", re.compile(r"(?<![A-Za-z0-9_])" + "sk" + r"-[A-Za-z0-9_-]{32,}")),
    (
        "private_key",
        re.compile(
            "-----BEGIN "
            + r"(?:RSA |OPENSSH |EC |DSA )?"
            + "PRIVATE KEY-----"
        ),
    ),
]


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="ignore")


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        text = read_text(path)
        if text is None:
            continue
        rel = path.relative_to(ROOT)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{line_no}: {name}")
    if findings:
        print("[FAIL] high-confidence secret pattern found", file=sys.stderr)
        for item in findings:
            print(item, file=sys.stderr)
        return 1
    print("[OK] high-confidence secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
