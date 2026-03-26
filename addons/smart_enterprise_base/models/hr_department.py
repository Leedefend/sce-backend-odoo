# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrDepartment(models.Model):
    _inherit = "hr.department"

    company_id = fields.Many2one(
        "res.company",
        string="所属公司",
        required=True,
        default=lambda self: self.env.company,
    )
    sc_manager_user_id = fields.Many2one(
        "res.users",
        string="部门负责人",
        domain="[('company_ids', 'in', company_id)]",
    )
    sc_is_active = fields.Boolean("启用", default=True)
    sc_user_count = fields.Integer("用户数", compute="_compute_sc_user_count")

    @api.depends_context("active_test")
    def _compute_sc_user_count(self):
        User = self.env["res.users"].sudo()
        grouped = User.read_group(
            [("sc_department_id", "in", self.ids)],
            ["sc_department_id"],
            ["sc_department_id"],
        )
        counts = {
            item["sc_department_id"][0]: item["sc_department_id_count"]
            for item in grouped
            if item.get("sc_department_id")
        }
        for department in self:
            department.sc_user_count = int(counts.get(department.id, 0))

    @api.constrains("parent_id", "company_id")
    def _check_parent_company_consistency(self):
        for department in self:
            if (
                department.parent_id
                and department.company_id
                and department.parent_id.company_id
                and department.parent_id.company_id != department.company_id
            ):
                raise ValidationError(_("上级部门必须与当前部门属于同一公司。"))

    @api.constrains("sc_manager_user_id", "company_id")
    def _check_manager_company_consistency(self):
        for department in self:
            if (
                department.sc_manager_user_id
                and department.company_id
                and department.company_id not in department.sc_manager_user_id.company_ids
            ):
                raise ValidationError(_("部门负责人必须属于当前公司。"))

    def action_open_enterprise_users(self):
        self.ensure_one()
        action = self.env.ref("smart_enterprise_base.action_enterprise_user").sudo().read()[0]
        action["name"] = _("用户设置：%s") % self.display_name
        action["domain"] = [("company_id", "=", self.company_id.id), ("sc_department_id", "=", self.id)]
        action["context"] = {
            "default_company_id": self.company_id.id,
            "default_sc_department_id": self.id,
            "search_default_company_id": self.company_id.id,
            "search_default_sc_department_id": self.id,
            "sc_department_name": self.display_name,
        }
        return action
