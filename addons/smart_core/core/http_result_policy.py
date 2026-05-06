# -*- coding: utf-8 -*-
from typing import Any, Dict

from .intent_operation_policy import is_write_intent

SYMBOLIC_ERROR_STATUS = {
    "BAD_REQUEST": 400,
    "AUTH_REQUIRED": 401,
    "PERMISSION_DENIED": 403,
    "FEATURE_DISABLED": 403,
    "INTENT_NOT_FOUND": 404,
    "VALIDATION_ERROR": 422,
    "LIMIT_EXCEEDED": 429,
    "INTERNAL_ERROR": 500,
}


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


def _coerce_http_status(raw: Any, *, success: bool, default: int = 200) -> int:
    if isinstance(raw, str) and raw.strip().upper() in SYMBOLIC_ERROR_STATUS:
        return SYMBOLIC_ERROR_STATUS[raw.strip().upper()]
    try:
        status = int(raw)
    except Exception:
        return 500 if not success else default
    if status < 100 or status > 599:
        return 500 if not success else default
    return status


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


def normalize_error_result(
    result: Dict[str, Any],
    status: int,
    *,
    status_code_mapper,
    error_envelope_builder,
    trace_id: str | None,
    api_version: str,
    contract_version: str,
) -> Dict[str, Any]:
    if result_is_success(result):
        return result
    err = result.get("error") if isinstance(result.get("error"), dict) else {}
    if "code" not in err or "message" not in err:
        return error_envelope_builder(
            code=status_code_mapper(status),
            message=str(err or "请求失败"),
            trace_id=trace_id,
            api_version=api_version,
            contract_version=contract_version,
        )
    if isinstance(err.get("code"), int):
        next_result = dict(result)
        next_error = dict(err)
        next_error["code"] = status_code_mapper(status)
        next_result["error"] = next_error
        return next_result
    return result


def result_http_status(result: Dict[str, Any] | None, default: int = 200) -> int:
    payload = result if isinstance(result, dict) else {}
    success = result_is_success(payload)
    raw = payload.get("code", None)
    if raw is None:
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        error_code = error.get("code") if "code" in error else None
        if isinstance(error_code, int):
            raw = error_code
        elif isinstance(error_code, str) and error_code.strip().upper() in SYMBOLIC_ERROR_STATUS:
            raw = SYMBOLIC_ERROR_STATUS[error_code.strip().upper()]
        else:
            raw = 500 if not success else default
    return _coerce_http_status(raw, success=success, default=default)
