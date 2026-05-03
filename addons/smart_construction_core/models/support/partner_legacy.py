# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sc_supplier_type = fields.Selection(
        [
            ("material", "材料供应商"),
            ("labor", "劳务供应商"),
            ("subcontract", "分包单位"),
            ("service", "服务供应商"),
            ("equipment", "设备供应商"),
            ("other", "其他"),
        ],
        string="供应商类型",
        index=True,
    )
    sc_account_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行")
    sc_bank_account = fields.Char(string="账号")
    sc_region = fields.Char(string="所属地区", index=True)
    sc_supplier_note = fields.Text(string="供应商备注")
    sc_attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_res_partner_supplier_attachment_rel",
        "partner_id",
        "attachment_id",
        string="供应商附件",
    )

    # Legacy identity carrier fields for idempotent migration replay.
    legacy_partner_id = fields.Char(index=True)
    legacy_partner_source = fields.Char(index=True)
    legacy_partner_name = fields.Char()
    legacy_credit_code = fields.Char()
    legacy_tax_no = fields.Char(index=True)
    legacy_deleted_flag = fields.Char()
    legacy_source_evidence = fields.Char()
