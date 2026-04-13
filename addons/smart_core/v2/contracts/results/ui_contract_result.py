from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class UIContractResultV2:
    intent: str
    contract: Dict[str, Any]
    model: str
    view_type: str
    contract_surface: str
    render_mode: str
    source_mode: str
    governed_from_native: bool
    surface_mapping: Dict[str, Any]
    schema_validated: bool
    trace_id: str
    status: str
    version: str
    phase: str
