# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    sc_department_id = fields.Many2one(
        "hr.department",
        string="所属部门",
        domain="[('company_id', '=', company_id)]",
    )
    sc_manager_user_id = fields.Many2one(
        "res.users",
        string="直属上级",
        domain="[('company_ids', 'in', company_id)]",
    )

    @api.constrains("sc_department_id", "company_id")
    def _check_department_company_consistency(self):
        for user in self:
            if (
                user.sc_department_id
                and user.company_id
                and user.sc_department_id.company_id
                and user.sc_department_id.company_id != user.company_id
            ):
                raise ValidationError(_("所属部门必须与用户当前公司一致。"))

    @api.constrains("sc_manager_user_id", "company_id")
    def _check_manager_company_consistency(self):
        for user in self:
            if (
                user.sc_manager_user_id
                and user.company_id
                and user.company_id not in user.sc_manager_user_id.company_ids
            ):
                raise ValidationError(_("直属上级必须属于当前公司。"))
