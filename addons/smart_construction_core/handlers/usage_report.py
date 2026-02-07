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
    role_code = str(params.get("role_code") or "").strip().lower()
    user_id = _normalize_int(params.get("user_id"), default=0, min_value=0, max_value=10**9)
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
    role_scene_totals = defaultdict(int)
    role_capability_totals = defaultdict(int)
    user_scene_totals = defaultdict(int)
    user_capability_totals = defaultdict(int)
    scoped_scene_counts = defaultdict(int)
    scoped_capability_counts = defaultdict(int)
    scoped_scene_daily = defaultdict(int)
    scoped_capability_daily = defaultdict(int)
    latest_updated_at = ""

    for rec in counters:
        key = str(rec.key or "")
        value = int(rec.value or 0)
        if key == "usage.scene_open.total":
            scene_total = value
        elif key.startswith("usage.scene_open.role."):
            role_rest = key[len("usage.scene_open.role."):]
            role, role_scope = _split_first(role_rest)
            if not role:
                continue
            if role_scope == "total":
                role_scene_totals[role] += value
            elif role_scope.startswith("daily.") and _is_day(role_scope[len("daily."):]):
                day = role_scope[len("daily."):]
                if day in day_set and _scope_match(role, role_code):
                    scoped_scene_daily[day] += value
            elif role_scope:
                if _scope_match(role, role_code) and _matches_prefix(role_scope, scene_prefix):
                    scoped_scene_counts[role_scope] += value
        elif key.startswith("usage.scene_open.user."):
            user_rest = key[len("usage.scene_open.user."):]
            uid_token, user_scope = _split_first(user_rest)
            uid_value = _as_int(uid_token)
            if uid_value <= 0:
                continue
            if user_scope == "total":
                user_scene_totals[uid_value] += value
            elif user_scope.startswith("daily.") and _is_day(user_scope[len("daily."):]):
                day = user_scope[len("daily."):]
                if day in day_set and _scope_match(str(uid_value), str(user_id) if user_id else ""):
                    scoped_scene_daily[day] += value
            elif user_scope:
                if _scope_match(str(uid_value), str(user_id) if user_id else "") and _matches_prefix(user_scope, scene_prefix):
                    scoped_scene_counts[user_scope] += value
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
        elif key.startswith("usage.capability_open.role."):
            role_rest = key[len("usage.capability_open.role."):]
            role, role_scope = _split_first(role_rest)
            if not role:
                continue
            if role_scope == "total":
                role_capability_totals[role] += value
            elif role_scope.startswith("daily.") and _is_day(role_scope[len("daily."):]):
                day = role_scope[len("daily."):]
                if day in day_set and _scope_match(role, role_code):
                    scoped_capability_daily[day] += value
            elif role_scope:
                if _scope_match(role, role_code) and _matches_prefix(role_scope, capability_prefix):
                    scoped_capability_counts[role_scope] += value
        elif key.startswith("usage.capability_open.user."):
            user_rest = key[len("usage.capability_open.user."):]
            uid_token, user_scope = _split_first(user_rest)
            uid_value = _as_int(uid_token)
            if uid_value <= 0:
                continue
            if user_scope == "total":
                user_capability_totals[uid_value] += value
            elif user_scope.startswith("daily.") and _is_day(user_scope[len("daily."):]):
                day = user_scope[len("daily."):]
                if day in day_set and _scope_match(str(uid_value), str(user_id) if user_id else ""):
                    scoped_capability_daily[day] += value
            elif user_scope:
                if _scope_match(str(uid_value), str(user_id) if user_id else "") and _matches_prefix(user_scope, capability_prefix):
                    scoped_capability_counts[user_scope] += value
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

    if role_code or user_id:
        scene_counts = scoped_scene_counts
        capability_counts = scoped_capability_counts
        scene_daily = scoped_scene_daily
        capability_daily = scoped_capability_daily

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
        "role_top": _role_top(role_scene_totals, role_capability_totals, top_n),
        "user_top": _user_top(user_scene_totals, user_capability_totals, top_n),
        "filters": {
            "top": top_n,
            "days": days,
            "day_from": day_window[0] if day_window else "",
            "day_to": day_window[-1] if day_window else "",
            "scene_key_prefix": scene_prefix,
            "capability_key_prefix": capability_prefix,
            "role_code": role_code,
            "user_id": user_id,
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
        "role_top": [],
        "user_top": [],
        "filters": {
            "top": 10,
            "days": len(day_window),
            "day_from": day_window[0] if day_window else "",
            "day_to": day_window[-1] if day_window else "",
            "scene_key_prefix": "",
            "capability_key_prefix": "",
            "role_code": "",
            "user_id": 0,
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


def _split_first(value):
    text = str(value or "")
    idx = text.find(".")
    if idx < 0:
        return text, ""
    return text[:idx], text[idx + 1:]


def _as_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def _scope_match(current, expected):
    expected = str(expected or "").strip().lower()
    if not expected:
        return True
    return str(current or "").strip().lower() == expected


def _role_top(scene_totals, capability_totals, top_n):
    role_codes = set(scene_totals.keys()) | set(capability_totals.keys())
    rows = []
    for role_code in role_codes:
        scene_total = int(scene_totals.get(role_code, 0))
        capability_total = int(capability_totals.get(role_code, 0))
        rows.append(
            {
                "role_code": role_code,
                "scene_open_total": scene_total,
                "capability_open_total": capability_total,
                "combined_total": scene_total + capability_total,
            }
        )
    rows.sort(key=lambda row: row["combined_total"], reverse=True)
    return rows[:top_n]


def _user_top(scene_totals, capability_totals, top_n):
    user_ids = set(scene_totals.keys()) | set(capability_totals.keys())
    rows = []
    for uid in user_ids:
        scene_total = int(scene_totals.get(uid, 0))
        capability_total = int(capability_totals.get(uid, 0))
        rows.append(
            {
                "user_id": int(uid),
                "scene_open_total": scene_total,
                "capability_open_total": capability_total,
                "combined_total": scene_total + capability_total,
            }
        )
    rows.sort(key=lambda row: row["combined_total"], reverse=True)
    return rows[:top_n]
