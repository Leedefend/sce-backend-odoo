# -*- coding: utf-8 -*-

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = "project.project"

    @api.model
    def sc_demo_user_acceptance_cleanup(self):
        """Remove demo projects that should not appear in user acceptance."""
        projects = self.sudo().with_context(active_test=False).search(
            [
                "|",
                ("project_code", "in", ["SC-DEY-2025-001"]),
                (
                    "name",
                    "in",
                    [
                        "德阳智能制造产教融合项目",
                        "P2-空壳对照项目（演示）",
                        "演示项目 · 城市快速路提升工程",
                    ],
                ),
            ]
        )
        if not projects:
            _logger.info("sc_demo_user_acceptance_cleanup: no target projects found")
            return True

        project_ids = projects.ids
        delete_models = [
            "payment.request",
            "construction.contract",
            "project.material.plan",
            "tender.bid",
            "sc.project.document",
            "project.cost.ledger",
            "project.cost.period",
            "project.progress.entry",
            "project.budget.cost.alloc",
            "project.budget.boq.line",
            "project.budget.line",
            "project.budget",
            "project.wbs",
            "construction.work.breakdown",
            "project.task",
        ]
        deleted = {}
        for model_name in delete_models:
            self._sc_demo_unlink_project_records(model_name, project_ids, deleted)

        for _index in range(8):
            summary = projects._project_unlink_dependency_summary(project_ids)
            model_names = {
                item.get("model")
                for blockers in summary.values()
                for item in blockers
                if item.get("model")
            }
            if not model_names:
                break
            for model_name in sorted(model_names):
                self._sc_demo_unlink_project_records(model_name, project_ids, deleted)

        deleted["project.project"] = len(projects)
        projects.unlink()
        _logger.info("sc_demo_user_acceptance_cleanup: deleted=%s", deleted)
        return True

    def _sc_demo_unlink_project_records(self, model_name, project_ids, deleted):
        if model_name not in self.env:
            return
        Model = self.env[model_name].sudo().with_context(active_test=False)
        if "project_id" not in Model._fields:
            return
        records = Model.search([("project_id", "in", project_ids)])
        if not records:
            return
        if model_name == "payment.request" and "state" in records._fields:
            records.with_context(allow_transition=True).write({"state": "cancel"})
        elif model_name == "construction.contract" and "state" in records._fields:
            records.write({"state": "cancel"})
        elif model_name == "project.material.plan" and "state" in records._fields:
            records.write({"state": "draft"})
        deleted[model_name] = deleted.get(model_name, 0) + len(records)
        records.unlink()
