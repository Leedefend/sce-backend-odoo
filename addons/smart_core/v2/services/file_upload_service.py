from __future__ import annotations

from typing import Any, Dict

from ..contracts.results import FileUploadResultV2


class FileUploadServiceV2:
    def execute_stub(self, *, payload: Dict[str, Any], context: Dict[str, Any]) -> FileUploadResultV2:
        if bool((payload or {}).get("raise_handler_error")):
            raise RuntimeError("file_upload handler forced error")

        return FileUploadResultV2(
            intent="file.upload",
            model=str((payload or {}).get("model") or ""),
            res_id=int((payload or {}).get("res_id") or 0),
            name=str((payload or {}).get("name") or "upload.bin"),
            schema_validated=bool((payload or {}).get("schema_validated")),
            trace_id=str((context or {}).get("trace_id") or ""),
            status="execution_closure",
            version="v2",
            phase="boundary_closure",
        )
