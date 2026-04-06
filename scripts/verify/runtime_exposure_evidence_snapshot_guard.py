#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "artifacts" / "backend" / "runtime_exposure_evidence.json"
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "runtime_exposure_evidence_snapshot.json"


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


def _current_snapshot(evidence: Dict[str, Any]) -> Dict[str, Any]:
    coverage = evidence.get("coverage") if isinstance(evidence.get("coverage"), dict) else {}
    schema = evidence.get("projection_schema") if isinstance(evidence.get("projection_schema"), dict) else {}
    baseline = evidence.get("baseline") if isinstance(evidence.get("baseline"), dict) else {}
    return {
        "coverage": {
            "total_types": int(coverage.get("total_types") or 0),
            "covered_types": int(coverage.get("covered_types") or 0),
            "missing_types": int(coverage.get("missing_types") or 0),
        },
        "projection_schema": {
            "capability_list_field_count": int(schema.get("capability_list_field_count") or 0),
            "workspace_field_count": int(schema.get("workspace_field_count") or 0),
            "required_runtime_exposure_fields": schema.get("required_runtime_exposure_fields") if isinstance(schema.get("required_runtime_exposure_fields"), list) else [],
        },
        "baseline": {
            "schema_snapshot_match": bool(baseline.get("schema_snapshot_match")),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime exposure evidence snapshot guard")
    parser.add_argument("--update-baseline", action="store_true", help="Overwrite baseline with current evidence snapshot")
    args = parser.parse_args()

    evidence = _load_json(EVIDENCE)
    if not evidence:
        print("[runtime_exposure_evidence_snapshot_guard] FAIL")
        print(f"missing_or_invalid_evidence={EVIDENCE.relative_to(ROOT).as_posix()}")
        return 2

    current = _current_snapshot(evidence)

    if args.update_baseline:
        _save_json(BASELINE, current)
        print("[runtime_exposure_evidence_snapshot_guard] UPDATED")
        print(f"baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 0

    baseline = _load_json(BASELINE)
    if not baseline:
        print("[runtime_exposure_evidence_snapshot_guard] FAIL")
        print(f"missing_or_invalid_baseline={BASELINE.relative_to(ROOT).as_posix()}")
        return 2

    if baseline != current:
        print("[runtime_exposure_evidence_snapshot_guard] FAIL")
        print("baseline and current evidence snapshot mismatch")
        return 2

    print("[runtime_exposure_evidence_snapshot_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

