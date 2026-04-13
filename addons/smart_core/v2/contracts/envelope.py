from __future__ import annotations

from time import perf_counter
from typing import Any, Dict, Optional


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
    return {
        "ok": bool(ok),
        "data": data if isinstance(data, dict) or data is None else {"value": data},
        "error": error if isinstance(error, dict) or error is None else {"message": str(error)},
        "meta": {
            "intent": str(intent or ""),
            "trace_id": str(trace_id or ""),
            "contract_version": str(contract_version or "v2"),
            "schema_version": str(schema_version or "v1"),
            "latency_ms": latency_ms,
        },
        "effect": effect if isinstance(effect, dict) or effect is None else {"value": effect},
    }
