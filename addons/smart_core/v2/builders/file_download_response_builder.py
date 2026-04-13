from __future__ import annotations

from ..contracts.results import FileDownloadResultV2


class FileDownloadResponseBuilderV2:
    def build(self, result: FileDownloadResultV2) -> dict:
        return {
            "intent": str(result.intent or "file.download"),
            "model": str(result.model or ""),
            "res_id": int(result.res_id or 0),
            "name": str(result.name or "download.bin"),
            "schema_validated": bool(result.schema_validated),
            "trace_id": str(result.trace_id or ""),
            "status": str(result.status or "execution_closure"),
            "version": str(result.version or "v2"),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_file_download_response(result: FileDownloadResultV2) -> dict:
    return FileDownloadResponseBuilderV2().build(result)
