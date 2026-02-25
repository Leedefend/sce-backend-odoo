# -*- coding: utf-8 -*-
from __future__ import annotations


class SystemInitPayloadBuilder:
    @staticmethod
    def build_base(
        *,
        user_dict: dict,
        nav_tree: list,
        nav_meta: dict,
        default_route: dict,
        intents,
        intents_meta,
        feature_flags: dict,
        capabilities: list,
        scene_channel: str,
        channel_selector: str,
        channel_source_ref: str,
        contract_mode: str,
    ) -> dict:
        return {
            "user": user_dict,
            "nav": nav_tree,
            "nav_meta": nav_meta,
            "default_route": default_route,
            "intents": intents,
            "intents_meta": intents_meta,
            "feature_flags": feature_flags,
            "capabilities": capabilities,
            "capability_groups": [],
            "preload": [],
            "scenes": [],
            "scene_version": "v1",
            "schema_version": "v1",
            "scene_channel": scene_channel,
            "scene_channel_selector": channel_selector,
            "scene_channel_source_ref": channel_source_ref,
            "scene_contract_ref": None,
            "contract_mode": contract_mode,
            "ext_facts": {},
        }

    @staticmethod
    def attach_hud(data: dict, trace_id: str, elapsed_ms: int, contract_version: str, scene_trace_meta: dict) -> None:
        data["hud"] = {
            "trace_id": trace_id,
            "latency_ms": elapsed_ms,
            "contract_version": contract_version,
            "role_key": data.get("role_surface", {}).get("role_code"),
            **scene_trace_meta,
        }

    @staticmethod
    def attach_diagnostic(data: dict, diagnostic_info: dict) -> None:
        data["diagnostic"] = diagnostic_info
