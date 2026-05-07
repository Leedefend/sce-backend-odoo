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
    sc_registered_capital = fields.Char(string="注册资本")
    sc_business_scope = fields.Text(string="经营范围")
    sc_default_tax_rate = fields.Float(string="默认税率%", digits=(16, 4))
    sc_default_tax_rate_text = fields.Char(string="历史税率文本")
    sc_supplier_note = fields.Text(string="供应商备注")
    sc_attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_res_partner_supplier_attachment_rel",
        "partner_id",
        "attachment_id",
        string="供应商附件",
    )

    # Legacy identity carrier fields for idempotent migration replay.
    legacy_partner_id = fields.Char(string="历史供应商编号", index=True)
    legacy_partner_source = fields.Char(string="历史来源", index=True)
    legacy_partner_name = fields.Char(string="历史供应商名称")
    legacy_credit_code = fields.Char(string="历史统一信用代码")
    legacy_tax_no = fields.Char(string="历史税号", index=True)
    legacy_deleted_flag = fields.Char(string="历史删除标识")
    legacy_source_evidence = fields.Char(string="历史来源证据")


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    sc_legacy_external_id = fields.Char(string="历史账户外部键", index=True, copy=False)
    sc_legacy_partner_id = fields.Char(string="历史往来单位编号", index=True)
    sc_legacy_partner_source = fields.Char(string="历史往来单位来源", index=True)
    sc_legacy_partner_name = fields.Char(string="历史往来单位名称")
    sc_account_holder_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行", index=True)
    sc_source_evidence = fields.Char(string="历史来源证据")
    sc_import_batch = fields.Char(string="导入批次", index=True)

    _sql_constraints = [
        (
            "sc_legacy_external_id_unique",
            "unique(sc_legacy_external_id)",
            "历史账户外部键必须唯一。",
        ),
    ]
