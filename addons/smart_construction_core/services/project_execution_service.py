# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_execution_builders import BUILDERS


class ProjectExecutionService:
    """Assemble project.execution minimal entry and runtime blocks."""

    ENTRY_SUMMARY_KEYS = (
        "project_code",
        "manager_name",
        "stage_name",
        "date_start",
        "date_end",
    )
    ENTRY_BLOCKS = (
        ("execution_tasks", "执行任务", "deferred"),
        ("next_actions", "执行下一步", "deferred"),
    )
    RUNTIME_BLOCK_MAP = {
        "execution_tasks": "block.project.execution_tasks",
        "next_actions": "block.project.execution_next_actions",
    }

    def __init__(self, env):
        self.env = env
        self._builders = [builder_cls(env) for builder_cls in BUILDERS]
        self._builder_map = {builder.block_key: builder for builder in self._builders}

    def build_entry(self, project_id=None, context=None):
        project, _diag = self._resolve_project_with_diagnostics(project_id)
        project_payload = self._project_payload(project)
        resolved_project_id = int(project_payload.get("id") or 0)
        blocks = [{"key": key, "title": title, "state": state} for key, title, state in self.ENTRY_BLOCKS]
        if resolved_project_id <= 0:
            return {
                "project_id": 0,
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
            "title": "项目执行：%s" % str(project_payload.get("name") or "项目"),
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
        builder_key = self.RUNTIME_BLOCK_MAP.get(normalized_key)
        project, _diag = self._resolve_project_with_diagnostics(project_id)
        resolved_project_id = int(getattr(project, "id", 0) or 0)
        if not builder_key:
            return {
                "project_id": resolved_project_id,
                "block_key": normalized_key or "",
                "block": self._error_block(normalized_key or "unknown", "UNSUPPORTED_BLOCK_KEY"),
                "degraded": True,
            }

        builder = self._builder_map.get(builder_key)
        if builder is None:
            block = self._error_block(builder_key, "BLOCK_BUILDER_NOT_FOUND")
        else:
            try:
                block = builder.build(project=project, context=dict(context or {}))
            except Exception:
                block = self._error_block(builder_key, "BLOCK_BUILD_FAILED")
        state = str((block or {}).get("state") or "").strip().lower()
        return {
            "project_id": resolved_project_id,
            "block_key": normalized_key or "",
            "block": block if isinstance(block, dict) else self._error_block(builder_key, "INVALID_BLOCK_PAYLOAD"),
            "degraded": state != "ready",
        }

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_domain_for_user(self):
        model = self._model("project.project")
        if model is None:
            return []
        f = getattr(model, "_fields", {})
        uid = int(self.env.user.id)
        ors = []
        for field in ("manager_id", "owner_id", "user_id"):
            if field in f:
                ors.append((field, "=", uid))
        for field in ("user_ids", "member_ids", "member_user_ids"):
            if field in f:
                ors.append((field, "in", [uid]))
        if not ors:
            return []
        if len(ors) == 1:
            return [ors[0]]
        return (["|"] * (len(ors) - 1)) + ors

    def _resolve_project_with_diagnostics(self, project_id):
        Project = self._model("project.project")
        if Project is None:
            return None, {"resolved_project_id": 0, "reason": "project.project model not available"}
        requested_project_id = int(project_id or 0) if str(project_id or "").strip() else 0
        if requested_project_id > 0:
            try:
                record = Project.browse(requested_project_id).exists()
                if record:
                    return record, {"resolved_project_id": int(record.id), "reason": "explicit_project_id"}
            except Exception:
                pass
        domain = self._project_domain_for_user()
        try:
            record = Project.search(domain, order="write_date desc,id desc", limit=1)
            if record:
                return record, {"resolved_project_id": int(record.id), "reason": "user_domain"}
        except Exception:
            pass
        try:
            record = Project.search([], order="write_date desc,id desc", limit=1)
            if record:
                return record, {"resolved_project_id": int(record.id), "reason": "global_search"}
        except Exception:
            pass
        return None, {"resolved_project_id": 0, "reason": "no project resolved"}

    def _project_payload(self, project):
        def _safe_text(value):
            try:
                return str(value or "")
            except Exception:
                return ""

        def _safe_rel_name(record, field_name):
            try:
                relation = getattr(record, field_name, None)
            except Exception:
                return ""
            return _safe_text(getattr(relation, "display_name", ""))

        def _safe_field(record, field_name):
            try:
                return getattr(record, field_name, "")
            except Exception:
                return ""

        if not project:
            return {
                "id": 0,
                "name": "",
                "project_code": "",
                "manager_name": "",
                "stage_name": "",
                "date_start": "",
                "date_end": "",
            }
        return {
            "id": int(project.id),
            "name": _safe_text(_safe_field(project, "name")),
            "project_code": _safe_text(_safe_field(project, "project_code")),
            "manager_name": _safe_rel_name(project, "user_id"),
            "stage_name": _safe_rel_name(project, "stage_id"),
            "date_start": str(_safe_field(project, "date_start") or ""),
            "date_end": str(_safe_field(project, "date") or _safe_field(project, "date_end") or ""),
            "today": str(fields.Date.today()),
        }

    @staticmethod
    def _error_block(block_key, code):
        return {
            "block_key": block_key,
            "block_type": "unknown",
            "title": block_key,
            "state": "error",
            "visibility": {"allowed": True, "reason_code": "OK", "reason": ""},
            "data": {},
            "error": {"code": code, "message": code},
        }
