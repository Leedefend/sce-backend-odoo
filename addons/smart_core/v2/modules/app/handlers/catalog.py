from __future__ import annotations

from typing import Any, Dict

from ....handlers.base import BaseIntentHandlerV2, HandlerContextV2
from ..builders.catalog_builder import build_app_catalog_contract
from ..services.catalog_service import AppCatalogServiceV2


class AppCatalogHandlerV2(BaseIntentHandlerV2):
    intent_name = "app.catalog"

    def __init__(self) -> None:
        self._service = AppCatalogServiceV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        _ = payload
        _ = context
        return self._service.list_apps()

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_app_catalog_contract(result)
