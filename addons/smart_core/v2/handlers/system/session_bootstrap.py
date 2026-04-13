from __future__ import annotations

from typing import Any, Dict

from ...builders.session_bootstrap_response_builder import SessionBootstrapResponseBuilderV2
from ...services.session_bootstrap_service import SessionBootstrapServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class SessionBootstrapHandlerV2(BaseIntentHandlerV2):
    intent_name = "session.bootstrap"

    def __init__(self) -> None:
        self._service = SessionBootstrapServiceV2()
        self._builder = SessionBootstrapResponseBuilderV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        result = self._service.bootstrap(
            payload=payload or {},
            context={
                "trace_id": str(context.trace_id or ""),
                "user_id": int(context.user_id or 0),
                "company_id": int(context.company_id or 0),
                "registry_snapshot": tuple(context.registry_snapshot or ()),
            },
        )
        return self._builder.build(result)
