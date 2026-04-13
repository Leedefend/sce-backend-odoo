from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadContractResultV2:
    intent: str
    model: str
    view_type: str
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
