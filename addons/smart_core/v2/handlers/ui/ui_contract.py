from __future__ import annotations

from typing import Any, Dict

from ...builders.ui_contract_response_builder import UIContractResponseBuilderV2
from ...services.ui_contract_service import UIContractServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class UIContractHandlerV2(BaseIntentHandlerV2):
    intent_name = "ui.contract"

    def __init__(self) -> None:
        self._service = UIContractServiceV2()
        self._builder = UIContractResponseBuilderV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        result = self._service.build_contract_stub(
            payload=payload or {},
            context={
                "trace_id": str(context.trace_id or ""),
                "user_id": int(context.user_id or 0),
                "company_id": int(context.company_id or 0),
            },
        )
        return self._builder.build(result)
