# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from odoo.addons.smart_core.core.ui_base_contract_adapter import adapt_ui_base_contract


def build_orchestrator_input(raw_contract: Dict[str, Any] | None, *, scene_key: str = "") -> Dict[str, Any]:
    adapted = adapt_ui_base_contract(raw_contract, scene_key=scene_key)
    payload = adapted.get("orchestrator_input")
    return payload if isinstance(payload, dict) else {}

