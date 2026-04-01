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
    sc_department_ids = fields.Many2many(
        "hr.department",
        "res_users_hr_department_rel",
        "user_id",
        "department_id",
        string="附加部门",
        domain="[('company_id', '=', company_id)]",
    )
    sc_manager_user_id = fields.Many2one(
        "res.users",
        string="直属上级",
        domain="[('company_ids', 'in', company_id)]",
    )
    sc_post_id = fields.Many2one(
        "sc.enterprise.post",
        string="主岗位",
        domain="[('company_id', '=', company_id)]",
    )
    sc_post_ids = fields.Many2many(
        "sc.enterprise.post",
        "res_users_sc_enterprise_post_rel",
        "user_id",
        "post_id",
        string="附加岗位",
        domain="[('company_id', '=', company_id)]",
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

    @api.constrains("sc_department_ids", "company_id")
    def _check_extra_department_company_consistency(self):
        for user in self:
            invalid_departments = user.sc_department_ids.filtered(
                lambda department: department.company_id
                and user.company_id
                and department.company_id != user.company_id
            )
            if invalid_departments:
                raise ValidationError(_("附加部门必须与用户当前公司一致。"))

    @api.constrains("sc_manager_user_id", "company_id")
    def _check_manager_company_consistency(self):
        for user in self:
            if (
                user.sc_manager_user_id
                and user.company_id
                and user.company_id not in user.sc_manager_user_id.company_ids
            ):
                raise ValidationError(_("直属上级必须属于当前公司。"))

    @api.constrains("sc_post_id", "company_id")
    def _check_post_company_consistency(self):
        for user in self:
            if (
                user.sc_post_id
                and user.company_id
                and user.sc_post_id.company_id
                and user.sc_post_id.company_id != user.company_id
            ):
                raise ValidationError(_("主岗位必须与用户当前公司一致。"))

    @api.constrains("sc_post_ids", "company_id")
    def _check_extra_post_company_consistency(self):
        for user in self:
            invalid_posts = user.sc_post_ids.filtered(
                lambda post: post.company_id and user.company_id and post.company_id != user.company_id
            )
            if invalid_posts:
                raise ValidationError(_("附加岗位必须与用户当前公司一致。"))
