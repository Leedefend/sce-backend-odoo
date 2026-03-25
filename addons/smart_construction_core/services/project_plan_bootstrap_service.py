# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.project_plan_bootstrap_builders import BUILDERS


class ProjectPlanBootstrapService:
    """Provide business-truth-backed plan data for orchestration carriers."""
    ENTRY_BLOCKS = (
        ("plan_summary_detail", "计划摘要", "deferred"),
        ("plan_tasks", "计划任务", "deferred"),
        ("next_actions", "计划下一步", "deferred"),
    )
    RUNTIME_BLOCK_MAP = {
        "plan_summary_detail": "block.project.plan_summary_detail",
        "plan_tasks": "block.project.plan_tasks",
        "next_actions": "block.project.plan_next_actions",
    }

    def __init__(self, env):
        self.env = env
        self._builders = [builder_cls(env) for builder_cls in BUILDERS]
        self._builder_map = {builder.block_key: builder for builder in self._builders}

    def build_block(self, block_key, project=None, context=None):
        normalized_key = str(block_key or "").strip().lower()
        builder_key = self.RUNTIME_BLOCK_MAP.get(normalized_key)
        if not builder_key:
            return self.error_block(normalized_key or "unknown", "UNSUPPORTED_BLOCK_KEY")

        builder = self._builder_map.get(builder_key)
        if builder is None:
            block = self.error_block(builder_key, "BLOCK_BUILDER_NOT_FOUND")
        else:
            try:
                block = builder.build(project=project, context=dict(context or {}))
            except Exception:
                block = self.error_block(builder_key, "BLOCK_BUILD_FAILED")
        return block if isinstance(block, dict) else self.error_block(builder_key, "INVALID_BLOCK_PAYLOAD")

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
        if "create_uid" in f:
            ors.append(("create_uid", "=", uid))
        for field in ("user_ids", "member_ids", "member_user_ids"):
            if field in f:
                ors.append((field, "in", [uid]))
        if not ors:
            return []
        if len(ors) == 1:
            return [ors[0]]
        return (["|"] * (len(ors) - 1)) + ors

    def resolve_project_with_diagnostics(self, project_id):
        model_in_env = False
        model_error = ""
        try:
            model_in_env = "project.project" in self.env
        except Exception as exc:
            model_error = str(exc)
        Project = None
        try:
            Project = self.env["project.project"]
        except Exception as exc:
            model_error = str(exc)
        if Project is None:
            return None, {
                "requested_project_id": int(project_id or 0),
                "resolved_project_id": 0,
                "resolution_path": "model_missing",
                "reason": "project.project model not available",
                "model_in_env": model_in_env,
                "model_error": model_error,
            }
        requested_project_id = 0
        try:
            requested_project_id = int(project_id or 0)
        except Exception:
            requested_project_id = 0
        diagnostics = {
            "requested_project_id": requested_project_id,
            "resolved_project_id": 0,
            "resolution_path": "",
            "reason": "",
            "candidate_counts": {},
        }
        if project_id:
            try:
                record = Project.browse(int(project_id)).exists()
                if record:
                    diagnostics.update(
                        {
                            "resolved_project_id": int(record.id),
                            "resolution_path": "explicit_project_id",
                            "reason": "matched explicit project_id",
                        }
                    )
                    return record, diagnostics
                diagnostics["reason"] = "explicit project_id not found or inaccessible"
            except Exception:
                diagnostics["reason"] = "explicit project_id browse failed"
        try:
            if "create_uid" in getattr(Project, "_fields", {}):
                creator_domain = [("create_uid", "=", int(self.env.user.id))]
                diagnostics["candidate_counts"]["creator_domain"] = int(Project.search_count(creator_domain))
                record = Project.search(creator_domain, order="create_date desc,id desc", limit=1)
                if record:
                    diagnostics.update(
                        {
                            "resolved_project_id": int(record.id),
                            "resolution_path": "creator_domain",
                            "reason": "matched latest project created by current user",
                        }
                    )
                    return record, diagnostics
            else:
                diagnostics["candidate_counts"]["creator_domain"] = 0
        except Exception:
            diagnostics["candidate_counts"]["creator_domain"] = -1
            diagnostics["reason"] = "creator_domain search failed"
        domain = self._project_domain_for_user()
        diagnostics["user_domain"] = domain
        try:
            if domain:
                diagnostics["candidate_counts"]["user_domain"] = int(Project.search_count(domain))
            else:
                diagnostics["candidate_counts"]["user_domain"] = 0
            record = Project.search(domain, order="write_date desc,id desc", limit=1)
            if record:
                diagnostics.update(
                    {
                        "resolved_project_id": int(record.id),
                        "resolution_path": "user_domain",
                        "reason": "matched project by user ownership/member domain",
                    }
                )
                return record, diagnostics
        except Exception:
            diagnostics["candidate_counts"]["user_domain"] = -1
            diagnostics["reason"] = "user_domain search failed"
        try:
            diagnostics["candidate_counts"]["global"] = int(Project.search_count([]))
            record = Project.search([], order="write_date desc,id desc", limit=1)
            if record:
                diagnostics.update(
                    {
                        "resolved_project_id": int(record.id),
                        "resolution_path": "global_search",
                        "reason": "matched latest project in global search",
                    }
                )
                return record, diagnostics
        except Exception:
            diagnostics["candidate_counts"]["global"] = -1
            diagnostics["reason"] = "global search failed"
        diagnostics.update(
            {
                "resolved_project_id": 0,
                "resolution_path": diagnostics.get("resolution_path") or "no_match",
                "reason": diagnostics.get("reason") or "no project resolved",
            }
        )
        return None, diagnostics

    def project_payload(self, project):
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
                "state": "empty",
            }
        return {
            "id": int(project.id),
            "name": _safe_text(_safe_field(project, "name")),
            "project_code": _safe_text(_safe_field(project, "project_code")),
            "manager_name": _safe_rel_name(project, "user_id"),
            "stage_name": _safe_rel_name(project, "stage_id"),
            "date_start": str(_safe_field(project, "date_start") or ""),
            "date_end": str(_safe_field(project, "date") or _safe_field(project, "date_end") or ""),
            "state": "ready",
            "today": str(fields.Date.today()),
        }

    @staticmethod
    def error_block(block_key, code):
        return {
            "block_key": block_key,
            "block_type": "unknown",
            "title": block_key,
            "state": "error",
            "visibility": {"allowed": True, "reason_code": "OK", "reason": ""},
            "data": {},
            "error": {"code": code, "message": code},
        }
