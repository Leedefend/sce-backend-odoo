from __future__ import annotations

from typing import Any, Dict

from ...builders.api_onchange_response_builder import ApiOnchangeResponseBuilderV2
from ...services.api_onchange_service import ApiOnchangeServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class ApiOnchangeHandlerV2(BaseIntentHandlerV2):
    intent_name = "api.onchange"

    def __init__(self) -> None:
        self._service = ApiOnchangeServiceV2()
        self._builder = ApiOnchangeResponseBuilderV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        result = self._service.execute_stub(
            payload=payload or {},
            context={
                "trace_id": str(context.trace_id or ""),
                "user_id": int(context.user_id or 0),
                "company_id": int(context.company_id or 0),
            },
        )
        return self._builder.build(result)
