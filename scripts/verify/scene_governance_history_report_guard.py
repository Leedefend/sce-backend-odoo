#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUEUE_BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_asset_queue_trend_guard.json"
CONSUMPTION_BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_ready_consumption_trend_guard.json"
REPORT_BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_governance_history_report_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_state_path(default_path: Path, baseline: dict) -> Path:
    raw = str(baseline.get("state_file") or "").strip()
    if not raw:
        return default_path
    return ROOT / raw


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    if isinstance(value, (int, float)):
        return value != 0
    return False


def _parse_iso_ts(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    queue_baseline = _load_json(QUEUE_BASELINE_PATH)
    consumption_baseline = _load_json(CONSUMPTION_BASELINE_PATH)
    report_baseline = _load_json(REPORT_BASELINE_PATH)
    if not queue_baseline:
        errors.append(f"missing or invalid baseline: {QUEUE_BASELINE_PATH.relative_to(ROOT).as_posix()}")
    if not consumption_baseline:
        errors.append(f"missing or invalid baseline: {CONSUMPTION_BASELINE_PATH.relative_to(ROOT).as_posix()}")
    if not report_baseline:
        errors.append(f"missing or invalid baseline: {REPORT_BASELINE_PATH.relative_to(ROOT).as_posix()}")
    if errors:
        print("[scene_governance_history_report_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    queue_state_path = _resolve_state_path(ROOT / "artifacts" / "backend" / "scene_asset_queue_trend_state.json", queue_baseline)
    consumption_state_path = _resolve_state_path(
        ROOT / "artifacts" / "backend" / "scene_ready_consumption_trend_state.json", consumption_baseline
    )

    queue_state = _load_json(queue_state_path)
    consumption_state = _load_json(consumption_state_path)
    if not queue_state:
        errors.append(f"missing or invalid queue trend state: {queue_state_path.relative_to(ROOT).as_posix()}")
    if not consumption_state:
        errors.append(f"missing or invalid consumption trend state: {consumption_state_path.relative_to(ROOT).as_posix()}")
    if errors:
        print("[scene_governance_history_report_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    queue_size = _safe_int(queue_state.get("queue_size"), 0)
    queue_growth = _safe_int(queue_state.get("queue_growth"), 0)
    queue_remaining = _safe_int(queue_state.get("remaining_count"), 0)

    consumption_enabled = _safe_bool(consumption_state.get("enabled"))
    scene_count = _safe_int(consumption_state.get("scene_count"), 0)
    scene_type_count = _safe_int(consumption_state.get("scene_type_count"), 0)
    aggregate_base_search_rate = _safe_float(consumption_state.get("aggregate_base_search_rate"), 0.0)
    aggregate_action_surface_rate = _safe_float(consumption_state.get("aggregate_action_surface_rate"), 0.0)
    aggregate_base_search_rate_drop = _safe_float(consumption_state.get("aggregate_base_search_rate_drop"), 0.0)
    aggregate_action_surface_rate_drop = _safe_float(consumption_state.get("aggregate_action_surface_rate_drop"), 0.0)

    max_queue_size = _safe_int(queue_baseline.get("max_queue_size"), 500)
    max_growth_per_run = _safe_int(queue_baseline.get("max_growth_per_run"), 200)
    min_scene_count = _safe_int(consumption_baseline.get("min_scene_count"), 1)
    min_scene_type_count = _safe_int(consumption_baseline.get("min_scene_type_count"), 1)
    min_aggregate_base_search_rate = _safe_float(consumption_baseline.get("min_aggregate_base_search_rate"), 0.0)
    min_aggregate_action_surface_rate = _safe_float(consumption_baseline.get("min_aggregate_action_surface_rate"), 0.0)
    max_base_search_rate_drop_per_run = _safe_float(consumption_baseline.get("max_base_search_rate_drop_per_run"), 0.35)
    max_action_surface_rate_drop_per_run = _safe_float(consumption_baseline.get("max_action_surface_rate_drop_per_run"), 0.35)

    require_queue_policy_alignment = _safe_bool(report_baseline.get("require_queue_policy_alignment"))
    require_consumption_policy_alignment = _safe_bool(report_baseline.get("require_consumption_policy_alignment"))
    max_capture_time_skew_seconds = _safe_int(report_baseline.get("max_capture_time_skew_seconds"), 900)

    queue_policy_aligned = queue_size <= max_queue_size and queue_growth <= max_growth_per_run
    consumption_policy_aligned = True
    if consumption_enabled:
        consumption_policy_aligned = (
            scene_count >= min_scene_count
            and scene_type_count >= min_scene_type_count
            and aggregate_base_search_rate >= min_aggregate_base_search_rate
            and aggregate_action_surface_rate >= min_aggregate_action_surface_rate
        )
    drop_policy_aligned = (
        aggregate_base_search_rate_drop <= max_base_search_rate_drop_per_run
        and aggregate_action_surface_rate_drop <= max_action_surface_rate_drop_per_run
    )

    queue_captured_at = str(queue_state.get("captured_at") or "")
    consumption_captured_at = str(consumption_state.get("captured_at") or "")
    queue_ts = _parse_iso_ts(queue_captured_at)
    consumption_ts = _parse_iso_ts(consumption_captured_at)
    capture_time_skew_seconds = -1
    if queue_ts is not None and consumption_ts is not None:
        capture_time_skew_seconds = int(abs((queue_ts - consumption_ts).total_seconds()))
    capture_time_skew_aligned = capture_time_skew_seconds >= 0 and capture_time_skew_seconds <= max_capture_time_skew_seconds

    if require_queue_policy_alignment and not queue_policy_aligned:
        errors.append("queue trend violates baseline policy")
    if require_consumption_policy_alignment and not consumption_policy_aligned:
        errors.append("consumption trend violates baseline policy when enabled")
    if not drop_policy_aligned:
        errors.append("consumption drop exceeds baseline threshold")
    if not capture_time_skew_aligned:
        errors.append("queue/consumption capture time skew exceeds baseline threshold")

    report_json_path = ROOT / str(report_baseline.get("report_json") or "artifacts/backend/scene_governance_history_report.json")
    report_md_path = ROOT / str(report_baseline.get("report_md") or "artifacts/backend/scene_governance_history_report.md")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "queue_policy_aligned": queue_policy_aligned,
            "consumption_policy_aligned": consumption_policy_aligned,
            "drop_policy_aligned": drop_policy_aligned,
            "capture_time_skew_aligned": capture_time_skew_aligned,
            "consumption_enabled": consumption_enabled,
            "queue_size": queue_size,
            "queue_growth": queue_growth,
            "queue_remaining_count": queue_remaining,
            "scene_count": scene_count,
            "scene_type_count": scene_type_count,
            "aggregate_base_search_rate": aggregate_base_search_rate,
            "aggregate_action_surface_rate": aggregate_action_surface_rate,
            "aggregate_base_search_rate_drop": aggregate_base_search_rate_drop,
            "aggregate_action_surface_rate_drop": aggregate_action_surface_rate_drop,
            "capture_time_skew_seconds": capture_time_skew_seconds,
            "max_capture_time_skew_seconds": max_capture_time_skew_seconds,
        },
        "policies": {
            "queue": {
                "max_queue_size": max_queue_size,
                "max_growth_per_run": max_growth_per_run,
            },
            "consumption": {
                "min_scene_count": min_scene_count,
                "min_scene_type_count": min_scene_type_count,
                "min_aggregate_base_search_rate": min_aggregate_base_search_rate,
                "min_aggregate_action_surface_rate": min_aggregate_action_surface_rate,
                "max_base_search_rate_drop_per_run": max_base_search_rate_drop_per_run,
                "max_action_surface_rate_drop_per_run": max_action_surface_rate_drop_per_run,
            },
        },
        "sources": {
            "queue_state": queue_state_path.relative_to(ROOT).as_posix(),
            "consumption_state": consumption_state_path.relative_to(ROOT).as_posix(),
            "queue_baseline": QUEUE_BASELINE_PATH.relative_to(ROOT).as_posix(),
            "consumption_baseline": CONSUMPTION_BASELINE_PATH.relative_to(ROOT).as_posix(),
            "report_baseline": REPORT_BASELINE_PATH.relative_to(ROOT).as_posix(),
        },
        "errors": errors,
        "report": {
            "json": report_json_path.relative_to(ROOT).as_posix(),
            "md": report_md_path.relative_to(ROOT).as_posix(),
        },
    }

    markdown_lines = [
        "# Scene Governance History Report",
        "",
        f"- queue_policy_aligned: `{queue_policy_aligned}`",
        f"- consumption_policy_aligned: `{consumption_policy_aligned}`",
        f"- drop_policy_aligned: `{drop_policy_aligned}`",
        f"- capture_time_skew_aligned: `{capture_time_skew_aligned}`",
        f"- consumption_enabled: `{consumption_enabled}`",
        f"- queue_size: `{queue_size}` (max `{max_queue_size}`)",
        f"- queue_growth: `{queue_growth}` (max `{max_growth_per_run}`)",
        f"- scene_count: `{scene_count}` (min `{min_scene_count}` when enabled)",
        f"- scene_type_count: `{scene_type_count}` (min `{min_scene_type_count}` when enabled)",
        f"- aggregate_base_search_rate: `{aggregate_base_search_rate:.4f}`",
        f"- aggregate_action_surface_rate: `{aggregate_action_surface_rate:.4f}`",
        f"- aggregate_base_search_rate_drop: `{aggregate_base_search_rate_drop:.4f}` (max `{max_base_search_rate_drop_per_run:.4f}`)",
        f"- aggregate_action_surface_rate_drop: `{aggregate_action_surface_rate_drop:.4f}` (max `{max_action_surface_rate_drop_per_run:.4f}`)",
        f"- capture_time_skew_seconds: `{capture_time_skew_seconds}` (max `{max_capture_time_skew_seconds}`)",
    ]
    if errors:
        markdown_lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(markdown_lines) + "\n")

    if errors:
        print("[scene_governance_history_report_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_governance_history_report_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

