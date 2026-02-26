#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SURFACE_JSON = ROOT / "artifacts" / "backend" / "runtime_surface_dashboard_report.json"
SCENE_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
RELEASE_CAP_JSON = ROOT / "artifacts" / "backend" / "release_capability_report.json"
PLATFORM_SLA_JSON = ROOT / "artifacts" / "backend" / "platform_sla_report.json"
HISTORY_JSONL = ROOT / "artifacts" / "backend" / "history" / "runtime_trend_samples.jsonl"

REPORT_JSON = ROOT / "artifacts" / "backend" / "runtime_trend_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "runtime_trend_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _day_range(end_day: datetime, days: int) -> list[str]:
    out = []
    for i in range(days - 1, -1, -1):
        out.append((end_day - timedelta(days=i)).date().isoformat())
    return out


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except Exception:
        return default


def _load_history(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _save_history(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(item, ensure_ascii=False) for item in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    now = datetime.now()
    window_days = max(1, _env_int("RUNTIME_TREND_DAYS", 7))
    history_days_limit = max(window_days, _env_int("RUNTIME_TREND_HISTORY_KEEP_DAYS", 30))
    write_history = os.getenv("RUNTIME_TREND_WRITE_HISTORY", "1").strip() != "0"
    days = _day_range(now, window_days)

    runtime_surface = _load_json(RUNTIME_SURFACE_JSON)
    scene_matrix = _load_json(SCENE_MATRIX_JSON)
    role_floor = _load_json(ROLE_FLOOR_JSON)
    release = _load_json(RELEASE_CAP_JSON)
    platform_sla = _load_json(PLATFORM_SLA_JSON)

    if not runtime_surface:
        errors.append("missing runtime_surface_dashboard_report.json")
    if not scene_matrix:
        errors.append("missing scene_capability_matrix_report.json")

    scene_count = int(((scene_matrix.get("summary") or {}).get("scene_count")) or 0)
    capability_avg = float(((runtime_surface.get("summary") or {}).get("runtime_capability_avg")) or 0.0)
    capability_max = int(((runtime_surface.get("summary") or {}).get("runtime_capability_max")) or 0)
    capability_min = int(((runtime_surface.get("summary") or {}).get("runtime_capability_min")) or 0)
    if scene_count <= 0:
        errors.append("invalid scene_count")

    latest_day = datetime.fromtimestamp(RUNTIME_SURFACE_JSON.stat().st_mtime).date().isoformat() if RUNTIME_SURFACE_JSON.exists() else days[-1]

    sample = {
        "day": latest_day,
        "scene_count": scene_count,
        "capability_avg": capability_avg,
        "capability_min": capability_min,
        "capability_max": capability_max,
    }
    history_rows = _load_history(HISTORY_JSONL)
    if write_history:
        history_rows.append(sample)
    history_map: dict[str, dict] = {}
    for row in history_rows:
        if not isinstance(row, dict):
            continue
        day = str(row.get("day") or "").strip()
        if day:
            history_map[day] = row
    keep_days = _day_range(now, history_days_limit)
    keep_day_set = set(keep_days)
    history_rows = [history_map[d] for d in keep_days if d in history_map]
    if write_history:
        _save_history(HISTORY_JSONL, history_rows)

    scene_series = []
    capability_series = []
    for day in days:
        row = history_map.get(day) if day in history_map else None
        scene_series.append({"day": day, "value": int(row.get("scene_count")) if isinstance(row, dict) and row.get("scene_count") is not None else None})
        capability_series.append(
            {
                "day": day,
                "avg": float(row.get("capability_avg")) if isinstance(row, dict) and row.get("capability_avg") is not None else None,
                "min": int(row.get("capability_min")) if isinstance(row, dict) and row.get("capability_min") is not None else None,
                "max": int(row.get("capability_max")) if isinstance(row, dict) and row.get("capability_max") is not None else None,
            }
        )

    journey_rows = release.get("role_journeys") if isinstance(release.get("role_journeys"), list) else []
    intent_counter: dict[str, int] = {}
    role_intent_counter: dict[tuple[str, str], int] = {}
    for role_row in journey_rows:
        role = str(role_row.get("role") or "").strip()
        chain = role_row.get("intent_trace_chain") if isinstance(role_row.get("intent_trace_chain"), list) else []
        for step in chain:
            if not isinstance(step, dict):
                continue
            intent = str(step.get("intent") or "").strip()
            if intent:
                intent_counter[intent] = intent_counter.get(intent, 0) + 1
                if role:
                    key = (role, intent)
                    role_intent_counter[key] = role_intent_counter.get(key, 0) + 1

    sla_rows = platform_sla.get("rows") if isinstance(platform_sla.get("rows"), list) else []
    for row in sla_rows:
        if not isinstance(row, dict):
            continue
        intent = str(row.get("intent") or "").strip()
        iterations = int(row.get("iterations") or 0)
        if intent and iterations > 0:
            intent_counter[intent] = intent_counter.get(intent, 0) + iterations

    intent_heatmap = [
        {"intent": key, "count": intent_counter[key], "source": "probe"}
        for key in sorted(intent_counter.keys(), key=lambda x: (-intent_counter[x], x))
    ]
    if not intent_heatmap:
        warnings.append("intent heatmap empty (no probe traces found)")

    role_rows = role_floor.get("roles") if isinstance(role_floor.get("roles"), list) else []
    role_distribution = []
    for row in role_rows:
        if not isinstance(row, dict):
            continue
        role_distribution.append(
            {
                "role": str(row.get("role") or "").strip(),
                "login": str(row.get("login") or "").strip(),
                "capability_count": int(row.get("capability_count") or 0),
                "journey_ok": all(
                    isinstance(step, dict) and bool(step.get("ok"))
                    for step in (row.get("journey") if isinstance(row.get("journey"), list) else [])
                ),
            }
        )
    role_distribution = sorted(role_distribution, key=lambda x: (-x["capability_count"], x["role"]))
    if not role_distribution:
        warnings.append("role behavior distribution empty")

    role_intent_heatmap = [
        {"role": role, "intent": intent, "count": count}
        for (role, intent), count in sorted(role_intent_counter.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
    ]

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "window_days": window_days,
            "scene_series_points": len(scene_series),
            "capability_series_points": len(capability_series),
            "intent_heatmap_count": len(intent_heatmap),
            "role_distribution_count": len(role_distribution),
            "role_intent_heatmap_count": len(role_intent_heatmap),
            "history_day_count": len(history_rows),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "scene_count_timeseries_7d": scene_series,
        "capability_usage_timeseries_7d": capability_series,
        "intent_call_heatmap": intent_heatmap,
        "role_behavior_distribution": role_distribution,
        "role_intent_heatmap": role_intent_heatmap,
        "notes": [
            "This trend report is evidence-driven from latest backend audit artifacts.",
            "Missing-day values are represented as null when no persisted sample exists for that day.",
            "History samples are persisted in artifacts/backend/history/runtime_trend_samples.jsonl.",
        ],
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Runtime Trend Report",
        "",
        f"- window_days: {window_days}",
        f"- scene_series_points: {len(scene_series)}",
        f"- capability_series_points: {len(capability_series)}",
        f"- intent_heatmap_count: {len(intent_heatmap)}",
        f"- role_distribution_count: {len(role_distribution)}",
        f"- role_intent_heatmap_count: {len(role_intent_heatmap)}",
        f"- history_day_count: {len(history_rows)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Scene Count",
        "",
    ]
    for row in scene_series:
        lines.append(f"- {row['day']}: {row['value'] if row['value'] is not None else 'null'}")
    lines.extend(["", "## Capability Usage", ""])
    for row in capability_series:
        if row["avg"] is None:
            lines.append(f"- {row['day']}: null")
        else:
            lines.append(f"- {row['day']}: avg={row['avg']}, min={row['min']}, max={row['max']}")
    lines.extend(["", "## Intent Heatmap", ""])
    if intent_heatmap:
        for row in intent_heatmap[:20]:
            lines.append(f"- {row['intent']}: {row['count']} ({row['source']})")
    else:
        lines.append("- none")
    lines.extend(["", "## Role Intent Heatmap", ""])
    if role_intent_heatmap:
        for row in role_intent_heatmap[:30]:
            lines.append(f"- {row['role']} -> {row['intent']}: {row['count']}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[runtime_trend_report] FAIL")
        return 2
    print("[runtime_trend_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
