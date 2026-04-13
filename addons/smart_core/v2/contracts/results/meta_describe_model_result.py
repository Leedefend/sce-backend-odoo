from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class MetaDescribeModelResultV2:
    intent: str
    model: str
    display_name: str
    fields: Dict[str, Any]
    can_read: bool
    can_write: bool
    source: str
    version: str
    schema_validated: bool
    phase: str
