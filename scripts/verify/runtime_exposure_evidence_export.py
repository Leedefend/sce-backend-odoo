#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]

COVERAGE = ROOT / "artifacts" / "backend" / "native_capability_projection_coverage_report.json"
SCHEMA_SNAPSHOT = ROOT / "artifacts" / "backend" / "runtime_exposure_projection_schema_snapshot.json"
BASELINE_SNAPSHOT = ROOT / "scripts" / "verify" / "baselines" / "runtime_exposure_projection_schema_snapshot.json"

OUT_JSON = ROOT / "artifacts" / "backend" / "runtime_exposure_evidence.json"
OUT_MD = ROOT / "artifacts" / "backend" / "runtime_exposure_evidence.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    coverage = _load_json(COVERAGE)
    schema_snapshot = _load_json(SCHEMA_SNAPSHOT)
    baseline_snapshot = _load_json(BASELINE_SNAPSHOT)

    coverage_summary = coverage.get("summary") if isinstance(coverage.get("summary"), dict) else {}
    list_fields = schema_snapshot.get("capability_list_projection_fields") if isinstance(schema_snapshot.get("capability_list_projection_fields"), list) else []
    workspace_fields = schema_snapshot.get("workspace_projection_fields") if isinstance(schema_snapshot.get("workspace_projection_fields"), list) else []
    required_fields = schema_snapshot.get("required_runtime_exposure_fields") if isinstance(schema_snapshot.get("required_runtime_exposure_fields"), list) else []

    snapshot_match = bool(schema_snapshot) and bool(baseline_snapshot) and schema_snapshot == baseline_snapshot

    payload: Dict[str, Any] = {
        "coverage": {
            "total_types": int(coverage_summary.get("total_types") or 0),
            "covered_types": int(coverage_summary.get("covered_types") or 0),
            "missing_types": int(coverage_summary.get("missing_types") or 0),
        },
        "projection_schema": {
            "capability_list_field_count": len(list_fields),
            "workspace_field_count": len(workspace_fields),
            "required_runtime_exposure_fields": required_fields,
        },
        "baseline": {
            "schema_snapshot_match": snapshot_match,
        },
        "status": "PASS" if int(coverage_summary.get("missing_types") or 0) == 0 and snapshot_match else "WARN",
    }

    _write_json(OUT_JSON, payload)

    lines = [
        "# Runtime Exposure Evidence",
        "",
        f"- coverage.total_types: {payload['coverage']['total_types']}",
        f"- coverage.covered_types: {payload['coverage']['covered_types']}",
        f"- coverage.missing_types: {payload['coverage']['missing_types']}",
        f"- schema.list_field_count: {payload['projection_schema']['capability_list_field_count']}",
        f"- schema.workspace_field_count: {payload['projection_schema']['workspace_field_count']}",
        f"- baseline.schema_snapshot_match: {payload['baseline']['schema_snapshot_match']}",
        f"- status: {payload['status']}",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    print("[runtime_exposure_evidence_export] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

