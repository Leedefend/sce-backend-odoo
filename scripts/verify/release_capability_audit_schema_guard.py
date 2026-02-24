#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "release_capability_report.json"
TOP20_JSON = ROOT / "artifacts" / "backend" / "release_capability_top20_fix_backlog.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"missing artifact: {path.relative_to(ROOT).as_posix()}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"invalid json: {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"artifact must be object: {path.name}")
    return payload


def _ensure_fields(name: str, payload: dict, required: list[str]) -> list[str]:
    errors = []
    for field in required:
        if field not in payload:
            errors.append(f"{name}: missing field '{field}'")
    return errors


def main() -> int:
    errors: list[str] = []
    report = _load_json(REPORT_JSON)
    top20 = _load_json(TOP20_JSON)

    errors.extend(
        _ensure_fields(
            "release_capability_report",
            report,
            [
                "ok",
                "generated_at",
                "summary",
                "role_journeys",
                "runtime_capability_matrix",
                "scene_openability",
                "acl_runtime_probe",
                "acl_csv_risks",
            ],
        )
    )
    errors.extend(_ensure_fields("release_capability_top20_fix_backlog", top20, ["ok", "summary", "items"]))

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    for key in (
        "journey_failed_steps",
        "capability_key_count",
        "scene_open_failed_checks",
        "acl_runtime_high_risk_count",
        "acl_csv_risk_count",
    ):
        if key not in summary:
            errors.append(f"release_capability_report.summary missing '{key}'")

    role_journeys = report.get("role_journeys")
    if not isinstance(role_journeys, list) or len(role_journeys) < 3:
        errors.append("release_capability_report.role_journeys must include >=3 role reports")

    scene_openability = report.get("scene_openability") if isinstance(report.get("scene_openability"), dict) else {}
    sample_rows = scene_openability.get("rows")
    if not isinstance(sample_rows, list):
        errors.append("release_capability_report.scene_openability.rows must be list")

    acl_probe = report.get("acl_runtime_probe")
    if not isinstance(acl_probe, list) or not acl_probe:
        errors.append("release_capability_report.acl_runtime_probe must be non-empty list")

    items = top20.get("items")
    if not isinstance(items, list):
        errors.append("release_capability_top20_fix_backlog.items must be list")
    else:
        if len(items) > 20:
            errors.append(f"top20 backlog must contain <=20 items, got {len(items)}")
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"top20 item#{idx} must be object")
                continue
            for field in ("id", "title", "reproduction", "root_cause", "change_points", "acceptance"):
                if field not in item:
                    errors.append(f"top20 item#{idx} missing '{field}'")

    if errors:
        print("[release_capability_audit_schema_guard] FAIL")
        for err in errors:
            print(err)
        return 1

    print("[release_capability_audit_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
