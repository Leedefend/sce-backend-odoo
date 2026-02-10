#!/usr/bin/env python3
"""Guard against introducing new explicit `any` usage in frontend app code."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "frontend/apps/web/src"
BASELINE_PATH = ROOT / "scripts/verify/baselines/frontend_no_new_any.json"
ANY_RE = re.compile(r"\bany\b")


def _collect_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted(SRC_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".ts", ".vue"}:
            continue
        if path.name.endswith(".d.ts"):
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        counts[rel] = len(ANY_RE.findall(text))
    return counts


def _load_baseline() -> dict[str, int]:
    if not BASELINE_PATH.exists():
        return {}
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    files = payload.get("files") if isinstance(payload, dict) else {}
    if not isinstance(files, dict):
        return {}
    out: dict[str, int] = {}
    for key, value in files.items():
        try:
            out[str(key)] = int(value)
        except Exception:
            continue
    return out


def _write_baseline(current: dict[str, int]) -> None:
    data = {
        "files": current,
        "total": sum(current.values()),
    }
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    update_mode = str(sys.argv[1] if len(sys.argv) > 1 else "").strip().lower() in {"--update", "update"}
    current = _collect_counts()

    if update_mode:
        _write_baseline(current)
        print("[OK] no-new-any baseline updated")
        print(f"- file: {BASELINE_PATH.relative_to(ROOT)}")
        print(f"- files: {len(current)}")
        print(f"- total_any: {sum(current.values())}")
        return 0

    baseline = _load_baseline()
    if not baseline:
        print("[FAIL] no-new-any guard")
        print(f"- missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT)}")
        print("- run: python3 scripts/verify/no_new_any_guard.py --update")
        return 1

    errors: list[str] = []
    for rel_path, now_count in sorted(current.items()):
        base_count = int(baseline.get(rel_path, 0))
        if now_count > base_count:
            errors.append(f"{rel_path}: any {now_count} > baseline {base_count}")

    if errors:
        print("[FAIL] no-new-any guard")
        for err in errors:
            print(f"- {err}")
        return 1

    improved = sum(max(int(baseline.get(path, 0)) - count, 0) for path, count in current.items())
    print("[OK] no-new-any guard")
    print(f"- files_checked: {len(current)}")
    print(f"- total_any: {sum(current.values())}")
    print(f"- reduced_any_since_baseline: {improved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
