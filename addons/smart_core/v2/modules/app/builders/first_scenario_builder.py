from __future__ import annotations

from ....contracts.results import FirstScenarioResultV2


def build_first_scenario_contract(result: FirstScenarioResultV2) -> dict:
    return {
        "intent": str(result.intent or "app.init"),
        "app_key": str(result.app_key or "platform"),
        "model": str(result.model or ""),
        "view_type": str(result.view_type or "form"),
        "session": dict(result.session or {}),
        "model_meta": dict(result.model_meta or {}),
        "ui_contract": dict(result.ui_contract or {}),
        "chain_status": dict(result.chain_status or {}),
        "version": str(result.version or "v2"),
        "source": str(result.source or "v2-first-scenario"),
    }
