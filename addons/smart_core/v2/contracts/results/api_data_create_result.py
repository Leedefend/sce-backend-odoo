from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiDataCreateResultV2:
    intent: str
    model: str
    value_count: int
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
