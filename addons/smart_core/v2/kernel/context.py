from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class RequestContextV2:
    trace_id: str = ""
    user_id: int = 0
    company_id: int = 0
    extras: Dict[str, Any] = field(default_factory=dict)
