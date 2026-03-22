# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import (
    ProjectPlanBootstrapService,
)


class ProjectPlanBootstrapSceneOrchestrator:
    LEGACY_ORCHESTRATION_MODE = "industry_local"

    ENTRY_SUMMARY_KEYS = (
        "project_code",
        "manager_name",
        "stage_name",
        "date_start",
        "date_end",
    )
    ENTRY_BLOCKS = (
        ("plan_summary_detail", "计划摘要", "deferred"),
        ("plan_tasks", "计划任务", "deferred"),
        ("next_actions", "计划下一步", "deferred"),
    )

    def __init__(self, env):
        self.env = env
        self._service = ProjectPlanBootstrapService(env)

    def build_entry(self, project_id=None, context=None):
        project, _diag = self._service.resolve_project_with_diagnostics(project_id)
        project_payload = self._service.project_payload(project)
        resolved_project_id = int(project_payload.get("id") or 0)
        blocks = [{"key": key, "title": title, "state": state} for key, title, state in self.ENTRY_BLOCKS]
        if resolved_project_id <= 0:
            return {
                "project_id": 0,
                "scene_key": "project.plan_bootstrap",
                "scene_label": "计划准备",
                "state_fallback_text": "当前状态：正在核对计划准备度。",
                "title": "计划编排",
                "summary": {key: "" for key in self.ENTRY_SUMMARY_KEYS},
                "blocks": blocks,
                "suggested_action": {},
                "runtime_fetch_hints": {"blocks": {}},
            }

        runtime_fetch_hints = {
            "blocks": {
                key: {
                    "intent": "project.plan_bootstrap.block.fetch",
                    "params": {
                        "project_id": resolved_project_id,
                        "block_key": key,
                    },
                }
                for key, _, _ in self.ENTRY_BLOCKS
            }
        }
        first_action = runtime_fetch_hints["blocks"].get("next_actions") or runtime_fetch_hints["blocks"].get("plan_summary_detail") or {}
        return {
            "project_id": resolved_project_id,
            "scene_key": "project.plan_bootstrap",
            "scene_label": "计划准备",
            "state_fallback_text": "当前状态：正在核对计划准备度。",
            "title": "计划准备：%s" % str(project_payload.get("name") or "项目"),
            "summary": {key: str(project_payload.get(key) or "") for key in self.ENTRY_SUMMARY_KEYS},
            "blocks": blocks,
            "suggested_action": {
                "key": "load_plan_next_actions",
                "intent": str(first_action.get("intent") or ""),
                "params": dict(first_action.get("params") or {}),
                "reason_code": "PROJECT_PLAN_BOOTSTRAP_READY",
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
            "block_key": normalized_key or "",
            "block": block if isinstance(block, dict) else self._service.error_block(normalized_key or "unknown", "INVALID_BLOCK_PAYLOAD"),
            "degraded": state != "ready",
        }
