# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProjectResponsibility(models.Model):
    _name = 'project.responsibility'
    _description = '项目成员'
    _order = 'project_id, role_key, id'

    project_id = fields.Many2one(
        'project.project', string='项目', required=True, index=True, ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company', string='公司', related='project_id.company_id', store=True, readonly=True
    )
    role_key = fields.Selection(
        [
            ('manager', '项目经理'),
            ('cost', '成本负责人'),
            ('finance', '财务'),
            ('cashier', '出纳'),
            ('material', '材料员'),
            ('safety', '安全员'),
            ('quality', '质检员'),
            ('document', '资料员'),
        ],
        string='角色',
        required=True,
    )
    project_role_code = fields.Selection(
        related='role_key',
        string='项目内角色',
        readonly=False,
        store=True,
    )
    user_id = fields.Many2one('res.users', string='责任人', required=True, index=True)
    department_id = fields.Many2one(
        'hr.department', string='项目部门', domain="[('company_id', '=', company_id)]"
    )
    post_id = fields.Many2one(
        'sc.enterprise.post', string='项目岗位', domain="[('company_id', '=', company_id)]"
    )
    is_primary = fields.Boolean('主责', default=False)
    active = fields.Boolean('有效', default=True)
    date_start = fields.Date('生效日期')
    date_end = fields.Date('失效日期')
    note = fields.Text('说明/授权范围')

    _sql_constraints = [
        (
            'project_role_unique',
            'unique(project_id, role_key, user_id)',
            '同一项目下同一角色不可重复指派到同一人员。',
        )
    ]

    @api.constrains('date_start', 'date_end')
    def _check_member_date_range(self):
        for member in self:
            if member.date_start and member.date_end and member.date_start > member.date_end:
                raise ValidationError('成员生效日期不能晚于失效日期。')

    @api.onchange('user_id')
    def _onchange_user_fill_org(self):
        for member in self:
            if not member.user_id:
                continue
            if not member.department_id and hasattr(member.user_id, 'sc_department_id'):
                member.department_id = member.user_id.sc_department_id
            if not member.post_id and hasattr(member.user_id, 'sc_post_id'):
                member.post_id = member.user_id.sc_post_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.mapped('project_id')._sync_project_member_visibility()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.mapped('project_id')._sync_project_member_visibility()
        return res

    def unlink(self):
        projects = self.mapped('project_id')
        res = super().unlink()
        projects._sync_project_member_visibility()
        return res
