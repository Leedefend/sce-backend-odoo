#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "delivery_journey_role_matrix_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[delivery_journey_role_matrix_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    journeys = _as_dict(baseline.get("journeys"))
    state_files = _as_dict(baseline.get("state_files"))
    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)

    report_json = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/delivery_journey_role_matrix_report.json"
    )
    report_md = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/delivery_journey_role_matrix_report.md"
    )

    errors: list[str] = []
    report_rows: dict[str, dict[str, Any]] = {}

    for journey_key, config in journeys.items():
        row = _as_dict(config)
        role_code = _text(row.get("role_code"))
        required_scenes = [_text(item) for item in _as_list(row.get("required_scenes")) if _text(item)]
        state_rel = _text(state_files.get(role_code))
        if not role_code or not state_rel:
            errors.append(f"{journey_key}: missing role_code/state file mapping")
            continue

        state_path = ROOT / state_rel
        state = _load_json(state_path)
        if not state:
            errors.append(f"{journey_key}: missing or invalid state file {state_rel}")
            continue

        scene_count = _safe_int(state.get("scene_count"), 0)
        observed_scenes = {_text(item) for item in _as_list(state.get("scene_keys")) if _text(item)}
        matched_scenes = [scene for scene in required_scenes if scene in observed_scenes]
        missing_scenes = [scene for scene in required_scenes if scene not in observed_scenes]

        if scene_count < min_scene_count:
            errors.append(f"{journey_key}: scene_count {scene_count} < {min_scene_count}")
        if missing_scenes:
            errors.append(f"{journey_key}: missing required scenes {missing_scenes}")

        report_rows[journey_key] = {
            "role_code": role_code,
            "state_file": state_rel,
            "scene_count": scene_count,
            "required_scene_count": len(required_scenes),
            "matched_scene_count": len(matched_scenes),
            "missing_scenes": missing_scenes,
            "required_scenes": required_scenes,
        }

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "journeys": report_rows,
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
        },
    }

    lines = ["# Delivery Journey Role Matrix Report", ""]
    for journey_key in sorted(report_rows.keys()):
        row = _as_dict(report_rows.get(journey_key))
        lines.append(
            f"- {journey_key}: role=`{_text(row.get('role_code'))}` "
            f"matched=`{_safe_int(row.get('matched_scene_count'), 0)}/{_safe_int(row.get('required_scene_count'), 0)}`"
        )
        missing = _as_list(row.get("missing_scenes"))
        if missing:
            lines.append(f"  - missing: `{missing}`")
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md, "\n".join(lines) + "\n")

    if errors:
        print("[delivery_journey_role_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json)
        print(report_md)
        return 1

    print(report_json)
    print(report_md)
    print("[delivery_journey_role_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

