from __future__ import annotations

from typing import Any, Dict

from ...builders.file_download_response_builder import FileDownloadResponseBuilderV2
from ...services.file_download_service import FileDownloadServiceV2
from ..base import BaseIntentHandlerV2, HandlerContextV2


class FileDownloadHandlerV2(BaseIntentHandlerV2):
    intent_name = "file.download"

    def __init__(self) -> None:
        self._service = FileDownloadServiceV2()
        self._builder = FileDownloadResponseBuilderV2()

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
