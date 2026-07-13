#!/usr/bin/env python3
"""Parse Python files without writing __pycache__ artifacts."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def iter_python_files(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        path = ROOT / raw
        if path.is_file() and path.suffix == ".py":
            out.append(path)
            continue
        if path.is_dir():
            out.extend(sorted(path.rglob("*.py")))
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python_syntax_check.py <file-or-directory> [...]", file=sys.stderr)
        return 2
    failures: list[str] = []
    for path in iter_python_files(argv):
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path.relative_to(ROOT)))
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)}:{exc.lineno}:{exc.offset}: {exc.msg}")
        except UnicodeDecodeError as exc:
            failures.append(f"{path.relative_to(ROOT)}: decode error: {exc}")
    if failures:
        print("[FAIL] Python syntax check failed", file=sys.stderr)
        for item in failures:
            print(item, file=sys.stderr)
        return 1
    print(f"[OK] Python syntax check passed ({len(iter_python_files(argv))} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
