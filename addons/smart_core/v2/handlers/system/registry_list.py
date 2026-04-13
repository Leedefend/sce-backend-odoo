from __future__ import annotations

from typing import Any, Dict

from ...builders.system_builder import build_registry_list_contract
from ...services.system_service import SystemService
from ..base import BaseIntentHandlerV2, HandlerContextV2


class SystemRegistryListHandlerV2(BaseIntentHandlerV2):
    intent_name = "system.registry.list"

    def __init__(self) -> None:
        self._service = SystemService()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        _ = payload
        return self._service.list_registered_intents(context.registry_snapshot)

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_registry_list_contract(result)
