# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_xmlid_map(env, model: str, ids: List[int]) -> Dict[int, str]:
    if not ids:
        return {}
    out: Dict[int, str] = {}
    rows = env["ir.model.data"].sudo().search_read(
        [("model", "=", model), ("res_id", "in", ids)],
        fields=["module", "name", "res_id"],
    )
    for row in rows:
        rid = int(row.get("res_id") or 0)
        if rid <= 0:
            continue
        module = _to_text(row.get("module"))
        name = _to_text(row.get("name"))
        if module and name:
            out[rid] = f"{module}.{name}"
    return out


def project_report_action_capabilities(env, user=None, *, limit: int = 600) -> List[Dict[str, Any]]:
    del user
    report_rows = env["ir.actions.report"].sudo().search_read(
        [("report_type", "!=", False)],
        fields=["id", "name", "model", "report_type", "report_name", "binding_type"],
        limit=limit,
        order="id asc",
    )
    if not isinstance(report_rows, list) or not report_rows:
        return []

    report_ids = [int(row.get("id") or 0) for row in report_rows if int(row.get("id") or 0) > 0]
    xmlid_map = _safe_xmlid_map(env, "ir.actions.report", report_ids)

    projected: List[Dict[str, Any]] = []
    for row in report_rows:
        report_id = int(row.get("id") or 0)
        if report_id <= 0:
            continue
        name = _to_text(row.get("name")) or f"report_action_{report_id}"
        model_name = _to_text(row.get("model"))
        xmlid = xmlid_map.get(report_id, "")
        cap_key = f"native.report_action.{xmlid or report_id}"

        projected.append(
            {
                "identity": {
                    "key": cap_key,
                    "name": name,
                    "domain": model_name or "native.odoo",
                    "type": "native_report_action",
                    "version": "v1",
                },
                "ownership": {
                    "owner_module": "smart_core",
                    "source_module": "smart_core.native.report",
                    "source_kind": "native_projection",
                },
                "ui": {
                    "label": name,
                    "hint": "Projected from ir.actions.report",
                    "group_key": "native_report_action",
                    "icon": "",
                    "sequence": report_id,
                    "tags": ["native", "report_action", "odoo"],
                },
                "binding": {
                    "contract": {
                        "subject": "native_report_action",
                        "contract_type": "report_action",
                        "contract_version": "v1",
                    },
                    "exposure": {
                        "report_id": report_id,
                        "report_xmlid": xmlid,
                        "report_type": _to_text(row.get("report_type")),
                        "report_name": _to_text(row.get("report_name")),
                        "binding_type": _to_text(row.get("binding_type")),
                        "model": model_name,
                    },
                    "intent": {
                        "primary_intent": "execute_button",
                    },
                },
                "permission": {
                    "required_roles": [],
                    "required_groups": [],
                    "access_mode": "execute",
                    "data_scope": "user_env",
                },
                "release": {
                    "tier": "standard",
                    "slice": "native",
                    "exposure_mode": "default",
                    "approval_required": False,
                    "feature_flag": "",
                },
                "lifecycle": {
                    "status": "ga",
                    "deprecated": False,
                    "replacement_key": "",
                    "introduced_in": "",
                    "sunset_after": "",
                },
                "runtime": {
                    "supports_entry": False,
                    "supports_execute": True,
                    "supports_batch": False,
                    "safe_fallback": "",
                },
                "audit": {
                    "audit_enabled": True,
                    "policy_trace_enabled": True,
                    "owner_trace": "smart_core.native.report_adapter",
                },
            }
        )
    return projected

