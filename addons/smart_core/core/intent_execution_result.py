# -*- coding: utf-8 -*-
# smart_core/core/intent_execution_result.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

SOURCE_KIND = "intent_execution_result_envelope"
SOURCE_AUTHORITIES = ("handler_result",)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "runtime_carrier": "intent_execution_result",
    }


@dataclass
class IntentExecutionResult:
    SOURCE_KIND = SOURCE_KIND
    SOURCE_AUTHORITIES = SOURCE_AUTHORITIES
    NO_BUSINESS_FACT_AUTHORITY = NO_BUSINESS_FACT_AUTHORITY

    @classmethod
    def source_authority_contract(cls) -> Dict[str, Any]:
        return source_authority_contract()

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

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_legacy_dict().get(key, default)


def adapt_handler_result(result: Any) -> Any:
    if isinstance(result, IntentExecutionResult):
        return result.to_legacy_dict()
    return result
