# -*- coding: utf-8 -*-
from __future__ import annotations


class BaseSceneEntryOrchestrator:
    """Platform-side helper for minimal scene entry/runtime block carriers."""

    scene_key = ""
    scene_label = ""
    state_fallback_text = ""
    title_empty = ""
    suggested_action_key = ""
    suggested_action_reason_code = ""
    block_fetch_intent = ""
    block_alias_map = {}
    entry_summary_keys = ()
    entry_blocks = ()

    def __init__(self, env, service):
        self.env = env
        self._service = service

    def build_entry(self, project_id=None, context=None):
        project, _diag = self._service.resolve_project_with_diagnostics(project_id)
        project_payload = self._service.project_payload(project)
        resolved_project_id = int(project_payload.get("id") or 0)
        blocks = [{"key": key, "title": title, "state": state} for key, title, state in self.entry_blocks]
        if resolved_project_id <= 0:
            return {
                "project_id": 0,
                "scene_key": self.scene_key,
                "scene_label": self.scene_label,
                "state_fallback_text": self.state_fallback_text,
                "title": self.title_empty,
                "summary": {key: "" for key in self.entry_summary_keys},
                "blocks": blocks,
                "suggested_action": {},
                "runtime_fetch_hints": {"blocks": {}},
            }

        runtime_fetch_hints = {
            "blocks": {
                key: {
                    "intent": self.block_fetch_intent,
                    "params": {
                        "project_id": resolved_project_id,
                        "block_key": key,
                    },
                }
                for key, _, _ in self.entry_blocks
            }
        }
        first_action = self.resolve_first_action(runtime_fetch_hints)
        return {
            "project_id": resolved_project_id,
            "scene_key": self.scene_key,
            "scene_label": self.scene_label,
            "state_fallback_text": self.state_fallback_text,
            "title": self.resolve_title(project_payload),
            "summary": {key: str(project_payload.get(key) or "") for key in self.entry_summary_keys},
            "blocks": blocks,
            "suggested_action": {
                "key": self.suggested_action_key,
                "intent": str(first_action.get("intent") or ""),
                "params": dict(first_action.get("params") or {}),
                "reason_code": self.suggested_action_reason_code,
            },
            "runtime_fetch_hints": runtime_fetch_hints,
        }

    def build_runtime_block(self, block_key, project_id=None, context=None):
        normalized_key = str(block_key or "").strip().lower()
        project, _diag = self._service.resolve_project_with_diagnostics(project_id)
        resolved_project_id = int(getattr(project, "id", 0) or 0)
        block = self._service.build_block(normalized_key, project=project, context=context)
        state = str((block or {}).get("state") or "").strip().lower()
        return {
            "project_id": resolved_project_id,
            "block_key": self.block_alias_map.get(normalized_key, normalized_key or ""),
            "block": block if isinstance(block, dict) else self._service.error_block(normalized_key or "unknown", "INVALID_BLOCK_PAYLOAD"),
            "degraded": state != "ready",
        }

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        for key, _title, _state in self.entry_blocks:
            action = blocks.get(key)
            if isinstance(action, dict) and action:
                return action
        return {}

    def resolve_title(self, project_payload):
        return self.title_empty
