# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sc_short_name = fields.Char("公司简称")
    sc_credit_code = fields.Char("统一社会信用代码")
    sc_contact_phone = fields.Char("联系电话")
    sc_address = fields.Char("地址")
    sc_is_active = fields.Boolean("启用", default=True)
    sc_department_count = fields.Integer("部门数", compute="_compute_sc_department_count")

    @api.depends_context("active_test")
    def _compute_sc_department_count(self):
        Department = self.env["hr.department"].sudo()
        grouped = Department.read_group(
            [("company_id", "in", self.ids)],
            ["company_id"],
            ["company_id"],
        )
        counts = {
            item["company_id"][0]: item["company_id_count"]
            for item in grouped
            if item.get("company_id")
        }
        for company in self:
            company.sc_department_count = int(counts.get(company.id, 0))

    def action_open_enterprise_departments(self):
        self.ensure_one()
        action = self.env.ref("smart_enterprise_base.action_enterprise_department").sudo().read()[0]
        action["name"] = _("组织架构：%s") % self.display_name
        action["domain"] = [("company_id", "=", self.id)]
        action["context"] = {
            "default_company_id": self.id,
            "search_default_company_id": self.id,
            "sc_company_name": self.display_name,
        }
        return action
