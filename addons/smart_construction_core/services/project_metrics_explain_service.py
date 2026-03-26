# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectMetricsExplainService:
    def __init__(self, env):
        self.env = env

    def build(self, project_payload):
        progress = self._number(project_payload.get("progress_percent"))
        cost_total = self._number(project_payload.get("cost_total"))
        payment_total = self._number(project_payload.get("payment_total"))

        progress_status = "normal" if progress > 0 else "warning"
        cost_status = "normal" if cost_total > 0 else "warning"
        payment_status = "warning" if payment_total > cost_total and payment_total > 0 else "normal"

        return [
            {
                "key": "progress",
                "status": progress_status,
                "explain": "执行进度已形成事实。" if progress_status == "normal" else "尚未形成可识别的执行进度。",
            },
            {
                "key": "cost",
                "status": cost_status,
                "explain": "成本处于已记录状态。" if cost_status == "normal" else "尚未录入成本，经营基线仍不完整。",
            },
            {
                "key": "payment",
                "status": payment_status,
                "explain": "付款与成本关系正常。" if payment_status == "normal" else "付款已超过成本，请检查资金事实是否异常。",
            },
        ]

    @staticmethod
    def _number(value):
        try:
            return float(value or 0.0)
        except Exception:
            return 0.0
