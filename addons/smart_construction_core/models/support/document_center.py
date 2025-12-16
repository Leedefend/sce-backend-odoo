# -*- coding: utf-8 -*-
from odoo import models, fields


class ScProjectDocument(models.Model):
    """F. 工程资料中心"""
    _name = 'sc.project.document'
    _description = 'Project Engineering Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id, doc_type_id, create_date desc'

    name = fields.Char('资料名称', required=True, tracking=True)

    project_id = fields.Many2one(
        'project.project', string='所属项目',
        required=True, index=True, tracking=True
    )
    wbs_id = fields.Many2one(
        'construction.work.breakdown', string='工程结构(WBS)',
        index=True
    )
    task_id = fields.Many2one(
        'project.task', string='关联任务/工序',
        index=True
    )
    contract_id = fields.Many2one(
        'account.analytic.account',
        string='关联合同',
        index=True
    )

    # 资料分类：全走 sc.dictionary
    doc_type_id = fields.Many2one(
        'sc.dictionary', string='资料大类',
        domain=[('type', '=', 'doc_type')],
        required=True, index=True, tracking=True
    )
    doc_subtype_id = fields.Many2one(
        'sc.dictionary', string='资料细类',
        domain=[('type', '=', 'doc_subtype')],
        tracking=True
    )

    date_doc = fields.Date('资料日期')
    version = fields.Char('版本号/版次')

    is_mandatory = fields.Boolean(
        '是否必备资料',
        help='若勾选，在结算/验收/付款时可作为前置校验依据。'
    )

    responsible_id = fields.Many2one(
        'res.users', string='责任人',
        default=lambda self: self.env.user, index=True
    )
    company_id = fields.Many2one(
        'res.company', string='公司',
        default=lambda self: self.env.company,
        readonly=True
    )

    note = fields.Text('说明/备注')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'sc_project_document_attachment_rel',
        'document_id', 'attachment_id',
        string='附件'
    )

    state = fields.Selection([
        ('draft', '草稿'),
        ('review', '审核中'),
        ('done', '已归档'),
        ('cancel', '作废'),
    ], string='状态', default='draft', tracking=True)

    attachment_count = fields.Integer(
        '附件数量', compute='_compute_attachment_count'
    )

    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    # 状态流转
    def action_submit(self):
        for rec in self:
            if rec.state == 'draft':
                rec.project_id._ensure_operation_allowed(operation_label="提交资料", blocked_states=("paused", "closed"))
                rec.state = 'review'

    def action_approve(self):
        for rec in self:
            if rec.state in ('draft', 'review'):
                rec.project_id._ensure_operation_allowed(operation_label="归档资料", blocked_states=("paused", "closed"))
                rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
