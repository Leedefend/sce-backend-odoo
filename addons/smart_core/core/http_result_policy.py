# -*- coding: utf-8 -*-
from typing import Any, Dict


def result_http_status(result: Dict[str, Any] | None, default: int = 200) -> int:
    payload = result if isinstance(result, dict) else {}
    raw = payload.get("code", default)
    try:
        status = int(raw)
    except Exception:
        return 500 if payload.get("ok") is False else default
    if status < 100 or status > 599:
        return 500 if payload.get("ok") is False else default
    return status
