#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_MATRIX_REPORT = ROOT / "artifacts" / "backend" / "scene_base_contract_source_mix_role_matrix_report.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def main() -> int:
    report = _load_json(ROLE_MATRIX_REPORT)
    role_reports = report.get("role_reports") if isinstance(report.get("role_reports"), dict) else {}
    if not role_reports:
        print("[scene_delivery_runtime_gate_decision] RUN missing role matrix report")
        return 0

    scene_counts = {
        role: _safe_int(row.get("scene_count"), 0)
        for role, row in role_reports.items()
        if isinstance(row, dict)
    }
    if scene_counts and all(count <= 0 for count in scene_counts.values()):
        print(
            "[scene_delivery_runtime_gate_decision] SKIP strict scene delivery runtime boundary: "
            f"all role scene counts are 0 ({scene_counts})"
        )
        return 10

    print(f"[scene_delivery_runtime_gate_decision] RUN strict scene delivery runtime boundary: {scene_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
