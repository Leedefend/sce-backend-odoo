from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ApiDataUnlinkResultV2:
    intent: str
    model: str
    ids: List[int]
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
