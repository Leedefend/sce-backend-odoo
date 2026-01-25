# -*- coding: utf-8 -*-
from collections import defaultdict
import logging
import time

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProjectOverviewService(models.AbstractModel):
    _name = "sc.project.overview.service"
    _description = "Project Overview Aggregation Service"

    @api.model
    def get_overview(self, project_ids):
        ids = [pid for pid in (project_ids or []) if pid]
        data = {pid: {
            "contract": {"count": 0},
            "cost": {"count": 0},
            "payment": {"count": 0, "pending": 0},
            "task": {"count": 0, "in_progress": 0},
        } for pid in ids}
        if not ids:
            return data

        env = self.env
        can_contract = env["project.project"]._can_read_model("construction.contract")
        can_cost = env["project.project"]._can_read_model("project.cost.ledger")
        can_payment = ("payment.request" in env) and env["project.project"]._can_read_model("payment.request")
        can_task = env["project.project"]._can_read_model("project.task")

        start_ts = time.time()
        calls = 0

        if can_contract:
            calls += 1
            rows = env["construction.contract"].read_group(
                [("project_id", "in", ids)],
                ["project_id"],
                ["project_id"],
            )
            for rec in rows:
                project_id = rec["project_id"][0]
                data[project_id]["contract"]["count"] = rec.get("__count", 0)

        if can_cost:
            calls += 1
            rows = env["project.cost.ledger"].read_group(
                [("project_id", "in", ids)],
                ["project_id"],
                ["project_id"],
            )
            for rec in rows:
                project_id = rec["project_id"][0]
                data[project_id]["cost"]["count"] = rec.get("__count", 0)

        if can_payment:
            calls += 1
            rows = env["payment.request"].read_group(
                [("project_id", "in", ids)],
                ["project_id"],
                ["project_id"],
            )
            for rec in rows:
                project_id = rec["project_id"][0]
                data[project_id]["payment"]["count"] = rec.get("__count", 0)
            calls += 1
            pending_rows = env["payment.request"].read_group(
                [
                    ("project_id", "in", ids),
                    ("state", "in", ["submit", "approve", "approved"]),
                ],
                ["project_id"],
                ["project_id"],
            )
            for rec in pending_rows:
                project_id = rec["project_id"][0]
                data[project_id]["payment"]["pending"] = rec.get("__count", 0)

        if can_task:
            calls += 1
            rows = env["project.task"].read_group(
                [("project_id", "in", ids)],
                ["project_id"],
                ["project_id"],
            )
            for rec in rows:
                project_id = rec["project_id"][0]
                data[project_id]["task"]["count"] = rec.get("__count", 0)
            calls += 1
            progress_rows = env["project.task"].read_group(
                [
                    ("project_id", "in", ids),
                    ("state", "=", "in_progress"),
                ],
                ["project_id"],
                ["project_id"],
            )
            for rec in progress_rows:
                project_id = rec["project_id"][0]
                data[project_id]["task"]["in_progress"] = rec.get("__count", 0)

        if env.context.get("sc_overview_debug"):
            elapsed = time.time() - start_ts
            _logger.info(
                "[sc_overview] project_ids=%s read_groups=%s elapsed=%.3fs",
                len(ids), calls, elapsed,
            )

        return data
