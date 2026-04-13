from __future__ import annotations

from typing import Any, Dict


class BaseOrchestratorV2:
    orchestrator_name: str = "base"

    def compose(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        _ = payload
        _ = context
        return {}
