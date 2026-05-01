# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectExecutionHintService:
    @staticmethod
    def build_suggested_action(project_id: int, reason_code: str) -> dict:
        return {
            "key": "refresh_execution_next_actions",
            "intent": "project.execution.block.fetch",
            "params": {"project_id": int(project_id), "block_key": "next_actions"},
            "reason_code": reason_code,
        }

    @staticmethod
    def build_lifecycle_hints(project_id: int, reason_code: str) -> dict:
        if int(project_id or 0) > 0:
            return {
                "stage": "execution_blocked",
                "first_action": "refresh_execution_next_actions",
                "primary_action_label": "刷新下一步动作",
                "suggested_action_intent": "project.execution.block.fetch",
                "suggested_action_title": "刷新下一步动作",
                "reason_code": str(reason_code or ""),
            }
        return {
            "stage": "no_project_context",
            "first_action": "create_project",
            "primary_action_label": "创建项目",
            "suggested_action_intent": "project.initiation.enter",
            "suggested_action_title": "创建项目",
            "reason_code": str(reason_code or "PROJECT_CONTEXT_MISSING"),
        }
