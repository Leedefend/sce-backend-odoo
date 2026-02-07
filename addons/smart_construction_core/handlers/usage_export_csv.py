# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler

from .usage_report import build_usage_report_data


class UsageExportCsvHandler(BaseIntentHandler):
    INTENT_TYPE = "usage.export.csv"
    DESCRIPTION = "Export usage analytics csv from backend"
    VERSION = "1.0.0"
    ETAG_ENABLED = False

    def handle(self, payload=None, ctx=None):
        params = payload or self.params or {}
        export_filtered_only = _as_bool(params.get("export_filtered_only"), default=True)
        hidden_reason = str(params.get("hidden_reason") or "ALL").strip()
        report = build_usage_report_data(self.env, params=params)
        visibility = _build_visibility_payload(self.env)
        csv_text = build_usage_csv(
            report=report,
            visibility=visibility,
            export_filtered_only=export_filtered_only,
            hidden_reason=hidden_reason,
        )
        day_from = report.get("filters", {}).get("day_from") or ""
        day_to = report.get("filters", {}).get("day_to") or ""
        filename = f"usage-analytics-{day_from or 'na'}-{day_to or 'na'}.csv"
        return {
            "ok": True,
            "data": {"filename": filename, "content": csv_text},
            "meta": {"intent": self.INTENT_TYPE},
        }


def build_usage_csv(*, report, visibility, export_filtered_only=True, hidden_reason="ALL"):
    hidden_reason = str(hidden_reason or "ALL")
    lines = ["section,key,count,extra"]
    lines.append(f"meta,export_filtered_only,{1 if export_filtered_only else 0},")
    filters = report.get("filters") or {}
    lines.append(f"meta,day_from,{_quote(filters.get('day_from') or '')},")
    lines.append(f"meta,day_to,{_quote(filters.get('day_to') or '')},")

    totals = report.get("totals") or {}
    lines.append(f"total,scene_open_total,{int(totals.get('scene_open_total') or 0)},")
    lines.append(f"total,capability_open_total,{int(totals.get('capability_open_total') or 0)},")

    for item in report.get("scene_top") or []:
        lines.append(f"scene_top,{_quote(item.get('key') or '')},{int(item.get('count') or 0)},")
    for item in report.get("capability_top") or []:
        lines.append(f"capability_top,{_quote(item.get('key') or '')},{int(item.get('count') or 0)},")
    for item in (report.get("daily") or {}).get("scene_open") or []:
        lines.append(f"scene_daily,{item.get('day') or ''},{int(item.get('count') or 0)},")
    for item in (report.get("daily") or {}).get("capability_open") or []:
        lines.append(f"capability_daily,{item.get('day') or ''},{int(item.get('count') or 0)},")

    summary = visibility.get("summary") or {}
    lines.append(f"capability_visibility,total,{int(summary.get('total') or 0)},")
    lines.append(f"capability_visibility,visible,{int(summary.get('visible') or 0)},")
    lines.append(f"capability_visibility,hidden,{int(summary.get('hidden') or 0)},")
    for item in visibility.get("reason_counts") or []:
        lines.append(f"reason_count,{_quote(item.get('reason_code') or '')},{int(item.get('count') or 0)},")

    hidden_rows = visibility.get("hidden_samples") or []
    if export_filtered_only and hidden_reason not in {"", "ALL"}:
        hidden_rows = [row for row in hidden_rows if str(row.get("reason_code") or "") == hidden_reason]
    for item in hidden_rows:
        reason = item.get("reason_code") or item.get("reason") or "-"
        lines.append(f"hidden_sample,{_quote(item.get('key') or '')},0,{_quote(reason)}")
    return "\n".join(lines)


def _build_visibility_payload(env):
    user = env.user
    Cap = env.get("sc.capability")
    if Cap is None:
        return {"summary": {}, "reason_counts": [], "hidden_samples": []}
    caps = Cap.sudo().search([("active", "=", True)], order="sequence, id")
    summary = {"total": len(caps), "visible": 0, "hidden": 0, "ready": 0, "preview": 0, "locked": 0}
    reason_counts = {}
    hidden_samples = []
    for cap in caps:
        access = cap._access_context(user)
        reason_code = str(access.get("reason_code") or "")
        state = str(access.get("state") or "")
        if access.get("visible"):
            summary["visible"] += 1
            if state == "READY":
                summary["ready"] += 1
            elif state == "PREVIEW":
                summary["preview"] += 1
            elif state == "LOCKED":
                summary["locked"] += 1
        else:
            summary["hidden"] += 1
            if len(hidden_samples) < 30:
                hidden_samples.append(
                    {
                        "key": cap.key,
                        "name": cap.name,
                        "reason_code": reason_code or "HIDDEN",
                        "reason": access.get("reason") or "",
                    }
                )
        if reason_code:
            reason_counts[reason_code] = int(reason_counts.get(reason_code, 0)) + 1
    reason_rows = [{"reason_code": code, "count": count} for code, count in reason_counts.items()]
    reason_rows.sort(key=lambda row: row["count"], reverse=True)
    return {"summary": summary, "reason_counts": reason_rows, "hidden_samples": hidden_samples}


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _quote(value):
    text = str(value or "")
    if not any(ch in text for ch in [",", "\"", "\n"]):
        return text
    return '"' + text.replace('"', '""') + '"'
