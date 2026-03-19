#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_no_action_scene_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


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


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_no_action_scene_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    state_rel = _text(baseline.get("state_file"))
    state_path = ROOT / state_rel if state_rel else ROOT / "artifacts/backend/scene_registry_asset_snapshot_state.json"
    state = _load_json(state_path)
    if not state:
        print("[scene_no_action_scene_guard] FAIL")
        print(f" - missing or invalid state file: {state_path.relative_to(ROOT).as_posix()}")
        return 1

    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)
    min_action_total = _safe_int(baseline.get("min_action_total"), 1)
    max_no_action_scene_count = _safe_int(baseline.get("max_no_action_scene_count"), 0)

    scene_count = _safe_int(state.get("scene_count"), 0)
    per_scene = _as_dict(state.get("per_scene"))
    no_action_scenes: list[str] = []
    for scene_key, payload in per_scene.items():
        row = _as_dict(payload)
        action_total = _safe_int(row.get("action_total"), 0)
        if action_total < min_action_total:
            no_action_scenes.append(_text(scene_key))

    errors: list[str] = []
    if scene_count < min_scene_count:
        errors.append(f"scene_count below threshold: {scene_count} < {min_scene_count}")
    if len(no_action_scenes) > max_no_action_scene_count:
        errors.append(
            f"no-action scene count exceeds threshold: {len(no_action_scenes)} > {max_no_action_scene_count}; "
            f"samples={no_action_scenes[:10]}"
        )

    if errors:
        print("[scene_no_action_scene_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_no_action_scene_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

