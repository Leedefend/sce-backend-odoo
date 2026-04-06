#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]

COVERAGE = ROOT / "artifacts" / "backend" / "native_capability_projection_coverage_report.json"
SCHEMA_SNAPSHOT = ROOT / "artifacts" / "backend" / "runtime_exposure_projection_schema_snapshot.json"
SCHEMA_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "runtime_exposure_projection_schema_snapshot.json"
EVIDENCE = ROOT / "artifacts" / "backend" / "runtime_exposure_evidence.json"
EVIDENCE_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "runtime_exposure_evidence_snapshot.json"

OUT_JSON = ROOT / "artifacts" / "backend" / "native_capability_projection_release_readiness_summary.json"
OUT_MD = ROOT / "artifacts" / "backend" / "native_capability_projection_release_readiness_summary.md"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_md(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Native Capability Projection Release Readiness Summary",
        "",
        f"- status: {payload.get('status', 'FAIL')}",
        f"- checks.coverage_ok: {payload.get('checks', {}).get('coverage_ok', False)}",
        f"- checks.schema_snapshot_match: {payload.get('checks', {}).get('schema_snapshot_match', False)}",
        f"- checks.evidence_snapshot_match: {payload.get('checks', {}).get('evidence_snapshot_match', False)}",
        f"- coverage.total_types: {payload.get('coverage', {}).get('total_types', 0)}",
        f"- coverage.covered_types: {payload.get('coverage', {}).get('covered_types', 0)}",
        f"- coverage.missing_types: {payload.get('coverage', {}).get('missing_types', 0)}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    coverage = _load_json(COVERAGE)
    schema_snapshot = _load_json(SCHEMA_SNAPSHOT)
    schema_baseline = _load_json(SCHEMA_BASELINE)
    evidence = _load_json(EVIDENCE)
    evidence_baseline = _load_json(EVIDENCE_BASELINE)

    coverage_summary = coverage.get("summary") if isinstance(coverage.get("summary"), dict) else {}
    missing_types = int(coverage_summary.get("missing_types") or 0)
    coverage_ok = bool(coverage) and missing_types == 0

    schema_snapshot_match = bool(schema_snapshot) and bool(schema_baseline) and schema_snapshot == schema_baseline

    evidence_current = {
        "coverage": evidence.get("coverage") if isinstance(evidence.get("coverage"), dict) else {},
        "projection_schema": evidence.get("projection_schema") if isinstance(evidence.get("projection_schema"), dict) else {},
        "baseline": evidence.get("baseline") if isinstance(evidence.get("baseline"), dict) else {},
    }
    evidence_snapshot_match = bool(evidence_baseline) and evidence_current == evidence_baseline

    payload: Dict[str, Any] = {
        "status": "PASS" if coverage_ok and schema_snapshot_match and evidence_snapshot_match else "FAIL",
        "checks": {
            "coverage_ok": coverage_ok,
            "schema_snapshot_match": schema_snapshot_match,
            "evidence_snapshot_match": evidence_snapshot_match,
        },
        "coverage": {
            "total_types": int(coverage_summary.get("total_types") or 0),
            "covered_types": int(coverage_summary.get("covered_types") or 0),
            "missing_types": missing_types,
        },
    }

    _save_json(OUT_JSON, payload)
    _write_md(OUT_MD, payload)

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if payload["status"] != "PASS":
        print("[native_capability_projection_release_readiness_summary_guard] FAIL")
        return 2
    print("[native_capability_projection_release_readiness_summary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

