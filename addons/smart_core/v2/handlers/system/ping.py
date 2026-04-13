from __future__ import annotations

from typing import Any, Dict

from ...builders.system_builder import build_ping_contract
from ...services.system_service import SystemService
from ..base import BaseIntentHandlerV2, HandlerContextV2


class SystemPingHandlerV2(BaseIntentHandlerV2):
    intent_name = "system.ping"

    def __init__(self) -> None:
        self._service = SystemService()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        return self._service.ping(payload, {"trace_id": context.trace_id})

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_ping_contract(result)
