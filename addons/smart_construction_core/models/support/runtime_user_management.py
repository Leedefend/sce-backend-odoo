# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    sc_assignable_user_permission = fields.Boolean(string="可由用户配置管理员分配的角色", default=False, index=True)


class ResUsers(models.Model):
    _inherit = "res.users"

    login = fields.Char(string="用户名")
    name = fields.Char(string="姓名")
    phone = fields.Char(string="手机号")
    email = fields.Char(string="邮箱")

    sc_user_role_group_ids = fields.Many2many(
        "res.groups",
        "sc_runtime_user_role_group_rel",
        "user_id",
        "group_id",
        string="用户角色",
        compute="_compute_sc_user_role_group_ids",
        inverse="_inverse_sc_user_role_group_ids",
        store=False,
    )
    sc_user_permission_group_ids = fields.Many2many(
        "res.groups",
        string="用户角色兼容字段",
        compute="_compute_sc_user_role_group_ids",
        inverse="_inverse_sc_user_permission_group_ids",
        store=False,
    )

    @api.model
    def _sc_internal_group(self):
        return self.env.ref("smart_construction_core.group_sc_internal_user", raise_if_not_found=False)

    @api.model
    def _sc_assignable_groups(self):
        return self.env["res.groups"].sudo().search([("sc_assignable_user_permission", "=", True)])

    @api.depends("groups_id")
    def _compute_sc_user_role_group_ids(self):
        assignable = self._sc_assignable_groups()
        for user in self:
            roles = user.groups_id & assignable
            user.sc_user_role_group_ids = roles
            user.sc_user_permission_group_ids = roles

    def _inverse_assignable_user_groups(self, field_name):
        assignable = self._sc_assignable_groups()
        internal_group = self._sc_internal_group()
        for user in self:
            keep_groups = user.groups_id - assignable
            target_groups = keep_groups | user[field_name]
            if internal_group and not user.share:
                target_groups |= internal_group
            user.groups_id = [(6, 0, target_groups.ids)]

    def _inverse_sc_user_role_group_ids(self):
        self._inverse_assignable_user_groups("sc_user_role_group_ids")

    def _inverse_sc_user_permission_group_ids(self):
        self._inverse_assignable_user_groups("sc_user_permission_group_ids")

    @api.model_create_multi
    def create(self, vals_list):
        internal_group = self._sc_internal_group()
        for vals in vals_list:
            if vals.get("share"):
                continue
            commands = list(vals.get("groups_id") or [])
            if internal_group and not commands:
                commands.append((4, internal_group.id))
            if internal_group and self.env.context.get("sc_runtime_user_management"):
                commands.append((4, internal_group.id))
            if commands:
                vals["groups_id"] = commands
            if self.env.context.get("sc_runtime_user_management") and not vals.get("password"):
                vals["password"] = self.env.context.get("sc_default_initial_password") or "123456"
        return super().create(vals_list)
