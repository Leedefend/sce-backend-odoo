from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass
class HandlerContextV2:
    trace_id: str = ""
    user_id: int = 0
    company_id: int = 0
    registry_snapshot: tuple[str, ...] = ()
    registry_entries: Dict[str, Any] = None


class HandlerResultBuilder(Protocol):
    def __call__(self, result: Dict[str, Any]) -> Dict[str, Any]:
        ...


class BaseIntentHandlerV2:
    intent_name: str = ""

    def validate(self, payload: Dict[str, Any], context: HandlerContextV2) -> None:
        _ = payload
        _ = context

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        raise NotImplementedError

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def run(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        self.validate(payload, context)
        result = self.execute(payload, context)
        return self.build(result)
