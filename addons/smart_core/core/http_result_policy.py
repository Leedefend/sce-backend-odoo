# -*- coding: utf-8 -*-
from typing import Any, Dict


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
