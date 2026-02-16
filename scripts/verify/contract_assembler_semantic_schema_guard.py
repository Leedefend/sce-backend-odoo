#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "artifacts" / "backend" / "contract_assembler_semantic_smoke.json"


def _resolve_artifact_path() -> Path:
    candidates = []
    raw_dir = str(os.getenv("ARTIFACTS_DIR") or "").strip()
    if raw_dir:
        candidates.append(Path(raw_dir) / "backend" / "contract_assembler_semantic_smoke.json")
    candidates.append(Path("/mnt/artifacts/backend/contract_assembler_semantic_smoke.json"))
    candidates.append(DEFAULT_ARTIFACT)
    for path in candidates:
        if path.is_file():
            return path
    return DEFAULT_ARTIFACT


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    path = _resolve_artifact_path()
    report = _load_json(path)
    if not report:
        print("[contract_assembler_semantic_schema_guard] FAIL")
        print(f"missing or invalid artifact: {path}")
        return 1

    errors: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    roles = report.get("roles") if isinstance(report.get("roles"), list) else []
    if not isinstance(report.get("ok"), bool):
        errors.append("ok must be bool")
    for key in ("role_count", "passed_role_count", "failed_role_count", "error_count"):
        if key not in summary:
            errors.append(f"summary missing key: {key}")
    if not roles:
        errors.append("roles must be non-empty list")
    role_order = []
    for idx, row in enumerate(roles):
        if not isinstance(row, dict):
            errors.append(f"roles[{idx}] must be object")
            continue
        for key in ("role", "login", "ok", "user_mode", "hud_mode", "failure_reason"):
            if key not in row:
                errors.append(f"roles[{idx}] missing key: {key}")
        role_order.append(str(row.get("role") or ""))
        user_mode = row.get("user_mode") if isinstance(row.get("user_mode"), dict) else {}
        hud_mode = row.get("hud_mode") if isinstance(row.get("hud_mode"), dict) else {}
        for mode_name, mode_obj in (("user_mode", user_mode), ("hud_mode", hud_mode)):
            for section in ("system_init", "ui_contract"):
                if section not in mode_obj:
                    errors.append(f"roles[{idx}].{mode_name} missing section: {section}")

    if role_order != sorted(role_order):
        errors.append("roles must be sorted by role key for deterministic diff")

    if errors:
        print("[contract_assembler_semantic_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[contract_assembler_semantic_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
