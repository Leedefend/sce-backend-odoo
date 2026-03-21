# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

CRITICAL_SCENES = {
    "workspace.home",
    "workspace.list",
}


def scene_severity(scene_key: str | None) -> str:
    if scene_key and scene_key in CRITICAL_SCENES:
        return "critical"
    return "non_critical"


def is_critical_drift_warn(entry: dict) -> bool:
    if not isinstance(entry, dict):
        return False
    if str(entry.get("severity") or "").strip().lower() != "warn":
        return False
    scene_key = entry.get("scene_key")
    return scene_key in CRITICAL_SCENES


def append_resolve_error(resolve_errors, *, scene_key, kind, code, ref=None, message=None, severity=None, field=None):
    entry = {
        "scene_key": scene_key or "",
        "kind": kind,
        "code": code,
        "severity": severity or scene_severity(scene_key),
        "message": message or "",
    }
    if ref:
        entry["ref"] = ref
    if field:
        entry["field"] = field
    resolve_errors.append(entry)


class SceneDriftEngine:
    def evaluate(self, scenes, diagnostics):
        if not isinstance(diagnostics, dict):
            return diagnostics
        diagnostics["drift"] = diagnostics.get("drift") if isinstance(diagnostics.get("drift"), list) else []
        diagnostics["resolve_errors"] = (
            diagnostics.get("resolve_errors") if isinstance(diagnostics.get("resolve_errors"), list) else []
        )
        return diagnostics


def build_scene_health_payload(data: dict, trace_id: str = "", company_id: int | None = None) -> dict:
    data = data or {}
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    diag = data.get("scene_diagnostics") if isinstance(data.get("scene_diagnostics"), dict) else {}
    resolve_errors = diag.get("resolve_errors") if isinstance(diag.get("resolve_errors"), list) else []
    drift = diag.get("drift") if isinstance(diag.get("drift"), list) else []
    normalize_warnings = diag.get("normalize_warnings") if isinstance(diag.get("normalize_warnings"), list) else []

    critical_resolve_errors = [
        entry for entry in resolve_errors
        if isinstance(entry, dict) and str(entry.get("severity") or "").strip().lower() == "critical"
    ]
    critical_drift_warn = [entry for entry in drift if is_critical_drift_warn(entry)]

    debt = []
    for entry in resolve_errors:
        if not isinstance(entry, dict):
            continue
        severity = str(entry.get("severity") or "").strip().lower()
        if severity != "critical":
            debt.append({"type": "resolve_error", **entry})
    for entry in drift:
        if not isinstance(entry, dict):
            continue
        if not is_critical_drift_warn(entry):
            debt.append({"type": "drift", **entry})
    for entry in normalize_warnings:
        if isinstance(entry, dict):
            debt.append({"type": "normalize_warning", **entry})

    resolved_company_id = company_id
    if resolved_company_id is None:
        raw_company_id = user.get("company_id") if isinstance(user, dict) else None
        try:
            resolved_company_id = int(raw_company_id) if raw_company_id else None
        except Exception:
            resolved_company_id = None

    return {
        "company_id": resolved_company_id,
        "scene_channel": data.get("scene_channel"),
        "rollback_active": bool(diag.get("rollback_active")),
        "scene_version": data.get("scene_version"),
        "schema_version": data.get("schema_version"),
        "contract_ref": data.get("scene_contract_ref"),
        "summary": {
            "critical_resolve_errors_count": len(critical_resolve_errors),
            "critical_drift_warn_count": len(critical_drift_warn),
            "non_critical_debt_count": len(debt),
        },
        "details": {
            "resolve_errors": resolve_errors,
            "drift": drift,
            "debt": debt,
        },
        "auto_degrade": diag.get("auto_degrade") if isinstance(diag.get("auto_degrade"), dict) else {
            "triggered": False,
            "reason_codes": [],
            "action_taken": "none",
        },
        "last_updated_at": fields.Datetime.now(),
        "trace_id": trace_id or "",
    }
