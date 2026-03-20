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
        feature_flags: dict,
        capabilities: list,
        scene_channel: str,
        channel_selector: str,
        channel_source_ref: str,
        contract_mode: str,
        contract_version: str,
    ) -> dict:
        return {
            "user": user_dict,
            "nav": nav_tree,
            "nav_meta": nav_meta,
            "default_route": default_route,
            "intents": intents,
            "feature_flags": feature_flags,
            "capabilities": capabilities,
            "capability_groups": [],
            "preload": [],
            "scenes": [],
            "scene_version": "v1",
            "schema_version": "1.0.0",
            "contract_version": contract_version,
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

    @staticmethod
    def attach_preload(data: dict, home_contract, etags: dict, preload_items: list) -> None:
        if home_contract:
            data["preload"].append({"key": "home", "etag": etags.get("home")})
        if preload_items:
            data["preload"].extend(preload_items)

    @staticmethod
    def attach_layered_contract(data: dict) -> None:
        role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
        landing_scene_key = str(role_surface.get("landing_scene_key") or "").strip() or "portal.dashboard"
        contract_version = str(data.get("contract_version") or "1.0.0")
        schema_version = str(data.get("schema_version") or "1.0.0")
        sections_payload = {
            "contract_version": contract_version,
            "schema_version": schema_version,
            "session": {
                "user": data.get("user"),
                "contract_mode": data.get("contract_mode"),
                "scene_channel": data.get("scene_channel"),
            },
            "nav": {
                "nav": data.get("nav"),
                "default_route": data.get("default_route"),
                "nav_meta": data.get("nav_meta"),
            },
            "surface": {
                "role_surface": data.get("role_surface"),
                "role_surface_map": data.get("role_surface_map"),
                "capabilities": data.get("capabilities"),
                "capability_groups": data.get("capability_groups"),
                "feature_flags": data.get("feature_flags"),
            },
            "bootstrap_refs": {
                "workspace_home_ref": {
                    "intent": "ui.contract",
                    "scene_key": landing_scene_key,
                }
            },
        }
        data["system_init_sections_v1"] = sections_payload
        data["init_contract_v1"] = sections_payload
