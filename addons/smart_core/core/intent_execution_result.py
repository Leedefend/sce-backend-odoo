# -*- coding: utf-8 -*-
# smart_core/core/intent_execution_result.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class IntentExecutionResult:
    ok: bool = True
    data: Any = field(default_factory=dict)
    error: Dict[str, Any] | None = None
    meta: Dict[str, Any] = field(default_factory=dict)
    code: int | None = None
    status: str | None = None

    def to_legacy_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "ok": bool(self.ok),
            "data": self.data,
            "meta": dict(self.meta or {}),
        }
        if self.error is not None:
            payload["error"] = dict(self.error)
        if self.code is not None:
            payload["code"] = int(self.code)
        if self.status is not None:
            payload["status"] = str(self.status)
        return payload


def adapt_handler_result(result: Any) -> Any:
    if isinstance(result, IntentExecutionResult):
        return result.to_legacy_dict()
    return result
