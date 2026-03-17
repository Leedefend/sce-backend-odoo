#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_CANDIDATES = [
    "artifacts/backend/scene_product_delivery_readiness_report.json",
    "artifacts/backend/scene_base_contract_source_mix_role_matrix_report.json",
    "artifacts/backend/scene_base_contract_source_mix_report.json",
    "artifacts/backend/scene_sample_registry_diff_report.json",
    "artifacts/backend/scene_governance_history_report.json",
]


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _report_status(path: Path) -> tuple[bool, list[str], dict]:
    payload = _load_json(path)
    if not payload:
        return False, ["missing_or_invalid_report"], {}
    ok = bool(payload.get("ok", False))
    errors = [str(item) for item in _as_list(payload.get("errors")) if str(item)]
    if not errors and not ok:
        summary = _as_dict(payload.get("summary"))
        errors = [f"summary={json.dumps(summary, ensure_ascii=False)}"] if summary else ["ok=false"]
    return ok, errors, payload


def main() -> int:
    failed: list[dict[str, Any]] = []
    checked = 0
    for rel in REPORT_CANDIDATES:
        path = ROOT / rel
        if not path.exists():
            continue
        checked += 1
        ok, errors, payload = _report_status(path)
        if ok:
            continue
        failed.append(
            {
                "path": rel,
                "errors": errors,
                "summary": _as_dict(payload.get("summary")),
            }
        )

    print("[scene_delivery_failure_brief]")
    print(f"checked_reports={checked}")
    if not failed:
        print("failed_reports=0")
        print("status=NO_FAILURE_REPORT_DETECTED")
        return 0

    print(f"failed_reports={len(failed)}")
    for row in failed:
        print(f"- report={row['path']}")
        for item in row.get("errors") or []:
            print(f"  error={item}")
        summary = _as_dict(row.get("summary"))
        if summary:
            print(f"  summary={json.dumps(summary, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

