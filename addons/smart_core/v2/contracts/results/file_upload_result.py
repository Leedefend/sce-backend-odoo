from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileUploadResultV2:
    intent: str
    model: str
    res_id: int
    name: str
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
