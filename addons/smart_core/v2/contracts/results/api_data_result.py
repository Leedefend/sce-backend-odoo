from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiDataResultV2:
    intent: str
    model: str
    operation: str
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
