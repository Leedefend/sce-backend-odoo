from __future__ import annotations

from typing import Any, Dict

from ...builders.api_data_create_response_builder import ApiDataCreateResponseBuilderV2
from ...services.api_data_create_service import ApiDataCreateServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class ApiDataCreateHandlerV2(BaseIntentHandlerV2):
    intent_name = "api.data.create"

    def __init__(self) -> None:
        self._service = ApiDataCreateServiceV2()
        self._builder = ApiDataCreateResponseBuilderV2()

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
