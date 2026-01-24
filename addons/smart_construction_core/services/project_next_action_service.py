# -*- coding: utf-8 -*-
import logging

from odoo import api, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class ProjectNextActionService(models.AbstractModel):
    _name = "sc.project.next_action.service"
    _description = "Project Next Action Rule Service"

    @api.model
    def get_next_actions(self, project, limit=3):
        project.ensure_one()
        stats = self.env["sc.project.overview.service"].get_overview([project.id]).get(project.id, {})
        rules = self.env["sc.project.next_action.rule"].search(
            [
                ("active", "=", True),
                ("lifecycle_state", "=", project.lifecycle_state),
            ],
            order="sequence, id",
        )
        actions = []
        seen = set()
        for rule in rules:
            if rule.condition_expr:
                try:
                    ok = bool(
                        safe_eval(
                            rule.condition_expr,
                            {
                                "p": project,
                                "s": stats,
                                "u": self.env.user,
                            },
                        )
                    )
                except Exception as exc:
                    _logger.warning(
                        "[sc_next_action] rule=%s eval failed: %s",
                        rule.id,
                        exc,
                    )
                    ok = False
            else:
                ok = True
            if not ok:
                continue

            key = (rule.action_type, rule.action_ref, rule.name)
            if key in seen:
                continue
            seen.add(key)

            item = {
                "name": rule.name,
                "action_type": rule.action_type,
                "action_ref": rule.action_ref,
                "hint": self._format_hint(rule.hint_template, stats),
            }
            actions.append(item)
            if limit and len(actions) >= limit:
                break
        return actions

    def _format_hint(self, template, stats):
        if not template:
            return ""
        data = {
            "contract_count": stats.get("contract", {}).get("count", 0),
            "cost_count": stats.get("cost", {}).get("count", 0),
            "payment_count": stats.get("payment", {}).get("count", 0),
            "payment_pending": stats.get("payment", {}).get("pending", 0),
            "task_count": stats.get("task", {}).get("count", 0),
            "task_in_progress": stats.get("task", {}).get("in_progress", 0),
        }
        try:
            return template.format(**data)
        except Exception:
            return template
