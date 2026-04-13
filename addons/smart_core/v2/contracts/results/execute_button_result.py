from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecuteButtonResultV2:
    intent: str
    model: str
    record_id: int
    button_name: str
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
