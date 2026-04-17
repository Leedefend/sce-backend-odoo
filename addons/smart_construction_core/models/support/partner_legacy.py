# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    legacy_partner_id = fields.Char(
        string="旧系统往来单位ID",
        index=True,
        copy=False,
        help="旧系统 T_Base_CooperatCompany.Id / T_Base_SupplierInfo.ID，用于迁移幂等、精确回滚和后续合同相对方关联。",
    )
    legacy_partner_source = fields.Selection(
        [
            ("cooperat_company", "合作单位"),
            ("supplier", "供应商"),
            ("company_supplier", "合作单位+供应商"),
            ("contract_counterparty", "合同补充相对方"),
            ("receipt_counterparty", "收款补充相对方"),
        ],
        string="旧系统往来单位来源",
        index=True,
        copy=False,
        help="旧系统 partner 来源表及补充业务相对方来源，用于迁移审计和可重放数据资产。",
    )
    legacy_partner_name = fields.Char(
        string="旧系统往来单位名称",
        copy=False,
        help="旧系统来源名称快照，用于审计与人工复核；正式显示名称仍使用 name。",
    )
    legacy_credit_code = fields.Char(
        string="旧系统统一社会信用代码",
        copy=False,
        help="旧系统 T_Base_CooperatCompany.TYSHXYDM。仅作迁移辅助校验，不作为本批唯一锁定键。",
    )
    legacy_tax_no = fields.Char(
        string="旧系统税号",
        copy=False,
        help="旧系统 T_Base_CooperatCompany.SH。仅作迁移辅助校验，不作为本批唯一锁定键。",
    )
    legacy_deleted_flag = fields.Char(
        string="旧系统删除标志",
        copy=False,
        help="旧系统来源记录 DEL。删除态记录默认不进入首轮安全写入。",
    )
    legacy_source_evidence = fields.Char(
        string="旧系统证据路径",
        copy=False,
        help="记录迁移候选的证据来源，例如 C_JFHKLR.SGHTID/WLDWID 单一相对方。",
    )
