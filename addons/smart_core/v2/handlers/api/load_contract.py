from __future__ import annotations

from typing import Any, Dict

from ...builders.load_contract_response_builder import LoadContractResponseBuilderV2
from ...services.load_contract_service import LoadContractServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class LoadContractHandlerV2(BaseIntentHandlerV2):
    intent_name = "load_contract"

    def __init__(self) -> None:
        self._service = LoadContractServiceV2()
        self._builder = LoadContractResponseBuilderV2()

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
