#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "engineering_convergence" / "complexity_baseline_lock.json"


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def main() -> int:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, dict) or not files:
        print(f"[ERROR] invalid complexity baseline lock: {BASELINE.relative_to(ROOT)}", file=sys.stderr)
        return 2

    errors: list[str] = []
    checked = 0
    for rel_path, spec in sorted(files.items()):
        if not isinstance(spec, dict):
            errors.append(f"{rel_path}: invalid baseline spec")
            continue
        limit = int(spec.get("max_lines") or 0)
        path = ROOT / rel_path
        if limit <= 0:
            errors.append(f"{rel_path}: max_lines must be positive")
            continue
        if not path.is_file():
            errors.append(f"{rel_path}: file missing")
            continue
        lines = line_count(path)
        checked += 1
        if lines > limit:
            errors.append(f"{rel_path}: line count increased to {lines}, allowed {limit}")

    if errors:
        print("[complexity_baseline_lock] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"[complexity_baseline_lock] PASS checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
