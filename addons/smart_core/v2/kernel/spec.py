from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Any


@dataclass(frozen=True)
class IntentSpecV2:
    intent_name: str
    permission_mode: str
    request_schema: str
    response_contract: str
    version: str
    handler_factory: Callable[[], Any]
