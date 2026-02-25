# -*- coding: utf-8 -*-
from __future__ import annotations


class SceneDiagnosticsBuilder:
    @staticmethod
    def initial(data: dict, rollback_active: bool, channel_selector: str, channel_source_ref: str) -> dict:
        return {
            "schema_version": data.get("schema_version"),
            "scene_version": data.get("scene_version"),
            "loaded_from": None,
            "normalize_warnings": [],
            "resolve_errors": [],
            "drift": [],
            "rollback_active": bool(rollback_active),
            "rollback_ref": None,
            "channel_selector": channel_selector,
            "channel_source_ref": channel_source_ref,
            "auto_degrade": {"triggered": False, "reason_codes": [], "action_taken": "none"},
            "timings": {},
        }

    @staticmethod
    def governance(contract_mode: str, before_scene_count: int, before_capability_count: int, after_scene_count: int,
                   after_capability_count: int) -> dict:
        return {
            "contract_mode": contract_mode,
            "before": {
                "scene_count": before_scene_count,
                "capability_count": before_capability_count,
            },
            "after": {
                "scene_count": after_scene_count,
                "capability_count": after_capability_count,
            },
            "filtered": {
                "scene_count": max(0, before_scene_count - after_scene_count),
                "capability_count": max(0, before_capability_count - after_capability_count),
            },
        }
