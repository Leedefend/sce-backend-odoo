from __future__ import annotations

from typing import Any, Dict

from ...builders.file_upload_response_builder import FileUploadResponseBuilderV2
from ...services.file_upload_service import FileUploadServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class FileUploadHandlerV2(BaseIntentHandlerV2):
    intent_name = "file.upload"

    def __init__(self) -> None:
        self._service = FileUploadServiceV2()
        self._builder = FileUploadResponseBuilderV2()

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
