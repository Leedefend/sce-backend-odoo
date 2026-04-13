from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiOnchangeResultV2:
    intent: str
    model: str
    field_name: str
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
