from __future__ import annotations

from typing import Any, Dict


class FileUploadRequestSchemaV2:
    schema_name = "v2.file.upload.request.v1"

    @staticmethod
    def validate(payload: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        model = str(data.get("model") or "").strip()
        if not model:
            raise ValueError("model is required")

        res_id = data.get("res_id")
        if res_id in (None, ""):
            raise ValueError("res_id is required")

        normalized_res_id = int(res_id)

        filename = str(data.get("name") or "upload.bin").strip() or "upload.bin"
        file_data = str(data.get("data") or "").strip()
        if not file_data:
            raise ValueError("data is required")

        trace_id = ""
        if isinstance(context, dict):
            trace_id = str(context.get("trace_id") or "")

        return {
            "model": model,
            "res_id": normalized_res_id,
            "name": filename,
            "data": file_data,
            "schema_validated": True,
            "schema_trace_id": trace_id,
            "raise_handler_error": bool(data.get("raise_handler_error")),
        }
