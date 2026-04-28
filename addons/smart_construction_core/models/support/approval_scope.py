# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ScApprovalScope(models.Model):
    _name = "sc.approval.scope"
    _description = "审批岗位人员"
    _order = "sequence, id"

    name = fields.Char(required=True, string="审批岗位")
    sequence = fields.Integer(default=10, index=True, string="顺序")
    scope_key = fields.Selection(
        selection="_selection_approval_scope",
        required=True,
        index=True,
        string="岗位编码",
    )
    group_id = fields.Many2one("res.groups", compute="_compute_group_id", store=True, readonly=True, string="执行权限组")
    user_ids = fields.Many2many(
        "res.users",
        compute="_compute_user_ids",
        inverse="_inverse_user_ids",
        string="人员",
    )
    user_count = fields.Integer(compute="_compute_user_count", string="人数")
    note = fields.Text(string="说明")

    _sql_constraints = [
        ("sc_approval_scope_key_uniq", "unique(scope_key)", "审批岗位不能重复。"),
    ]

    @api.model
    def _selection_approval_scope(self):
        return self.env["sc.approval.policy"]._selection_approval_scope()

    @api.depends("scope_key")
    def _compute_group_id(self):
        Policy = self.env["sc.approval.policy"]
        for rec in self:
            group = Policy._group_for_approval_scope(rec.scope_key)
            rec.group_id = group.id if group else False

    def _compute_user_ids(self):
        for rec in self:
            rec.user_ids = rec.group_id.sudo().users if rec.group_id else False

    @api.depends("user_ids")
    def _compute_user_count(self):
        for rec in self:
            rec.user_count = len(rec.user_ids.filtered(lambda user: user.active and not user.share))

    def _inverse_user_ids(self):
        for rec in self:
            if not rec.group_id:
                raise ValidationError(_("审批岗位缺少底层执行组，不能维护人员。"))
            users = rec.user_ids.filtered(lambda user: user.active and not user.share)
            rec.group_id.sudo().write({"users": [(6, 0, users.ids)]})

    def action_open_add_user_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("新增审批人员"),
            "res_model": "sc.approval.scope.user.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_scope_id": self.id,
                "default_scope_key": self.scope_key,
            },
        }


class ScApprovalScopeUserWizard(models.TransientModel):
    _name = "sc.approval.scope.user.wizard"
    _description = "新增审批人员"

    scope_id = fields.Many2one("sc.approval.scope", required=True, readonly=True, string="审批岗位")
    scope_key = fields.Selection(related="scope_id.scope_key", readonly=True, string="岗位编码")
    name = fields.Char(required=True, string="姓名")
    login = fields.Char(required=True, string="登录名")
    email = fields.Char(string="邮箱")
    password = fields.Char(default="123456", required=True, string="初始密码")

    def action_create_user(self):
        self.ensure_one()
        if not self.scope_id.group_id:
            raise UserError(_("审批岗位缺少底层执行组，不能新增人员。"))
        login = (self.login or "").strip()
        if not login:
            raise ValidationError(_("请填写登录名。"))
        existing = self.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        if existing:
            if existing.share:
                raise ValidationError(_("登录名 %s 已被外部用户占用。") % login)
            user = existing
        else:
            groups = [
                self.env.ref("base.group_user").id,
                self.env.ref("smart_construction_core.group_sc_internal_user").id,
                self.env.ref("smart_construction_core.group_sc_cap_business_initiator").id,
                self.scope_id.group_id.id,
            ]
            user = self.env["res.users"].with_context(no_reset_password=True).sudo().create(
                {
                    "name": self.name.strip(),
                    "login": login,
                    "email": (self.email or "").strip() or False,
                    "password": self.password,
                    "groups_id": [(6, 0, groups)],
                }
            )
        if self.scope_id.group_id not in user.groups_id:
            user.sudo().write({"groups_id": [(4, self.scope_id.group_id.id)]})
        return {"type": "ir.actions.act_window_close"}
