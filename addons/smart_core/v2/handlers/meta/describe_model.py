from __future__ import annotations

from typing import Any, Dict

from ...builders.meta_describe_model_response_builder import MetaDescribeModelResponseBuilderV2
from ...services.meta_describe_model_service import MetaDescribeModelServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class MetaDescribeModelHandlerV2(BaseIntentHandlerV2):
    intent_name = "meta.describe_model"

    def __init__(self) -> None:
        self._service = MetaDescribeModelServiceV2()
        self._builder = MetaDescribeModelResponseBuilderV2()

    def execute(self, payload: Dict[str, Any], context: HandlerContextV2) -> Dict[str, Any]:
        result = self._service.describe(
            payload=payload or {},
            context={
                "trace_id": str(context.trace_id or ""),
                "user_id": int(context.user_id or 0),
                "company_id": int(context.company_id or 0),
            },
        )
        return self._builder.build(result)
