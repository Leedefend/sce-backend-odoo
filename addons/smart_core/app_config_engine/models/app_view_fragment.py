# -*- coding: utf-8 -*-
# models/app_view_fragment.py
from odoo import models, fields, api
from .contract_mixin import ContractSchemaMixin

class AppViewFragment(models.Model, ContractSchemaMixin):
    _name = 'app.view.fragment'
    _description = 'Reusable View Fragment (Contract Blocks)'
    _order = 'category, priority desc, id desc'

    name = fields.Char(required=True)
    category = fields.Selection([
        ('toolbar', 'Toolbar Block'),
        ('form_group', 'Form Group'),
        ('tree_columns', 'Tree Columns'),
        ('kanban_card', 'Kanban Card'),
        ('search', 'Search Block'),
        ('statusbar', 'Statusbar'),
        ('custom', 'Custom'),
    ], default='custom', index=True)
    view_type = fields.Selection([
        ('form','Form'),('tree','Tree'),('kanban','Kanban'),
        ('pivot','Pivot'),('graph','Graph'),('calendar','Calendar'),
        ('gantt','Gantt'),('search','Search'),
    ], required=True, index=True)

    # 可复用契约片段（与视图契约 JSON 结构一致，但仅包含子集）
    contract = fields.Json(required=True)
    priority = fields.Integer(default=10)
    groups_id = fields.Many2many('res.groups', string='Visible to Groups')
    is_active = fields.Boolean(default=True)

    def materialize(self, view_type):
        """返回白名单清洗后的片段（仅保留该视图可用键）"""
        self.ensure_one()
        return self.sanitize_contract(view_type, self.contract or {})
