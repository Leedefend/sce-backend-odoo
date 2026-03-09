#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "frontend_page_block_visual_snapshot_guard.json"
REGISTRY = ROOT / "frontend/apps/web/src/app/pageBlockRegistry.ts"
BLOCK_DIR = ROOT / "frontend/apps/web/src/components/page/blocks"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_registry_keys(text: str) -> list[str]:
    keys = {m.group(1) for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*:", text)}
    return sorted(key for key in keys if key not in {"const", "export", "return"})


def _collect_snapshot() -> dict:
    registry_text = REGISTRY.read_text(encoding="utf-8", errors="ignore")
    block_files = sorted(BLOCK_DIR.glob("*.vue"))
    return {
        "registry_keys": _extract_registry_keys(registry_text),
        "block_files": {
            str(path.relative_to(ROOT).as_posix()): _sha256(path)
            for path in block_files
        },
        "registry_file": {
            str(REGISTRY.relative_to(ROOT).as_posix()): _sha256(REGISTRY),
        },
    }


def _load_baseline() -> dict:
    if not BASELINE.is_file():
        return {}
    try:
        payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _fail(errors: list[str]) -> int:
    print("[frontend_page_block_visual_snapshot_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    if not REGISTRY.is_file():
        return _fail([f"missing file: {REGISTRY.relative_to(ROOT).as_posix()}"])
    if not BLOCK_DIR.is_dir():
        return _fail([f"missing directory: {BLOCK_DIR.relative_to(ROOT).as_posix()}"])

    baseline = _load_baseline()
    if not baseline:
        return _fail([f"missing or invalid baseline: {BASELINE.relative_to(ROOT).as_posix()}"])

    current = _collect_snapshot()
    errors: list[str] = []

    if baseline.get("registry_keys") != current.get("registry_keys"):
        errors.append("registry_keys mismatch; update baseline after intentional registry change")

    baseline_files = baseline.get("block_files") if isinstance(baseline.get("block_files"), dict) else {}
    current_files = current.get("block_files") if isinstance(current.get("block_files"), dict) else {}

    missing_files = sorted(set(baseline_files.keys()) - set(current_files.keys()))
    extra_files = sorted(set(current_files.keys()) - set(baseline_files.keys()))
    if missing_files:
        errors.append(f"missing block files: {', '.join(missing_files)}")
    if extra_files:
        errors.append(f"unexpected block files: {', '.join(extra_files)}")

    for path, expected_hash in sorted(baseline_files.items()):
        current_hash = current_files.get(path)
        if current_hash and current_hash != expected_hash:
            errors.append(f"block file changed without baseline update: {path}")

    baseline_registry_file = baseline.get("registry_file") if isinstance(baseline.get("registry_file"), dict) else {}
    current_registry_file = current.get("registry_file") if isinstance(current.get("registry_file"), dict) else {}
    if baseline_registry_file != current_registry_file:
        errors.append("pageBlockRegistry.ts changed without baseline update")

    if errors:
        return _fail(errors)

    print("[frontend_page_block_visual_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
