# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def action_portal_demo_ping(self):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Portal 执行",
                "message": "演示动作已执行。",
                "type": "success",
                "sticky": False,
            },
        }
