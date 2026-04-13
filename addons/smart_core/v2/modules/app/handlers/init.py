from __future__ import annotations

from typing import Any, Dict

from ....handlers.base import BaseIntentHandlerV2, HandlerContextV2
from ..builders.first_scenario_builder import build_first_scenario_contract
from ..services.first_scenario_service import FirstScenarioServiceV2


class AppInitHandlerV2(BaseIntentHandlerV2):
    intent_name = "app.init"

    def __init__(self) -> None:
        self._service = FirstScenarioServiceV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        result = self._service.assemble(
            payload=payload or {},
            context={
                "trace_id": str(context.trace_id or ""),
                "user_id": int(context.user_id or 0),
                "company_id": int(context.company_id or 0),
            },
        )
        return build_first_scenario_contract(result)
