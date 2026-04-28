# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScLegacyAccountMaster(models.Model):
    _name = "sc.legacy.account.master"
    _description = "历史账户主数据"
    _order = "account_type, name"
    _rec_name = "display_name"

    legacy_account_id = fields.Char(string="账户原编号", required=True, index=True)
    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    name = fields.Char(string="账户名称", required=True, index=True)
    account_no = fields.Char(string="账号", index=True)
    account_type = fields.Char(string="账户类型", index=True)
    opening_balance = fields.Float(string="期初余额")
    bank_name = fields.Char(string="开户行", index=True)
    sort_no = fields.Char(string="排序号")
    is_default = fields.Boolean(string="默认账户")
    fixed_account = fields.Boolean(string="固定账户")
    legacy_state = fields.Char(string="旧账户状态", index=True)
    source_table = fields.Char(string="来源表", default="C_Base_ZHSZ", required=True, index=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)
    display_name = fields.Char(string="显示名称", compute="_compute_display_name", store=True, index=True)

    _sql_constraints = [
        ("legacy_account_id_unique", "unique(legacy_account_id)", "Legacy account id must be unique."),
    ]

    @api.depends("name", "account_no", "legacy_account_id")
    def _compute_display_name(self):
        for record in self:
            parts = [record.name or record.legacy_account_id]
            if record.account_no:
                parts.append(record.account_no)
            record.display_name = " ".join(part for part in parts if part)
