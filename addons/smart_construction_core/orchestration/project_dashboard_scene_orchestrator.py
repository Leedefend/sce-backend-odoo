# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


class ProjectDashboardSceneOrchestrator:
    LEGACY_ORCHESTRATION_MODE = "industry_local"

    ENTRY_SUMMARY_KEYS = (
        "project_code",
        "manager_name",
        "partner_name",
        "stage_name",
        "health_state",
    )
    ENTRY_BLOCKS = (
        ("progress", "项目进度", "deferred"),
        ("risks", "风险提醒", "deferred"),
        ("next_actions", "下一步动作", "deferred"),
    )

    def __init__(self, env):
        self.env = env
        self._service = ProjectDashboardService(env)

    def build_entry(self, project_id=None, context=None):
        project, _diag = self._service.resolve_project_with_diagnostics(project_id)
        project_payload = self._service.project_payload(project)
        resolved_project_id = int(project_payload.get("id") or 0)
        blocks = [{"key": key, "title": title, "state": state} for key, title, state in self.ENTRY_BLOCKS]
        if resolved_project_id <= 0:
            return {
                "project_id": 0,
                "scene_key": "project.dashboard",
                "scene_label": "项目驾驶舱",
                "state_fallback_text": "当前状态：已完成立项，正在查看项目驾驶舱。",
                "title": "项目驾驶舱",
                "summary": {key: "" for key in self.ENTRY_SUMMARY_KEYS},
                "blocks": blocks,
                "suggested_action": {},
                "runtime_fetch_hints": {"blocks": {}},
            }

        runtime_fetch_hints = {
            "blocks": {
                key: {
                    "intent": "project.dashboard.block.fetch",
                    "params": {
                        "project_id": resolved_project_id,
                        "block_key": key,
                    },
                }
                for key, _, _ in self.ENTRY_BLOCKS
            }
        }
        first_action = runtime_fetch_hints["blocks"].get("progress") or {}
        return {
            "project_id": resolved_project_id,
            "scene_key": "project.dashboard",
            "scene_label": "项目驾驶舱",
            "state_fallback_text": "当前状态：已完成立项，正在查看项目驾驶舱。",
            "title": "项目驾驶舱：%s" % str(project_payload.get("name") or "项目"),
            "summary": {key: str(project_payload.get(key) or "") for key in self.ENTRY_SUMMARY_KEYS},
            "blocks": blocks,
            "suggested_action": {
                "key": "load_dashboard_progress",
                "intent": str(first_action.get("intent") or ""),
                "params": dict(first_action.get("params") or {}),
                "reason_code": "PROJECT_DASHBOARD_READY",
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
            "block_key": "risks" if normalized_key == "risk" else normalized_key,
            "block": block if isinstance(block, dict) else self._service.error_block(normalized_key or "unknown", "INVALID_BLOCK_PAYLOAD"),
            "degraded": state != "ready",
        }
