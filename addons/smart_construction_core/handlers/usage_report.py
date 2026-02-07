# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler


class UsageReportHandler(BaseIntentHandler):
    INTENT_TYPE = "usage.report"
    DESCRIPTION = "Usage analytics report for scene/capability"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        data = build_usage_report_data(self.env, params=params)
        return {"ok": True, "data": data, "meta": {"intent": self.INTENT_TYPE}}

def build_usage_report_data(env, params=None):
    params = params or {}
    top_n = _normalize_int(params.get("top"), default=10, min_value=1, max_value=30)
    days = _normalize_int(params.get("days"), default=7, min_value=1, max_value=30)
    scene_prefix = str(params.get("scene_key_prefix") or "").strip().lower()
    capability_prefix = str(params.get("capability_key_prefix") or "").strip().lower()
    day_window = _build_day_window(
        days=days,
        day_from=params.get("day_from"),
        day_to=params.get("day_to"),
    )
    day_set = set(day_window)

    user = env.user
    company = user.company_id if user else None
    Usage = env.get("sc.usage.counter")
    if Usage is None or not company:
        return _empty_report(days=days, day_window=day_window)

    counters = Usage.sudo().search([("company_id", "=", company.id)])
    scene_total = 0
    capability_total = 0
    scene_counts = defaultdict(int)
    capability_counts = defaultdict(int)
    scene_daily = defaultdict(int)
    capability_daily = defaultdict(int)
    latest_updated_at = ""

    for rec in counters:
        key = str(rec.key or "")
        value = int(rec.value or 0)
        if key == "usage.scene_open.total":
            scene_total = value
        elif key.startswith("usage.scene_open.daily."):
            day = key[len("usage.scene_open.daily."):]
            if _is_day(day) and day in day_set:
                scene_daily[day] += value
        elif key.startswith("usage.scene_open."):
            scene_key = key[len("usage.scene_open."):]
            if scene_key and scene_key != "total" and _matches_prefix(scene_key, scene_prefix):
                scene_counts[scene_key] += value
        elif key == "usage.capability_open.total":
            capability_total = value
        elif key.startswith("usage.capability_open.daily."):
            day = key[len("usage.capability_open.daily."):]
            if _is_day(day) and day in day_set:
                capability_daily[day] += value
        elif key.startswith("usage.capability_open."):
            cap_key = key[len("usage.capability_open."):]
            if cap_key and cap_key != "total" and _matches_prefix(cap_key, capability_prefix):
                capability_counts[cap_key] += value
        if rec.updated_at and str(rec.updated_at) > latest_updated_at:
            latest_updated_at = str(rec.updated_at)

    return {
        "generated_at": latest_updated_at,
        "totals": {
            "scene_open_total": scene_total,
            "capability_open_total": capability_total,
        },
        "daily": {
            "scene_open": _daily_series(scene_daily, day_window=day_window),
            "capability_open": _daily_series(capability_daily, day_window=day_window),
        },
        "scene_top": _top_items(scene_counts, top_n),
        "capability_top": _top_items(capability_counts, top_n),
        "filters": {
            "top": top_n,
            "days": days,
            "day_from": day_window[0] if day_window else "",
            "day_to": day_window[-1] if day_window else "",
            "scene_key_prefix": scene_prefix,
            "capability_key_prefix": capability_prefix,
        },
    }


def _empty_report(days=7, day_window=None):
    day_window = day_window or _build_day_window(days=days)
    return {
        "generated_at": "",
        "totals": {"scene_open_total": 0, "capability_open_total": 0},
        "daily": {
            "scene_open": _daily_series({}, day_window=day_window),
            "capability_open": _daily_series({}, day_window=day_window),
        },
        "scene_top": [],
        "capability_top": [],
        "filters": {
            "top": 10,
            "days": len(day_window),
            "day_from": day_window[0] if day_window else "",
            "day_to": day_window[-1] if day_window else "",
            "scene_key_prefix": "",
            "capability_key_prefix": "",
        },
    }


def _top_items(counter_map, top_n):
    items = [{"key": key, "count": int(value)} for key, value in counter_map.items()]
    items.sort(key=lambda item: item["count"], reverse=True)
    return items[:top_n]


def _is_day(value):
    try:
        datetime.strptime(str(value), "%Y-%m-%d")
        return True
    except Exception:
        return False


def _daily_series(counter_map, day_window):
    rows = []
    for day in day_window:
        rows.append({"day": day, "count": int(counter_map.get(day, 0))})
    return rows


def _normalize_int(value, default, min_value, max_value):
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(min_value, min(parsed, max_value))


def _matches_prefix(value, prefix):
    if not prefix:
        return True
    return str(value or "").lower().startswith(prefix)


def _build_day_window(*, days=7, day_from=None, day_to=None):
    parsed_from = _parse_day(day_from)
    parsed_to = _parse_day(day_to)
    if parsed_from and parsed_to and parsed_from <= parsed_to:
        delta = (parsed_to - parsed_from).days + 1
        if delta <= 30:
            return [(parsed_from + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta)]
    today = datetime.utcnow().date()
    safe_days = _normalize_int(days, default=7, min_value=1, max_value=30)
    return [(today - timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(safe_days - 1, -1, -1)]


def _parse_day(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return None
