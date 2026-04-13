from __future__ import annotations

from typing import Any, Dict

from ...builders.meta_builder import build_registry_catalog_contract
from ...services.meta_service import MetaService
from ..base import BaseIntentHandlerV2, HandlerContextV2


class MetaRegistryCatalogHandlerV2(BaseIntentHandlerV2):
    intent_name = "meta.registry.catalog"

    def __init__(self) -> None:
        self._service = MetaService()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        _ = payload
        entries = getattr(context, "registry_entries", {}) or {}
        return self._service.list_registry_catalog(entries)

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_registry_catalog_contract(result)
