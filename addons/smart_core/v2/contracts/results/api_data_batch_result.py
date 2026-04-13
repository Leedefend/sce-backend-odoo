from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiDataBatchResultV2:
    intent: str
    model: str
    operation_count: int
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
