# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    project_id = fields.Many2one(
        'project.project',
        string='项目',
        related='move_id.project_id',
        store=True,
        index=True,
        help='项目维度，用于项目驾驶舱汇总发票收入/成本。'
    )
