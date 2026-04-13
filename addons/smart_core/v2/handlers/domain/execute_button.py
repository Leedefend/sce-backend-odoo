from __future__ import annotations

from typing import Any, Dict

from ...builders.execute_button_response_builder import ExecuteButtonResponseBuilderV2
from ...services.execute_button_service import ExecuteButtonServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class ExecuteButtonHandlerV2(BaseIntentHandlerV2):
    intent_name = "execute_button"

    def __init__(self) -> None:
        self._service = ExecuteButtonServiceV2()
        self._builder = ExecuteButtonResponseBuilderV2()

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
