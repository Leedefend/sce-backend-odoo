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

    @api.model_create_multi
    def create(self, vals_list):
        self._ensure_fiscalyear_db_defaults()
        for vals in vals_list:
            if "account_opening_date" in self._fields and not vals.get("account_opening_date"):
                vals["account_opening_date"] = fields.Date.context_today(self).replace(month=1, day=1)
            if "po_lead" in self._fields and vals.get("po_lead") is None:
                vals["po_lead"] = 0.0
            if "fiscalyear_last_day" in self._fields and not vals.get("fiscalyear_last_day"):
                vals["fiscalyear_last_day"] = 31
            if "fiscalyear_last_month" in self._fields and not vals.get("fiscalyear_last_month"):
                vals["fiscalyear_last_month"] = "12"
        return super().create(vals_list)

    def init(self):
        super().init()
        self._ensure_fiscalyear_db_defaults()

    def _ensure_fiscalyear_db_defaults(self):
        self.env.cr.execute(
            """
            SELECT column_name
              FROM information_schema.columns
             WHERE table_name = 'res_company'
               AND column_name IN (
                   'account_opening_date',
                   'fiscalyear_last_day',
                   'fiscalyear_last_month',
                   'po_lead'
               )
            """
        )
        columns = {row[0] for row in self.env.cr.fetchall()}
        if "account_opening_date" in columns:
            self.env.cr.execute(
                """
                ALTER TABLE res_company
                ALTER COLUMN account_opening_date SET DEFAULT date_trunc('year', CURRENT_DATE)::date
                """
            )
        if "fiscalyear_last_day" in columns:
            self.env.cr.execute(
                "ALTER TABLE res_company ALTER COLUMN fiscalyear_last_day SET DEFAULT 31"
            )
        if "fiscalyear_last_month" in columns:
            self.env.cr.execute(
                "ALTER TABLE res_company ALTER COLUMN fiscalyear_last_month SET DEFAULT '12'"
            )
        if "po_lead" in columns:
            self.env.cr.execute(
                "ALTER TABLE res_company ALTER COLUMN po_lead SET DEFAULT 0.0"
            )

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
