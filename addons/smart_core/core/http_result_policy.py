# -*- coding: utf-8 -*-
from typing import Any, Dict

from .intent_operation_policy import is_write_intent


def result_is_success(result: Dict[str, Any] | None) -> bool:
    if not isinstance(result, dict):
        return True
    ok = result.get("ok", True)
    if isinstance(ok, bool):
        return ok
    if isinstance(ok, (int, float)):
        return bool(ok)
    if isinstance(ok, str):
        return ok.strip().lower() not in {"0", "false", "no", "off"}
    return bool(ok)


def normalize_result_ok(result: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if isinstance(result, dict) and "ok" in result:
        result["ok"] = result_is_success(result)
    return result


def result_transaction_action(
    intent_name: str,
    params: Dict[str, Any] | None,
    result: Dict[str, Any] | None,
    status: int,
) -> str:
    if not is_write_intent(intent_name, params):
        return "none"
    if int(status or 0) < 400 and result_is_success(result):
        return "commit"
    return "rollback"


def result_http_status(result: Dict[str, Any] | None, default: int = 200) -> int:
    payload = result if isinstance(result, dict) else {}
    raw = payload.get("code", default)
    try:
        status = int(raw)
    except Exception:
        return 500 if not result_is_success(payload) else default
    if status < 100 or status > 599:
        return 500 if not result_is_success(payload) else default
    return status
