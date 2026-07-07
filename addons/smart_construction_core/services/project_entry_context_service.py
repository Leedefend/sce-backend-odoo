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

    def _company_options(self, active_company_id=0):
        allowed = self.env.user.company_ids
        rows = []
        active_id = int(active_company_id or self.env.company.id or 0)
        for company in allowed.sorted(key=lambda item: item.id):
            rows.append(
                {
                    "company_id": int(company.id),
                    "company_name": str(company.display_name or company.name or "").strip(),
                    "active": int(company.id) == active_id,
                }
            )
        return rows

    def _allowed_company_id(self, company_id=0):
        selected = int(company_id or 0)
        allowed_ids = set(self.env.user.company_ids.ids)
        if selected and selected in allowed_ids:
            return selected
        current = int(self.env.company.id or 0)
        return current if current in allowed_ids else 0

    @staticmethod
    def _operation_options(project_context=None, active_operation_strategy=""):
        context = project_context if isinstance(project_context, dict) else {}
        project_strategy = str(context.get("operation_strategy") or "").strip()
        active = str(active_operation_strategy or project_strategy or "").strip()
        base = [
            {"operation_strategy": "direct", "operation_strategy_label": "公司直营"},
            {"operation_strategy": "joint", "operation_strategy_label": "联营项目"},
        ]
        rows = []
        for item in base:
            strategy = item["operation_strategy"]
            disabled = bool(project_strategy and strategy != project_strategy)
            rows.append(
                {
                    **item,
                    "active": strategy == active,
                    "disabled": disabled,
                    "disabled_reason": "经营方式必须与当前项目一致" if disabled else "",
                }
            )
        return rows

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

    def resolve(self, project_id=0, company_id=0, operation_strategy=""):
        project, diagnostics = self._dashboard_service.resolve_project_with_diagnostics(project_id)
        allowed_company_id = self._allowed_company_id(company_id)
        if project and allowed_company_id and project.company_id.id != allowed_company_id:
            project = self.env["project.project"].browse([])
            diagnostics = {**(diagnostics or {}), "resolution_path": "company_scope_denied"}
        operation_strategy = str(operation_strategy or "").strip()
        if project and operation_strategy in {"direct", "joint"} and project.operation_strategy != operation_strategy:
            project = self.env["project.project"].browse([])
            diagnostics = {**(diagnostics or {}), "resolution_path": "operation_scope_denied"}
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
            "company_options": self._company_options(active_company_id=allowed_company_id or project_context.get("company_id") or 0),
            "operation_options": self._operation_options(project_context, operation_strategy),
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
    def _is_showroom_project(cls, name):
        normalized = str(name or "").strip()
        return normalized.startswith("展厅-")

    @classmethod
    def _project_rank(cls, project, active_project_id=0):
        context = build_project_context(project)
        project_id = int(context.get("project_id") or 0)
        project_name = str(context.get("project_name") or "")
        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        showcase = bool(getattr(project, "sc_project_showcase", False))
        showcase_ready = bool(getattr(project, "sc_project_showcase_ready", False))
        noisy = cls._is_noisy_project_name(project_name)
        rank = 0
        if project_id and project_id == int(active_project_id or 0):
            rank += 800 if showcase_ready or not noisy else 25
        if showcase_ready:
            rank += 500
        if showcase:
            rank += 150
        if cls._is_showroom_project(project_name):
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

    @staticmethod
    def _safe_search(Project, domain, *, order="", limit=0):
        try:
            return Project.search(domain or [], order=order, limit=limit)
        except Exception:
            return Project.browse([])

    @staticmethod
    def _append_unique_records(target, records, seen_ids):
        for record in records:
            project_id = int(getattr(record, "id", 0) or 0)
            if project_id <= 0 or project_id in seen_ids:
                continue
            seen_ids.add(project_id)
            target += record
        return target

    @staticmethod
    def _showroom_candidate_domain():
        return [
            "|",
            ("name", "like", "展厅-%"),
            "|",
            ("sc_project_showcase", "=", True),
            ("sc_project_showcase_ready", "=", True),
        ]

    def _option_candidate_records(self, Project, active_project_id=0, limit=12, company_id=0, operation_strategy=""):
        fetch_limit = max(int(limit or 12) * 6, 24)
        candidates = Project.browse([])
        seen_ids = set()
        scope_domain = []
        if int(company_id or 0) > 0:
            scope_domain.append(("company_id", "=", int(company_id)))
        operation_strategy = str(operation_strategy or "").strip()
        if operation_strategy in {"direct", "joint"}:
            scope_domain.append(("operation_strategy", "=", operation_strategy))

        if int(active_project_id or 0) > 0:
            active_record = self._safe_search(
                Project,
                scope_domain + [("id", "=", int(active_project_id or 0))],
                limit=1,
            )
            candidates = self._append_unique_records(candidates, active_record, seen_ids)

        user_domain = self._dashboard_service._project_domain_for_user()
        user_records = self._safe_search(
            Project,
            scope_domain + user_domain,
            order="write_date desc,id desc",
            limit=fetch_limit,
        )
        candidates = self._append_unique_records(candidates, user_records, seen_ids)

        showroom_records = self._safe_search(
            Project,
            scope_domain + self._showroom_candidate_domain(),
            order="write_date desc,id desc",
            limit=max(int(limit or 12), 6),
        )
        candidates = self._append_unique_records(candidates, showroom_records, seen_ids)

        if len(candidates) >= min(fetch_limit, 2):
            return candidates

        fallback_records = self._safe_search(
            Project,
            scope_domain,
            order="write_date desc,id desc",
            limit=fetch_limit,
        )
        candidates = self._append_unique_records(candidates, fallback_records, seen_ids)
        return candidates

    def list_options(self, active_project_id=0, limit=12, company_id=0, operation_strategy=""):
        Project = self.env["project.project"]
        allowed_company_id = self._allowed_company_id(company_id)
        operation_strategy = str(operation_strategy or "").strip()
        if operation_strategy not in {"direct", "joint"}:
            operation_strategy = ""
        records = self._option_candidate_records(
            Project,
            active_project_id=active_project_id,
            limit=limit,
            company_id=allowed_company_id,
            operation_strategy=operation_strategy,
        )
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
                    "operation_strategy": str(context.get("operation_strategy") or ""),
                    "operation_strategy_label": str(context.get("operation_strategy_label") or ""),
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
            "company_options": self._company_options(active_company_id=allowed_company_id),
            "operation_options": self._operation_options(
                options[0].get("project_context") if options else {},
                operation_strategy or (options[0].get("operation_strategy") if options else ""),
            ),
            "suggested_action": dict(guidance.get("suggested_action") or {}),
            "lifecycle_hints": dict(guidance.get("lifecycle_hints") or {}),
            "diagnostics_summary": dict(diagnostics_summary or {}),
        }
