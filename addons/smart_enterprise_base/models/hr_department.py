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
