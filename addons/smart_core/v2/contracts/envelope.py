from __future__ import annotations

from time import perf_counter
from typing import Any, Dict, Optional


def _project_response_meta(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    projected: Dict[str, Any] = {}
    for key in ("contract_surface", "contract_mode", "render_mode", "source_mode"):
        value = data.get(key)
        if value is not None:
            projected[key] = value
    return projected


def make_envelope(
    *,
    ok: bool,
    intent: str,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
    effect: Optional[Dict[str, Any]] = None,
    trace_id: str = "",
    contract_version: str = "v2",
    schema_version: str = "v1",
    started_at: Optional[float] = None,
) -> Dict[str, Any]:
    latency_ms = 0
    if started_at is not None:
        latency_ms = int((perf_counter() - started_at) * 1000)
    meta = {
        "intent": str(intent or ""),
        "trace_id": str(trace_id or ""),
        "contract_version": str(contract_version or "v2"),
        "schema_version": str(schema_version or "v1"),
        "latency_ms": latency_ms,
    }
    meta.update(_project_response_meta(data))
    return {
        "ok": bool(ok),
        "data": data if isinstance(data, dict) or data is None else {"value": data},
        "error": error if isinstance(error, dict) or error is None else {"message": str(error)},
        "meta": meta,
        "effect": effect if isinstance(effect, dict) or effect is None else {"value": effect},
    }
