# smart_core/controllers/intent_permission_details.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict

from ..utils.reason_codes import REASON_PERMISSION_DENIED


def build_permission_error_details(intent_name: str, params: Dict[str, Any], message: str) -> Dict[str, Any]:
    intent = str(intent_name or "").strip().lower()
    details: Dict[str, Any] = {
        "intent": str(intent_name or "").strip(),
        "reason_code": REASON_PERMISSION_DENIED,
    }
    if message:
        details["cause"] = str(message)

    model = str((params or {}).get("model") or "").strip()
    op = str((params or {}).get("op") or "").strip().lower()

    if not op and intent.startswith("api.data."):
        suffix = intent.split(".", 2)[-1].strip().lower()
        if suffix:
            op = suffix

    if intent == "api.data.batch":
        batch_action = str((params or {}).get("action") or "").strip().lower()
        if batch_action:
            op = f"batch.{batch_action}"

    if intent == "api.data" or intent.startswith("api.data."):
        if model:
            details["model"] = model
        if op:
            details["op"] = op

    return details
