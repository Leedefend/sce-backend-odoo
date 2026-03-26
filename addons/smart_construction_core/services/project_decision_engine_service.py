# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectDecisionEngineService:
    DECISION_SOURCE = "rule_engine_v1"

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _project_domain(self, model_name, project):
        model = self._model(model_name)
        if model is None:
            return []
        fields = getattr(model, "_fields", {})
        if "project_id" not in fields:
            return []
        return [("project_id", "=", int(project.id))]

    def _count(self, model_name, project):
        model = self._model(model_name)
        if model is None or not project:
            return 0
        try:
            return int(model.search_count(self._project_domain(model_name, project)))
        except Exception:
            return 0

    def _sum_first_field(self, model_name, project, field_names):
        model = self._model(model_name)
        if model is None or not project:
            return 0.0
        domain = self._project_domain(model_name, project)
        for field_name in field_names:
            if field_name not in getattr(model, "_fields", {}):
                continue
            try:
                rows = model.read_group(domain, [field_name], [])
            except Exception:
                continue
            if not rows:
                continue
            try:
                return float(rows[0].get(field_name) or 0.0)
            except Exception:
                return 0.0
        return 0.0

    def analyze(self, project):
        if not project:
            return {
                "lifecycle_state": "",
                "task_count": 0,
                "cost_count": 0,
                "payment_count": 0,
                "cost_total": 0.0,
                "payment_total": 0.0,
                "progress_percent": 0.0,
                "signals": {},
            }

        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        task_count = self._count("project.task", project)
        cost_count = self._count("account.move", project)
        payment_count = self._count("payment.request", project)
        cost_total = self._sum_first_field("account.move", project, ["amount_total_signed", "amount_total"])
        payment_total = self._sum_first_field("payment.request", project, ["amount_total", "amount"])

        done_count = 0
        try:
            task_model = self._model("project.task")
            if task_model is not None:
                done_count = int(task_model.search_count(self._project_domain("project.task", project) + [("stage_id.fold", "=", True)]))
        except Exception:
            done_count = 0
        progress_percent = round((done_count / float(task_count)) * 100.0, 2) if task_count > 0 else 0.0

        signals = {
            "is_draft": lifecycle_state == "draft",
            "no_tasks": lifecycle_state in {"in_progress", "closing", "warranty", "done"} and task_count <= 0,
            "no_cost": lifecycle_state in {"in_progress", "closing", "warranty", "done"} and cost_count <= 0,
            "no_payment": lifecycle_state in {"in_progress", "closing", "warranty", "done"} and cost_count > 0 and payment_count <= 0,
            "payment_exceeds_cost": payment_total > cost_total and payment_total > 0,
            "ready_for_settlement": cost_count > 0 and payment_count > 0,
            "settlement_blocked": lifecycle_state in {"closing", "warranty", "done"} and payment_count <= 0,
            "progress_missing": task_count <= 0 or progress_percent <= 0,
        }

        return {
            "lifecycle_state": lifecycle_state,
            "task_count": task_count,
            "cost_count": cost_count,
            "payment_count": payment_count,
            "cost_total": cost_total,
            "payment_total": payment_total,
            "progress_percent": progress_percent,
            "signals": signals,
        }

    def decide(self, project):
        facts = self.analyze(project)
        signals = facts["signals"]

        if signals["is_draft"]:
            primary_key = "start_execution"
            reason = "当前项目已完成立项，但尚未进入执行阶段。"
            rule = "draft_to_execution"
        elif signals["no_tasks"]:
            primary_key = "project_execution_enter"
            reason = "当前项目已进入执行阶段，但还没有形成任务事实。"
            rule = "execution_tasks_missing"
        elif signals["no_cost"]:
            primary_key = "cost_tracking_enter"
            reason = "当前项目已有执行动作，但尚未形成成本事实。"
            rule = "execution_cost_missing"
        elif signals["no_payment"]:
            primary_key = "payment_enter"
            reason = "当前项目已有成本事实，但尚未形成付款事实。"
            rule = "payment_missing"
        elif signals["payment_exceeds_cost"]:
            primary_key = "settlement_enter"
            reason = "当前项目付款已超过成本，建议先进入结算结果复核经营口径。"
            rule = "payment_exceeds_cost"
        elif signals["ready_for_settlement"]:
            primary_key = "settlement_enter"
            reason = "当前项目已具备成本与付款事实，建议进入结算结果检查收口条件。"
            rule = "settlement_ready"
        else:
            primary_key = "project_execution_enter"
            reason = "当前项目可以继续从执行推进进入主线。"
            rule = "execution_default"

        priority_scores = {
            "start_execution": 100 if primary_key == "start_execution" else 0,
            "project_execution_enter": 95 if primary_key == "project_execution_enter" else (80 if signals["no_tasks"] else 20),
            "cost_tracking_enter": 95 if primary_key == "cost_tracking_enter" else (70 if signals["no_cost"] else 10),
            "payment_enter": 95 if primary_key == "payment_enter" else (60 if signals["no_payment"] else 5),
            "settlement_enter": 95 if primary_key == "settlement_enter" else (50 if signals["ready_for_settlement"] else 0),
        }

        available_action_keys = {"project_execution_enter"}
        if signals["is_draft"]:
            available_action_keys.add("start_execution")
        if facts["lifecycle_state"] in {"in_progress", "closing", "warranty", "done"}:
            available_action_keys.add("cost_tracking_enter")
        if facts["cost_count"] > 0 and facts["lifecycle_state"] in {"in_progress", "closing", "warranty", "done"}:
            available_action_keys.add("payment_enter")
        if signals["ready_for_settlement"] or signals["payment_exceeds_cost"]:
            available_action_keys.add("settlement_enter")

        return {
            "primary_action_key": primary_key,
            "reason": reason,
            "decision_rule": rule,
            "decision_source": self.DECISION_SOURCE,
            "priority_scores": priority_scores,
            "available_action_keys": available_action_keys,
            "facts": facts,
        }
