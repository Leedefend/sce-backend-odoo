# -*- coding: utf-8 -*-
"""Platform company-access helpers for industry modules."""

from __future__ import annotations

from typing import Any

from odoo import fields


def platform_entitlement_payload(env, user) -> dict[str, Any]:
    try:
        payload = env["sc.entitlement"].get_payload(user)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def platform_feature_flags_for_user(env, user) -> dict[str, Any]:
    flags = platform_entitlement_payload(env, user).get("flags")
    return flags if isinstance(flags, dict) else {}


def platform_limits_for_company(env, company) -> dict[str, Any]:
    if not company:
        return {}
    try:
        ent = env["sc.entitlement"].get_effective(company)
    except Exception:
        return {}
    limits = getattr(ent, "effective_limits_json", None)
    return limits if isinstance(limits, dict) else {}


def platform_limit_for_company(env, company, key: str, default: int = 0) -> int:
    limits = platform_limits_for_company(env, company)
    try:
        return int(limits.get(str(key or "").strip()) or default)
    except Exception:
        return int(default or 0)


def platform_usage_map(env, company) -> dict[str, Any]:
    if not company:
        return {}
    try:
        usage = env["sc.usage.counter"].get_usage_map(company)
    except Exception:
        return {}
    return usage if isinstance(usage, dict) else {}


def platform_usage_value(env, company, key: str, default: Any = None) -> Any:
    return platform_usage_map(env, company).get(str(key or "").strip(), default)


def start_platform_ops_job(env, vals: dict[str, Any]):
    payload = dict(vals or {})
    payload.setdefault("status", "running")
    payload.setdefault("started_at", fields.Datetime.now())
    return env["sc.ops.job"].sudo().create(payload)


def finish_platform_ops_job(job, *, result_json: Any = None, error_message: str = ""):
    vals = {"finished_at": fields.Datetime.now()}
    if error_message:
        vals.update({"status": "failed", "error_message": str(error_message)})
    else:
        vals.update({"status": "done", "result_json": result_json or []})
    job.write(vals)
    return job
