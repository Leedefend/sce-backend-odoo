from __future__ import annotations

from typing import Any, Dict

from ...builders.api_data_unlink_response_builder import ApiDataUnlinkResponseBuilderV2
from ...services.api_data_unlink_service import ApiDataUnlinkServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class ApiDataUnlinkHandlerV2(BaseIntentHandlerV2):
    intent_name = "api.data.unlink"

    def __init__(self) -> None:
        self._service = ApiDataUnlinkServiceV2()
        self._builder = ApiDataUnlinkResponseBuilderV2()

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
