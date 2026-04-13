from __future__ import annotations

from typing import Any, Dict

from ...builders.system_builder import build_system_init_contract
from ...services.system_service import SystemService
from ..base import BaseIntentHandlerV2, HandlerContextV2


class SystemInitHandlerV2(BaseIntentHandlerV2):
    intent_name = "system.init"

    def __init__(self) -> None:
        self._service = SystemService()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        ctx = {
            "trace_id": context.trace_id,
            "user_id": context.user_id,
            "company_id": context.company_id,
            "registry_snapshot": context.registry_snapshot,
        }
        return self._service.build_system_init(payload or {}, ctx)

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_system_init_contract(result)

