# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectChangeOrder(models.Model):
    _name = "project.change.order"
    _description = "工程变更/签证"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(
        "变更单号",
        copy=False,
        default="新建",
        tracking=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        tracking=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="关联合同",
        required=True,
        index=True,
        tracking=True,
        domain="[('project_id', '=', project_id)]",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="相对方",
        related="contract_id.partner_id",
        store=True,
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="contract_id.company_id",
        store=True,
        readonly=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="contract_id.currency_id",
        store=True,
        readonly=True,
        tracking=True,
    )
    change_type = fields.Selection(
        [
            ("design", "设计变更"),
            ("site", "现场签证"),
            ("claim", "索赔"),
            ("discount", "减项"),
            ("other", "其他"),
        ],
        string="变更类型",
        required=True,
        default="design",
        tracking=True,
    )
    change_category = fields.Selection(
        [
            ("increase", "增项"), 
            ("decrease", "减项"), 
            ("none", "仅记录不影响金额"),
        ],
        string="金额方向",
        required=True,
        default="increase",
        tracking=True,
    )
    reason = fields.Char('变更原因', required=True, tracking=True)
    description = fields.Text('变更说明', tracking=True)
    date_request = fields.Date('提出日期', default=fields.Date.context_today, tracking=True)
    date_approved = fields.Date('批准日期', tracking=True)
    amount_subtotal = fields.Monetary('变更金额小计', currency_field='currency_id', compute='_compute_amounts', store=True)
    tax_rate = fields.Float('税率(%)', tracking=True)
    amount_total = fields.Monetary('变更含税金额', currency_field='currency_id', compute='_compute_amounts', store=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("rejected", "已驳回"),
            ("closed","已关闭")
        ],
        string="状态",
        default="draft",
        tracking=True,
    )
    note = fields.Text('备注', tracking=True)
    line_ids = fields.One2many(
        "project.change.order.line",
        "change_id",
        string="变更明细",
        copy=True,
    )

    @api.depends('line_ids.amount','line_ids')
    def _compute_amounts(self):
        """
            汇总子表的含税金额
        """
        for record in self:
            record.amount_subtotal = sum(record.line_ids.mapped('amount'))
            # amount_total 目前同等于amount_subtotal 后续接入tax_rate税率参与详细计算
            record.amount_total = sum(record.line_ids.mapped('amount'))


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("project.change.order") or "新建"
                )
        return super().create(vals_list)

    def action_submit(self):
        """
         提交单据 并且检验至少一条变更明细，
        """
        if not self.line_ids:
            raise ValidationError(_("请先添加至少一条变更明细。"))
        self.write({"state": "submit"})
        return True

    def action_approve(self):
        """
            审批单据 写入审批时间
        """
        if self.state != "submit":
            raise ValidationError(_("请先提交单据。"))
        self.write(
                {
                    "state": "approved", 
                    "date_approved":fields.Date.context_today(self)
                }
            )
        self._apply_to_contract()
        return True

    def action_reject(self):
        """
            驳回单据
        """
        if self.state != "submit":
            raise ValidationError(_("请先提交单据。"))
        self.write({"state": "rejected"})
        return True

    def action_close(self):
        """
            关闭单据
        """
        if self.state not in ("approved", "rejected"):
            raise ValidationError(_("请先批准或驳回单据。"))
        self.write({"state": "closed"})
        return True

    def _apply_to_contract(self):
        """
            后续补充业务逻辑
        """
        pass


class ProjectChangeOrderLine(models.Model):
    _name = "project.change.order.line"
    _description = "工程变更明细"
    _order = "id desc"

    change_id = fields.Many2one(
        "project.change.order",
        string="变更单",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char('内容', required=True, tracking=True)
    wbs_code = fields.Char('WBS/分项编码')
    cost_item_id = fields.Many2one('project.dictionary', '成本项', domain=[('type', '=', 'cost_item')], tracking=True)
    quantity = fields.Float('数量', default=1.0, tracking=True)
    uom_id = fields.Many2one('uom.uom', '单位', tracking=True)
    price_unit = fields.Monetary('含税单价', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="change_id.currency_id",
        store=True,
        readonly=True,
    )
    amount = fields.Monetary('含税金额', currency_field='currency_id', compute='_compute_amount', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        """
            计算含税金额
        """
        for record in self:
            record.amount = record.quantity * record.price_unit