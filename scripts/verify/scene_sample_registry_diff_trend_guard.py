#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_sample_registry_diff_trend_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


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


def _resolve_role_code(report: dict) -> str:
    sources = report.get("sources") if isinstance(report.get("sources"), dict) else {}
    snapshot_state_rel = _text(sources.get("snapshot_state"))
    snapshot_payload = _load_json(ROOT / snapshot_state_rel) if snapshot_state_rel else {}
    role_code = _text(snapshot_payload.get("role_code"))
    if role_code:
        return role_code
    return _text(os.getenv("SC_ROLE_CODE") or os.getenv("ROLE_CODE") or "unknown")


def _merge_policy(base: dict, ext: dict) -> dict:
    out = dict(base)
    for key, value in ext.items():
        out[key] = value
    return out


def _resolve_policy(baseline: dict, role_code: str) -> dict:
    default_policy = baseline.get("default") if isinstance(baseline.get("default"), dict) else {}
    role_map = baseline.get("role") if isinstance(baseline.get("role"), dict) else {}

    legacy_policy = {
        "max_missing_required_scene_count_growth": _safe_int(baseline.get("max_missing_required_scene_count_growth"), 3),
        "max_unexpected_scene_count_growth": _safe_int(baseline.get("max_unexpected_scene_count_growth"), 20),
        "max_unbound_matched_scene_count_growth": _safe_int(baseline.get("max_unbound_matched_scene_count_growth"), 2),
    }

    policy = _merge_policy(legacy_policy, default_policy)
    role_policy = role_map.get(role_code) if isinstance(role_map.get(role_code), dict) else {}
    policy = _merge_policy(policy, role_policy)
    return {
        "max_missing_required_scene_count_growth": _safe_int(policy.get("max_missing_required_scene_count_growth"), 3),
        "max_unexpected_scene_count_growth": _safe_int(policy.get("max_unexpected_scene_count_growth"), 20),
        "max_unbound_matched_scene_count_growth": _safe_int(policy.get("max_unbound_matched_scene_count_growth"), 2),
    }


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_sample_registry_diff_trend_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    report_path = ROOT / _text(baseline.get("report_source") or "artifacts/backend/scene_sample_registry_diff_report.json")
    state_path = ROOT / _text(baseline.get("state_file") or "artifacts/backend/scene_sample_registry_diff_trend_state.json")
    report = _load_json(report_path)
    if not report:
        print("[scene_sample_registry_diff_trend_guard] FAIL")
        print(f" - missing or invalid report: {report_path.relative_to(ROOT).as_posix()}")
        return 1

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    role_code = _resolve_role_code(report)
    policy = _resolve_policy(baseline, role_code)
    current = {
        "role_code": role_code,
        "missing_required_scene_count": _safe_int(summary.get("missing_required_scene_count"), 0),
        "unexpected_scene_count": _safe_int(summary.get("unexpected_scene_count"), 0),
        "unbound_matched_scene_count": _safe_int(summary.get("unbound_matched_scene_count"), 0),
        "policy": policy,
        "captured_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    previous = _load_json(state_path)
    errors: list[str] = []
    if previous:
        missing_growth = current["missing_required_scene_count"] - _safe_int(previous.get("missing_required_scene_count"), 0)
        unexpected_growth = current["unexpected_scene_count"] - _safe_int(previous.get("unexpected_scene_count"), 0)
        unbound_growth = current["unbound_matched_scene_count"] - _safe_int(previous.get("unbound_matched_scene_count"), 0)
        current["missing_required_scene_count_growth"] = missing_growth
        current["unexpected_scene_count_growth"] = unexpected_growth
        current["unbound_matched_scene_count_growth"] = unbound_growth

        max_missing_growth = _safe_int(policy.get("max_missing_required_scene_count_growth"), 3)
        max_unexpected_growth = _safe_int(policy.get("max_unexpected_scene_count_growth"), 20)
        max_unbound_growth = _safe_int(policy.get("max_unbound_matched_scene_count_growth"), 2)

        if missing_growth > max_missing_growth:
            errors.append(
                f"missing_required_scene_count growth too fast: {missing_growth} > {max_missing_growth}"
            )
        if unexpected_growth > max_unexpected_growth:
            errors.append(
                f"unexpected_scene_count growth too fast: {unexpected_growth} > {max_unexpected_growth}"
            )
        if unbound_growth > max_unbound_growth:
            errors.append(
                f"unbound_matched_scene_count growth too fast: {unbound_growth} > {max_unbound_growth}"
            )

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("[scene_sample_registry_diff_trend_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_sample_registry_diff_trend_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
