from __future__ import annotations

from typing import Any, Dict

from ...builders.meta_builder import build_permission_check_contract
from ...services.meta_service import MetaService
from ..base import BaseIntentHandlerV2, HandlerContextV2


class PermissionCheckHandlerV2(BaseIntentHandlerV2):
    intent_name = "permission.check"

    def __init__(self) -> None:
        self._service = MetaService()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        model = str((payload or {}).get("model") or "").strip()
        operation = str((payload or {}).get("operation") or "read").strip().lower()
        return self._service.permission_check_stub(model_name=model, operation=operation, user_id=context.user_id)

    def build(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return build_permission_check_contract(result)
