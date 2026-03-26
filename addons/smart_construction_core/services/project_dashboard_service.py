# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields

from odoo.addons.smart_construction_core.services.cost_tracking_native_adapter import CostTrackingNativeAdapter
from odoo.addons.smart_construction_core.services.evidence_chain_service import EvidenceChainService
from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter
from odoo.addons.smart_construction_core.services.project_decision_engine_service import ProjectDecisionEngineService
from odoo.addons.smart_construction_core.services.project_metrics_explain_service import ProjectMetricsExplainService
from odoo.addons.smart_construction_core.services.project_state_explain_service import ProjectStateExplainService
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)

from .project_dashboard_builders import BUILDERS


class ProjectDashboardService:
    """Provide business-truth-backed dashboard data for orchestration carriers."""

    ENTRY_BLOCKS = (
        ("progress", "项目进度", "deferred"),
        ("risks", "风险提醒", "deferred"),
        ("next_actions", "下一步动作", "deferred"),
    )
    RUNTIME_BLOCK_MAP = {
        "progress": "block.project.progress",
        "risks": "block.project.risk",
        "risk": "block.project.risk",
        "next_actions": "block.project.next_actions",
    }

    def __init__(self, env):
        self.env = env
        self._cost_adapter = CostTrackingNativeAdapter(env)
        self._evidence_chain_service = EvidenceChainService(env)
        self._payment_adapter = PaymentSliceNativeAdapter(env)
        self._decision_engine = ProjectDecisionEngineService(env)
        self._state_explain_service = ProjectStateExplainService(env)
        self._metrics_explain_service = ProjectMetricsExplainService(env)
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

    def _resolve_project(self, project_id):
        project, _diag = self.resolve_project_with_diagnostics(project_id)
        return project

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
        try:
            rows = Project.search_read(
                [("active", "=", True)],
                fields=["id", "name", "write_date"],
                limit=1,
                order="write_date desc,id desc",
            )
            diagnostics["candidate_counts"]["active_search_read"] = int(len(rows or []))
            if rows and rows[0].get("id"):
                record = Project.browse(int(rows[0]["id"])).exists()
                if record:
                    diagnostics.update(
                        {
                            "resolved_project_id": int(record.id),
                            "resolution_path": "active_search_read",
                            "reason": "matched latest active project by search_read fallback",
                        }
                    )
                    return record, diagnostics
        except Exception:
            diagnostics["candidate_counts"]["active_search_read"] = -1
            diagnostics["reason"] = "active search_read fallback failed"
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
                "partner_name": "",
                "manager_name": "",
                "stage_name": "",
                "lifecycle_state": "",
                "milestone": "",
                "state": "empty",
                "progress_percent": "0",
                "cost_total": "0",
                "payment_total": "0",
                "status": "",
                "date": str(fields.Date.today()),
            }
        progress_percent = 0.0
        try:
            task_model = self._model("project.task")
            if task_model is not None:
                total = int(task_model.search_count([("project_id", "=", int(project.id))]))
                done = int(
                    task_model.search_count(
                        [("project_id", "=", int(project.id))] + ProjectTaskStateSupport.done_domain()
                    )
                )
                if total > 0:
                    progress_percent = round((done / float(total)) * 100.0, 2)
        except Exception:
            progress_percent = 0.0
        cost_summary = self._cost_adapter.summary(project)
        payment_summary = self._payment_adapter.summary(project)
        evidence_chain = self._evidence_chain_service.build_project_chain(int(project.id), limit=20)
        evidence_summary = evidence_chain.get("summary") or {}
        return {
            "id": int(project.id),
            "name": _safe_text(_safe_field(project, "name")),
            "project_code": _safe_text(_safe_field(project, "project_code")),
            "partner_name": _safe_rel_name(project, "partner_id"),
            "manager_name": _safe_rel_name(project, "user_id"),
            "stage_name": _safe_rel_name(project, "stage_id"),
            "health_state": _safe_text(_safe_field(project, "health_state")),
            "lifecycle_state": _safe_text(_safe_field(project, "lifecycle_state")),
            "milestone": _safe_text(_safe_field(project, "sc_execution_state")),
            "state": "ready",
            "progress_percent": str(progress_percent),
            "cost_total": str(cost_summary.get("total_cost_amount") or 0.0),
            "payment_total": str(payment_summary.get("total_payment_amount") or 0.0),
            "payment_executed_total": str(payment_summary.get("executed_payment_amount") or 0.0),
            "payment_executed_record_count": str(payment_summary.get("ledger_count") or 0),
            "evidence_refs": evidence_chain.get("evidence_refs") or [],
            "evidence_summary": evidence_summary,
            "facts": {
                "cost_total": str(cost_summary.get("total_cost_amount") or 0.0),
                "payment_total": str(payment_summary.get("total_payment_amount") or 0.0),
                "payment_executed_total": str(payment_summary.get("executed_payment_amount") or 0.0),
                "evidence_count": int(evidence_summary.get("evidence_count") or 0),
                "cost_evidence_count": int(evidence_summary.get("cost_count") or 0),
                "payment_evidence_count": int(evidence_summary.get("payment_count") or 0),
                "settlement_evidence_count": int(evidence_summary.get("settlement_count") or 0),
            },
            "status": _safe_text(_safe_field(project, "health_state") or _safe_field(project, "state")),
            "date": str(fields.Date.today()),
        }

    def build_state_explain(self, project):
        state_explain = self._state_explain_service.build(project)
        if not project:
            return {
                "stage_label": state_explain.get("stage_label") or "未选择项目",
                "stage_explain": state_explain.get("stage_explain") or "当前没有可用项目，无法进入项目驾驶舱。",
                "milestone_explain": "暂无项目里程碑。",
                "status_explain": state_explain.get("status_explain") or "请先选择项目或创建项目。",
            }
        milestone = str(getattr(project, "sc_execution_state", "") or "").strip().lower()
        milestone_explain_map = {
            "ready": "当前执行准备已完成，可以进入执行推进。",
            "in_progress": "当前执行正在推进，建议优先补齐成本与付款事实。",
            "done": "当前执行动作已完成，可继续检查成本、付款与结算结果。",
        }
        return {
            "stage_label": state_explain.get("stage_label") or "未设置阶段",
            "stage_explain": state_explain.get("stage_explain") or "当前项目处于已发布主线中，请按下一步动作推进。",
            "milestone_explain": milestone_explain_map.get(milestone, "当前里程碑尚未进入显式执行状态。"),
            "status_explain": state_explain.get("status_explain") or "当前项目状态正常。",
        }

    def build_metrics_explain(self, project):
        return self._metrics_explain_service.build(self.project_payload(project))

    def build_flow_map(self, project):
        project_payload = self.project_payload(project)
        decision = self._decision_engine.decide(project)
        signals = (decision.get("facts") or {}).get("signals") or {}
        lifecycle_state = str(project_payload.get("lifecycle_state") or "").strip().lower()
        facts = decision.get("facts") or {}
        payment_count = int(facts.get("payment_count") or 0)
        cost_count = int(facts.get("cost_count") or 0)

        current_stage = "initiation"
        is_completed = bool(signals.get("settlement_completed"))
        if lifecycle_state == "draft":
            current_stage = "initiation"
        elif lifecycle_state in {"closing", "warranty", "done"}:
            current_stage = "settlement"
        elif payment_count > 0:
            current_stage = "payment"
        elif cost_count > 0:
            current_stage = "cost"
        elif lifecycle_state in {"in_progress"}:
            current_stage = "execution"
        elif signals.get("payment_exceeds_cost") or signals.get("ready_for_settlement"):
            current_stage = "settlement"

        stage_order = ["initiation", "execution", "cost", "payment", "settlement"]
        stage_labels = {
            "initiation": "立项",
            "execution": "执行",
            "cost": "成本",
            "payment": "付款",
            "settlement": "结算",
        }
        current_index = stage_order.index(current_stage)
        items = []
        for index, key in enumerate(stage_order):
            if is_completed:
                status = "done"
            else:
                status = "done" if index < current_index else "current" if index == current_index else "todo"
            items.append(
                {
                    "key": key,
                    "label": stage_labels.get(key) or key,
                    "status": status,
                }
            )
        return {
            "current_stage": current_stage,
            "items": items,
        }

    def build_completion(self, project):
        decision = self._decision_engine.decide(project)
        facts = decision.get("facts") or {}
        signals = facts.get("signals") or {}
        lifecycle_state = str(facts.get("lifecycle_state") or "").strip().lower()
        percent = 20
        next_target = "进入执行"
        if signals.get("settlement_completed"):
            percent = 100
            next_target = "项目已完成"
        elif signals.get("is_draft"):
            percent = 20
            next_target = "开始执行"
        elif lifecycle_state in {"closing", "warranty", "done"}:
            percent = 90
            next_target = "完成结算确认"
        elif signals.get("no_tasks"):
            percent = 35
            next_target = "创建任务"
        elif signals.get("no_cost"):
            percent = 50
            next_target = "完成成本录入"
        elif signals.get("no_payment"):
            percent = 70
            next_target = "完成付款记录"
        elif signals.get("ready_for_settlement") or signals.get("payment_exceeds_cost"):
            percent = 85
            next_target = "完成结算检查"
        return {
            "percent": percent,
            "next_target": next_target,
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
