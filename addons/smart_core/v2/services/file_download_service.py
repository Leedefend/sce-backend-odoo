from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import FileDownloadResultV2


class FileDownloadServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> FileDownloadResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("file_download handler forced error")

        return FileDownloadResultV2(
            intent="file.download",
            model=str((payload or {}).get("model") or ""),
            res_id=int((payload or {}).get("res_id") or 0),
            name=str((payload or {}).get("name") or "download.bin"),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
