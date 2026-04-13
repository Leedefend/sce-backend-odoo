from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


def _root_shape(value: Any) -> Tuple[str, ...]:
    if not isinstance(value, dict):
        return tuple()
    return tuple(sorted(str(k) for k in value.keys()))


def _error_code(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    err = value.get("error")
    if not isinstance(err, dict):
        return ""
    code = err.get("code")
    return str(code or "")


def _status_of(value: Any) -> str:
    if isinstance(value, dict):
        if "ok" in value:
            return "ok" if bool(value.get("ok")) else "error"
        if value.get("status") in ("success", "ok"):
            return "ok"
    return "unknown"


def _diff_summary(v1_result: Any, v2_result: Any) -> List[str]:
    diffs: List[str] = []
    if _root_shape(v1_result) != _root_shape(v2_result):
        diffs.append("root_shape_mismatch")
    if _status_of(v1_result) != _status_of(v2_result):
        diffs.append("status_mismatch")
    if _error_code(v1_result) != _error_code(v2_result):
        diffs.append("error_code_mismatch")

    v1_meta_intent = ""
    v2_meta_intent = ""
    if isinstance(v1_result, dict) and isinstance(v1_result.get("meta"), dict):
        v1_meta_intent = str(v1_result["meta"].get("intent") or "")
    if isinstance(v2_result, dict) and isinstance(v2_result.get("meta"), dict):
        v2_meta_intent = str(v2_result["meta"].get("intent") or "")
    if v1_meta_intent and v2_meta_intent and v1_meta_intent != v2_meta_intent:
        diffs.append("meta_intent_mismatch")

    return diffs


def run_shadow_compare(
    *,
    intent: str,
    route_mode: str,
    params: Dict[str, Any],
    context: Dict[str, Any],
    v1_result: Any,
    v2_runner: Callable[[str, Dict[str, Any], Dict[str, Any]], Any],
) -> Dict[str, Any]:
    trace_id = str((context or {}).get("trace_id") or "")
    v2_result: Any = None
    v2_status = "ok"
    v2_error = ""
    try:
        v2_result = v2_runner(intent, params or {}, context or {})
    except Exception as exc:  # pragma: no cover
        v2_status = "error"
        v2_error = str(exc)
        v2_result = {"ok": False, "error": {"code": "SHADOW_V2_EXEC_ERROR", "message": v2_error}}

    summary = _diff_summary(v1_result, v2_result)

    return {
        "intent": str(intent or ""),
        "route_mode": str(route_mode or "v2_shadow"),
        "v1_status": _status_of(v1_result),
        "v2_status": _status_of(v2_result) if v2_status == "ok" else "error",
        "same_shape": _root_shape(v1_result) == _root_shape(v2_result),
        "same_reason_code": _error_code(v1_result) == _error_code(v2_result),
        "diff_summary": summary,
        "trace_id": trace_id,
        "v2_error": v2_error,
    }
