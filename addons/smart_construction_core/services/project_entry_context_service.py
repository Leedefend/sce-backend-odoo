# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_context_contract import (
    build_project_context,
)
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


class ProjectEntryContextService:
    ENTRY_ROUTE = "/s/project.management"
    _NOISY_NAME_PREFIXES = (
        "SCENE-CONTRACT-",
        "SCENE-AUDIT-",
        "RAW-",
    )

    def __init__(self, env):
        self.env = env
        self._dashboard_service = ProjectDashboardService(env)

    @staticmethod
    def _source_from_reason(resolution_path):
        normalized = str(resolution_path or "").strip().lower()
        if normalized == "explicit_project_id":
            return "current", "high"
        if normalized == "creator_domain":
            return "recent", "high"
        if normalized == "user_domain":
            return "current", "medium"
        if normalized in {"global_search", "active_search_read"}:
            return "fallback", "low"
        return "fallback", "low"

    @staticmethod
    def _build_lifecycle_guidance(*, available=False, project_context=None):
        project_id = int((project_context or {}).get("project_id") or 0)
        if available and project_id > 0:
            return {
                "suggested_action": {
                    "intent": "project.dashboard.enter",
                    "reason_code": "PROJECT_CONTEXT_READY",
                    "params": {"project_id": project_id},
                },
                "lifecycle_hints": {
                    "stage": "project_context_ready",
                    "project_id": project_id,
                    "primary_action_label": "进入项目管理",
                    "suggested_action_intent": "project.dashboard.enter",
                    "suggested_action_title": "进入项目管理",
                },
            }
        return {
            "suggested_action": {
                "intent": "project.initiation.enter",
                "reason_code": "PROJECT_CONTEXT_MISSING",
                "params": {},
            },
            "lifecycle_hints": {
                "stage": "no_project_context",
                "project_id": 0,
                "primary_action_label": "创建项目",
                "suggested_action_intent": "project.initiation.enter",
                "suggested_action_title": "创建项目",
            },
        }

    def resolve(self, project_id=0):
        project, diagnostics = self._dashboard_service.resolve_project_with_diagnostics(project_id)
        project_context = build_project_context(project)
        source, confidence = self._source_from_reason((diagnostics or {}).get("resolution_path"))
        available = int(project_context.get("project_id") or 0) > 0
        guidance = self._build_lifecycle_guidance(available=available, project_context=project_context)
        diagnostics_summary = self._build_diagnostics_summary(
            resolution_path=(diagnostics or {}).get("resolution_path"),
            available=available,
            option_count=0,
        )
        return {
            "available": available,
            "project_context": project_context,
            "source": source if available else "none",
            "confidence": confidence if available else "low",
            "route": self.ENTRY_ROUTE if available else "/my-work",
            "suggested_action": dict(guidance.get("suggested_action") or {}),
            "lifecycle_hints": dict(guidance.get("lifecycle_hints") or {}),
            "diagnostics": diagnostics or {},
            "diagnostics_summary": dict(diagnostics_summary or {}),
        }

    @classmethod
    def _is_noisy_project_name(cls, name):
        normalized = str(name or "").strip().upper()
        if not normalized:
            return False
        return any(normalized.startswith(prefix) for prefix in cls._NOISY_NAME_PREFIXES)

    @classmethod
    def _is_demo_showroom_project(cls, name):
        normalized = str(name or "").strip()
        return normalized.startswith("展厅-")

    @classmethod
    def _project_rank(cls, project, active_project_id=0):
        context = build_project_context(project)
        project_id = int(context.get("project_id") or 0)
        project_name = str(context.get("project_name") or "")
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        showcase = bool(getattr(project, "sc_demo_showcase", False))
        showcase_ready = bool(getattr(project, "sc_demo_showcase_ready", False))
        noisy = cls._is_noisy_project_name(project_name)
        rank = 0
        if project_id and project_id == int(active_project_id or 0):
            rank += 800 if showcase_ready or not noisy else 25
        if showcase_ready:
            rank += 500
        if showcase:
            rank += 150
        if cls._is_demo_showroom_project(project_name):
            rank += 200
        if not noisy:
            rank += 100
        if lifecycle_state in {"in_progress", "closing", "warranty", "done"}:
            rank += 40
        elif lifecycle_state and lifecycle_state != "draft":
            rank += 20
        return rank, context

    @staticmethod
    def _build_options_guidance(options, active_project_id=0):
        normalized_options = list(options or [])
        active_id = int(active_project_id or 0)
        if normalized_options:
            target_id = active_id if any(int(item.get("project_id") or 0) == active_id for item in normalized_options) else int(
                (normalized_options[0] or {}).get("project_id") or 0
            )
            return {
                "suggested_action": {
                    "intent": "project.dashboard.enter",
                    "reason_code": "PROJECT_OPTIONS_AVAILABLE",
                    "params": {"project_id": int(target_id or 0)},
                },
                "lifecycle_hints": {
                    "stage": "project_options_available",
                    "project_id": int(target_id or 0),
                    "primary_action_label": "进入项目管理",
                    "suggested_action_intent": "project.dashboard.enter",
                    "suggested_action_title": "进入项目管理",
                },
            }
        return {
            "suggested_action": {
                "intent": "project.initiation.enter",
                "reason_code": "PROJECT_OPTIONS_EMPTY",
                "params": {},
            },
            "lifecycle_hints": {
                "stage": "no_project_options",
                "project_id": 0,
                "primary_action_label": "创建项目",
                "suggested_action_intent": "project.initiation.enter",
                "suggested_action_title": "创建项目",
            },
        }

    @staticmethod
    def _build_diagnostics_summary(*, resolution_path="", available=False, option_count=0):
        normalized_path = str(resolution_path or "").strip().lower()
        if int(option_count or 0) > 0:
            return {
                "status": "options_available",
                "message": "已提供可切换项目列表，可直接进入项目管理。",
                "resolution_path": normalized_path or "options_ranked",
                "option_count": int(option_count or 0),
                "available": bool(available),
            }
        if bool(available):
            return {
                "status": "context_ready",
                "message": "已解析到当前项目，可直接进入项目管理。",
                "resolution_path": normalized_path or "context_resolved",
                "option_count": 0,
                "available": True,
            }
        return {
            "status": "context_missing",
            "message": "当前未解析到可用项目，建议先创建项目。",
            "resolution_path": normalized_path or "context_missing",
            "option_count": 0,
            "available": False,
        }

    def list_options(self, active_project_id=0, limit=12):
        Project = self.env["project.project"]
        domain = self._dashboard_service._project_domain_for_user()
        try:
            records = Project.search(domain or [], order="write_date desc,id desc", limit=max(int(limit or 12) * 6, 24))
        except Exception:
            records = Project.search([], order="write_date desc,id desc", limit=max(int(limit or 12) * 6, 24))
        ranked_rows = []
        for project in records:
            rank, context = self._project_rank(project, active_project_id=active_project_id)
            if rank <= 0:
                continue
            ranked_rows.append((rank, project.id, context))
        ranked_rows.sort(key=lambda item: (-int(item[0]), -int(item[1])))
        options = []
        seen_project_ids = set()
        for _rank, _project_id, context in ranked_rows:
            project_id = int(context.get("project_id") or 0)
            if project_id <= 0 or project_id in seen_project_ids:
                continue
            seen_project_ids.add(project_id)
            options.append(
                {
                    "project_id": project_id,
                    "project_name": str(context.get("project_name") or ""),
                    "stage_label": str(context.get("stage_label") or ""),
                    "milestone_label": str(context.get("milestone_label") or ""),
                    "status": str(context.get("status") or ""),
                    "active": project_id == int(active_project_id or 0),
                    "project_context": context,
                }
            )
            if len(options) >= int(limit or 12):
                break
        guidance = self._build_options_guidance(options, active_project_id=active_project_id)
        diagnostics_summary = self._build_diagnostics_summary(
            resolution_path="options_ranked",
            available=bool(options),
            option_count=len(options),
        )
        return {
            "options": options,
            "active_project_id": int(active_project_id or 0),
            "suggested_action": dict(guidance.get("suggested_action") or {}),
            "lifecycle_hints": dict(guidance.get("lifecycle_hints") or {}),
            "diagnostics_summary": dict(diagnostics_summary or {}),
        }
