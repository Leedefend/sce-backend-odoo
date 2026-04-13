from __future__ import annotations

from typing import Any, Dict

from ....handlers.base import BaseIntentHandlerV2, HandlerContextV2
from ..builders.catalog_builder import build_app_nav_contract
from ..services.catalog_service import AppCatalogServiceV2


class AppNavHandlerV2(BaseIntentHandlerV2):
    intent_name = "app.nav"

    def __init__(self) -> None:
        self._service = AppCatalogServiceV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        _ = context
        app_key = str((payload or {}).get("app_key") or "platform").strip()
        return self._service.build_app_nav(app_key)

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_app_nav_contract(result)
