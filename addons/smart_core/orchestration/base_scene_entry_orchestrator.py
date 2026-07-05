# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


class BaseSceneEntryOrchestrator:
    """Platform-side helper for minimal scene entry/runtime block carriers."""

    SOURCE_KIND = "scene_entry_runtime_projection_adapter"
    SOURCE_AUTHORITIES = ("scene_runtime_service", "odoo.orm")
    ADAPTER_LAYER = "industry_orchestration_adapter"
    NO_BUSINESS_FACT_AUTHORITY = True
    LEGACY_SCENE_COPY_SOURCE_KIND = "legacy_scene_entry_copy_projection"

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
    first_action_block_keys = ()
    title_template = ""
    title_record_name_fallback = ""

    def __init__(self, env, service):
        self.env = env
        self._service = service
        self._apply_scene_entry_spec()

    def _apply_scene_entry_spec(self):
        specs = call_extension_hook_first(self.env, "smart_core_scene_entry_orchestrator_specs", self.env)
        specs = specs if isinstance(specs, dict) else {}
        spec = specs.get(type(self).__name__)
        if not isinstance(spec, dict):
            spec = specs.get(str(getattr(self, "scene_key", "") or ""))
        if not isinstance(spec, dict):
            return
        scalar_fields = (
            "scene_key",
            "scene_label",
            "state_fallback_text",
            "title_empty",
            "suggested_action_key",
            "suggested_action_reason_code",
            "block_fetch_intent",
            "title_template",
            "title_record_name_fallback",
        )
        for field in scalar_fields:
            if field in spec:
                setattr(self, field, str(spec.get(field) or "").strip())
        if isinstance(spec.get("block_alias_map"), dict):
            self.block_alias_map = dict(spec.get("block_alias_map") or {})
        if isinstance(spec.get("entry_summary_keys"), (list, tuple)):
            self.entry_summary_keys = tuple(str(item or "").strip() for item in spec["entry_summary_keys"] if str(item or "").strip())
        if isinstance(spec.get("entry_blocks"), (list, tuple)):
            blocks = []
            for item in spec["entry_blocks"]:
                if isinstance(item, dict):
                    key = str(item.get("key") or "").strip()
                    title = str(item.get("title") or "").strip()
                    state = str(item.get("state") or "deferred").strip() or "deferred"
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    key = str(item[0] or "").strip()
                    title = str(item[1] or "").strip()
                    state = str(item[2] if len(item) > 2 else "deferred").strip() or "deferred"
                else:
                    continue
                if key:
                    blocks.append((key, title, state))
            self.entry_blocks = tuple(blocks)
        if isinstance(spec.get("first_action_block_keys"), (list, tuple)):
            self.first_action_block_keys = tuple(str(item or "").strip() for item in spec["first_action_block_keys"] if str(item or "").strip())

    def source_authority_contract(self):
        provider = getattr(self._service, "source_authority_contract", None)
        delegated_source = None
        if callable(provider):
            delegated = provider()
            delegated_source = delegated if isinstance(delegated, dict) else None
        contract = {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            "adapter_layer": self.ADAPTER_LAYER,
            "runtime_carrier": "scene_entry_and_block_contract",
            "legacy_scene_copy_source": self.LEGACY_SCENE_COPY_SOURCE_KIND,
        }
        if delegated_source:
            contract["delegated_source_authority"] = delegated_source
        return contract

    def legacy_scene_copy_source_authority_contract(self):
        return {
            "kind": self.LEGACY_SCENE_COPY_SOURCE_KIND,
            "authorities": [
                "scene_label",
                "state_fallback_text",
                "title_empty",
                "entry_blocks",
                "resolve_title",
            ],
            "projection_only": True,
            "no_business_fact_authority": True,
            "legacy_compatibility": True,
        }

    def delegated_source_authority_contract(self):
        provider = getattr(self._service, "source_authority_contract", None)
        if callable(provider):
            delegated = provider()
            if isinstance(delegated, dict):
                return delegated
        return {
            "kind": "scene_entry_business_fact_projection",
            "authorities": ["odoo.orm"],
            "projection_only": True,
            "runtime_carrier": "scene_entry_and_block_contract",
        }

    def build_entry(self, project_id=None, context=None):
        project, _diag = self._service.resolve_project_with_diagnostics(project_id)
        project_payload = self._service.project_payload(project)
        resolved_project_id = int(project_payload.get("id") or 0)
        blocks = [{"key": key, "title": title, "state": state} for key, title, state in self.entry_blocks]
        source_authority = self.source_authority_contract()
        copy_source_authority = self.legacy_scene_copy_source_authority_contract()
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
                "lifecycle_hints": self._build_lifecycle_hints(
                    project_id=0,
                    first_action={},
                    stage="entry_missing_project",
                ),
                "source_authority": source_authority,
                "legacy_scene_copy_source_authority": copy_source_authority,
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
            "lifecycle_hints": self._build_lifecycle_hints(
                project_id=resolved_project_id,
                first_action=first_action,
                stage="entry_ready",
            ),
            "source_authority": source_authority,
            "legacy_scene_copy_source_authority": copy_source_authority,
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
            "source_authority": self.source_authority_contract(),
            "legacy_scene_copy_source_authority": self.legacy_scene_copy_source_authority_contract(),
        }

    def resolve_first_action(self, runtime_fetch_hints):
        blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        for key in self.first_action_block_keys:
            action = blocks.get(key)
            if isinstance(action, dict) and action:
                return action
        for key, _title, _state in self.entry_blocks:
            action = blocks.get(key)
            if isinstance(action, dict) and action:
                return action
        return {}

    def resolve_title(self, project_payload):
        template = str(self.title_template or "").strip()
        if template:
            name = str(project_payload.get("name") or self.title_record_name_fallback or "").strip()
            try:
                return template.format(name=name, **project_payload)
            except Exception:
                return template.replace("{name}", name)
        return self.title_empty

    def _build_lifecycle_hints(self, project_id, first_action, stage):
        resolved_project_id = int(project_id or 0)
        action = first_action if isinstance(first_action, dict) else {}
        action_intent = str(action.get("intent") or "").strip()
        action_key = str(self.suggested_action_key or "").strip()
        default_next_label = str(action_key or action_intent or "continue").replace("_", " ").strip()
        return {
            "stage": str(stage or "entry").strip() or "entry",
            "project_id": resolved_project_id,
            "scene_key": str(self.scene_key or "").strip(),
            "reason_code": str(self.suggested_action_reason_code or "").strip(),
            "primary_action_label": str(self.scene_label or self.title_empty or "继续").strip(),
            "next_step_label": default_next_label or "continue",
            "suggested_action_intent": action_intent,
        }
