from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class FirstScenarioResultV2:
    intent: str
    app_key: str
    model: str
    view_type: str
    session: Dict[str, Any]
    model_meta: Dict[str, Any]
    ui_contract: Dict[str, Any]
    chain_status: Dict[str, Any]
    version: str
    source: str
