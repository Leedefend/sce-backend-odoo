# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    cost_actual_pct = fields.Float(
        string="实际/预算%",
        compute="_compute_dashboard_metrics",
        store=True,
    )
    cost_commit_pct = fields.Float(
        string="承诺/预算%",
        compute="_compute_dashboard_metrics",
        store=True,
    )
    schedule_delta = fields.Float(
        string="进度偏差",
        compute="_compute_dashboard_metrics",
        store=True,
        help="实际完成率 - 计划完成率，负数表示落后。",
    )
    health_state = fields.Selection(
        [
            ("good", "健康"),
            ("warn", "预警"),
            ("risk", "风险"),
        ],
        string="健康度",
        compute="_compute_dashboard_metrics",
        store=True,
        index=True,
    )

    dashboard_alert_1 = fields.Char(string="驾驶舱提示1", compute="_compute_dashboard_alerts", store=False)
    dashboard_alert_2 = fields.Char(string="驾驶舱提示2", compute="_compute_dashboard_alerts", store=False)
    dashboard_alert_3 = fields.Char(string="驾驶舱提示3", compute="_compute_dashboard_alerts", store=False)

    @api.depends("budget_total", "cost_actual", "cost_committed", "plan_percent", "actual_percent")
    def _compute_dashboard_metrics(self):
        for rec in self:
            budget = rec.budget_total or 0.0
            actual = rec.cost_actual or 0.0
            commit = rec.cost_committed or 0.0

            rec.cost_actual_pct = (actual / budget * 100.0) if budget else 0.0
            rec.cost_commit_pct = (commit / budget * 100.0) if budget else 0.0

            plan = rec.plan_percent or 0.0
            act = rec.actual_percent or 0.0
            rec.schedule_delta = act - plan  # 负数 = 落后

            risk_by_cost = bool(budget) and (actual > budget or commit > budget)
            warn_by_cost = bool(budget) and (actual >= budget * 0.85 or commit >= budget * 0.90)
            risk_by_schedule = rec.schedule_delta <= -15.0
            warn_by_schedule = rec.schedule_delta <= -8.0

            if risk_by_cost or risk_by_schedule:
                rec.health_state = "risk"
            elif warn_by_cost or warn_by_schedule:
                rec.health_state = "warn"
            else:
                rec.health_state = "good"

    def _compute_dashboard_alerts(self):
        for rec in self:
            alerts = []

            budget = rec.budget_total or 0.0
            if budget <= 0:
                alerts.append("未设置目标成本：无法计算成本占用率。")
            else:
                if (rec.cost_actual or 0.0) > budget:
                    alerts.append("成本已超预算：请立即冻结新增承诺并复核费用口径。")
                elif rec.cost_actual_pct >= 85:
                    alerts.append("实际成本逼近预算（≥85%）：建议触发超标审批或压降措施。")
                elif rec.cost_commit_pct >= 90:
                    alerts.append("承诺成本占比过高（≥90%）：请核查未到票/未到货与合同变更。")

            if rec.schedule_delta <= -15:
                alerts.append("进度严重落后（≥15%）：建议重排关键路径并提交纠偏计划。")
            elif rec.schedule_delta <= -8:
                alerts.append("进度落后（≥8%）：建议检查资源投入与外协节点。")

            rec.dashboard_alert_1 = alerts[0] if len(alerts) > 0 else False
            rec.dashboard_alert_2 = alerts[1] if len(alerts) > 1 else False
            rec.dashboard_alert_3 = alerts[2] if len(alerts) > 2 else False
