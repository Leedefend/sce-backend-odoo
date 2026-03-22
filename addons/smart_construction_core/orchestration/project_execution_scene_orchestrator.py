# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_execution_service import (
    ProjectExecutionService,
)


class ProjectExecutionSceneOrchestrator:
    ENTRY_SUMMARY_KEYS = (
        "project_code",
        "manager_name",
        "stage_name",
        "date_start",
        "date_end",
    )
    ENTRY_BLOCKS = (
        ("execution_tasks", "执行任务", "deferred"),
        ("pilot_precheck", "试点前检查", "deferred"),
        ("next_actions", "执行下一步", "deferred"),
    )

    def __init__(self, env):
        self.env = env
        self._service = ProjectExecutionService(env)

    def build_entry(self, project_id=None, context=None):
        project, _diag = self._service.resolve_project_with_diagnostics(project_id)
        project_payload = self._service.project_payload(project)
        resolved_project_id = int(project_payload.get("id") or 0)
        blocks = [{"key": key, "title": title, "state": state} for key, title, state in self.ENTRY_BLOCKS]
        if resolved_project_id <= 0:
            return {
                "project_id": 0,
                "scene_key": "project.execution",
                "scene_label": "执行推进",
                "state_fallback_text": "当前状态：正在查看执行推进状态。",
                "title": "项目执行",
                "summary": {key: "" for key in self.ENTRY_SUMMARY_KEYS},
                "blocks": blocks,
                "suggested_action": {},
                "runtime_fetch_hints": {"blocks": {}},
            }

        runtime_fetch_hints = {
            "blocks": {
                key: {
                    "intent": "project.execution.block.fetch",
                    "params": {
                        "project_id": resolved_project_id,
                        "block_key": key,
                    },
                }
                for key, _, _ in self.ENTRY_BLOCKS
            }
        }
        first_action = runtime_fetch_hints["blocks"].get("next_actions") or runtime_fetch_hints["blocks"].get("execution_tasks") or {}
        return {
            "project_id": resolved_project_id,
            "scene_key": "project.execution",
            "scene_label": "执行推进",
            "state_fallback_text": "当前状态：正在查看执行推进状态。",
            "title": "执行推进：%s" % str(project_payload.get("name") or "项目"),
            "summary": {key: str(project_payload.get(key) or "") for key in self.ENTRY_SUMMARY_KEYS},
            "blocks": blocks,
            "suggested_action": {
                "key": "load_execution_next_actions",
                "intent": str(first_action.get("intent") or ""),
                "params": dict(first_action.get("params") or {}),
                "reason_code": "PROJECT_EXECUTION_READY",
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
