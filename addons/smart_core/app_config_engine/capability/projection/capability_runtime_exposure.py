# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


NATIVE_PRIMARY_INTENT_BASELINE = {
    "native_menu_entry": "app.open",
    "native_window_action": "ui.contract",
    "native_model_access": "ui.contract",
    "native_server_action": "execute_button",
    "native_report_action": "ui.contract",
    "native_view_binding": "ui.contract",
}


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def resolve_primary_intent(row: Dict[str, Any]) -> str:
    if not isinstance(row, dict):
        return ""
    binding = row.get("binding") if isinstance(row.get("binding"), dict) else {}
    intent = binding.get("intent") if isinstance(binding.get("intent"), dict) else {}
    explicit = _to_text(intent.get("primary_intent"))
    if explicit:
        return explicit
    identity = row.get("identity") if isinstance(row.get("identity"), dict) else {}
    capability_type = _to_text(identity.get("type"))
    return _to_text(NATIVE_PRIMARY_INTENT_BASELINE.get(capability_type))


def resolve_runtime_target(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    binding = row.get("binding") if isinstance(row.get("binding"), dict) else {}
    exposure = binding.get("exposure") if isinstance(binding.get("exposure"), dict) else {}
    scene = binding.get("scene") if isinstance(binding.get("scene"), dict) else {}
    contract = binding.get("contract") if isinstance(binding.get("contract"), dict) else {}
    identity = row.get("identity") if isinstance(row.get("identity"), dict) else {}

    scene_key = _to_text(scene.get("entry_scene_key"))
    if scene_key:
        return {
            "mode": "scene",
            "scene_key": scene_key,
        }

    if _to_text(exposure.get("menu_xmlid")) or exposure.get("menu_id"):
        return {
            "mode": "menu",
            "menu_xmlid": _to_text(exposure.get("menu_xmlid")),
            "menu_id": int(exposure.get("menu_id") or 0),
            "action_ref": _to_text(exposure.get("action_ref")),
        }

    if _to_text(exposure.get("action_xmlid")) or exposure.get("action_id"):
        return {
            "mode": "action",
            "action_xmlid": _to_text(exposure.get("action_xmlid")),
            "action_id": int(exposure.get("action_id") or 0),
            "action_type": _to_text(exposure.get("action_type")),
        }

    if _to_text(exposure.get("model_name")):
        return {
            "mode": "model",
            "model_name": _to_text(exposure.get("model_name")),
            "access": _to_text(exposure.get("access")),
        }

    if _to_text(exposure.get("report_xmlid")) or exposure.get("report_id"):
        return {
            "mode": "report",
            "report_xmlid": _to_text(exposure.get("report_xmlid")),
            "report_id": int(exposure.get("report_id") or 0),
        }

    if _to_text(exposure.get("server_action_xmlid")) or exposure.get("server_action_id"):
        return {
            "mode": "server_action",
            "server_action_xmlid": _to_text(exposure.get("server_action_xmlid")),
            "server_action_id": int(exposure.get("server_action_id") or 0),
        }

    if _to_text(exposure.get("view_xmlid")) or exposure.get("view_id"):
        return {
            "mode": "view_binding",
            "view_xmlid": _to_text(exposure.get("view_xmlid")),
            "view_id": int(exposure.get("view_id") or 0),
            "contract_subject": _to_text(contract.get("subject")),
        }

    capability_type = _to_text(identity.get("type"))
    return {"mode": capability_type or "unknown"}

