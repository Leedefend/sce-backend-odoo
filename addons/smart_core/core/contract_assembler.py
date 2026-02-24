# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.app_config_engine.utils.misc import stable_etag


class ContractAssembler:
    def build_scene_trace_meta(self, data: dict, scene_diagnostics: dict | None, elapsed_ms: int) -> dict:
        diagnostics = scene_diagnostics if isinstance(scene_diagnostics, dict) else {}
        governance = diagnostics.get("governance")
        return {
            "latency_ms": int(elapsed_ms),
            "scene_source": diagnostics.get("loaded_from") or "unknown",
            "scene_contract_ref": data.get("scene_contract_ref") or "unknown",
            "scene_channel": data.get("scene_channel") or "stable",
            "channel_selector": diagnostics.get("channel_selector") or "default",
            "channel_source_ref": diagnostics.get("channel_source_ref") or "default",
            "governance": governance,
            "governance_applied": governance,
        }

    def build_top_etag(self, data: dict, nav_fp: str, contract_mode: str, contract_version: str, api_version: str):
        return stable_etag({
            "user": data["user"],
            "nav_fp": nav_fp,
            "default_route": data["default_route"],
            "feature_flags": data["feature_flags"],
            "intents": data["intents"],
            "scenes": data.get("scenes"),
            "scene_channel": data.get("scene_channel"),
            "scene_contract_ref": data.get("scene_contract_ref"),
            "capabilities": data.get("capabilities"),
            "capability_groups": data.get("capability_groups"),
            "contract_mode": contract_mode,
            "contract_version": contract_version,
            "api_version": api_version,
        })

    def build_meta(
        self,
        *,
        elapsed_ms: int,
        nav_versions,
        parts_version,
        etags,
        intent_type: str,
        contract_version: str,
        api_version: str,
        contract_mode: str,
        scene_trace_meta: dict,
    ) -> dict:
        return {
            "elapsed_ms": elapsed_ms,
            "parts": {"nav": nav_versions, **parts_version},
            "etags": etags,
            "intent": intent_type,
            "contract_version": contract_version,
            "api_version": api_version,
            "contract_mode": contract_mode,
            "scene_trace": scene_trace_meta,
        }
