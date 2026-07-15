# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResGroups(models.Model):
    _inherit = "res.groups"

    sc_assignable_user_permission = fields.Boolean(string="可由用户配置管理员分配的角色", default=False, index=True)


class ResUsers(models.Model):
    _inherit = "res.users"

    login = fields.Char(string="登录账号")
    name = fields.Char(string="姓名")
    phone = fields.Char(string="手机号")
    email = fields.Char(string="邮箱")
    sc_runtime_source_login = fields.Char(
        string="用户名",
        compute="_compute_sc_runtime_profile_fields",
        search="_search_sc_runtime_source_login",
    )
    sc_runtime_legacy_user_id = fields.Char(
        string="原用户编号",
        compute="_compute_sc_runtime_profile_fields",
        search="_search_sc_runtime_legacy_user_id",
    )
    sc_runtime_company_real_user = fields.Boolean(
        string="公司真实用户",
        compute="_compute_sc_runtime_company_real_user",
        search="_search_sc_runtime_company_real_user",
    )
    sc_runtime_user_managed = fields.Boolean(
        string="用户配置管理员维护",
        default=False,
        index=True,
        copy=False,
    )

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
        string="用户角色",
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

    @api.model
    def _sc_legacy_profiles_by_user_id(self, user_ids):
        if "sc.legacy.user.profile" not in self.env.registry or not user_ids:
            return {}
        profiles = self.env["sc.legacy.user.profile"].sudo().with_context(active_test=False).search(
            [("user_id", "in", list(user_ids))],
            order="id asc",
        )
        profiles_by_user_id = {}
        for profile in profiles:
            profiles_by_user_id.setdefault(profile.user_id.id, profile)
        return profiles_by_user_id

    def _compute_sc_runtime_profile_fields(self):
        profiles_by_user_id = self._sc_legacy_profiles_by_user_id(self.ids)
        for user in self:
            profile = profiles_by_user_id.get(user.id)
            source_login = ""
            legacy_user_id = ""
            if profile:
                source_login = (
                    (profile.source_login or "").strip()
                    or (profile.generated_login or "").strip()
                    or (profile.legacy_user_id or "").strip()
                )
                legacy_user_id = (profile.legacy_user_id or "").strip()
            user.sc_runtime_source_login = source_login or (user.login or "").strip()
            user.sc_runtime_legacy_user_id = legacy_user_id

    @api.model
    def _search_sc_runtime_source_login(self, operator, value):
        if operator not in ("=", "!=", "like", "not like", "ilike", "not ilike"):
            operator = "ilike"
        domain = [("login", operator, value)]
        if "sc.legacy.user.profile" not in self.env.registry:
            return domain
        profile_domain = expression.OR(
            [
                [("source_login", operator, value)],
                [("generated_login", operator, value)],
                [("legacy_user_id", operator, value)],
            ]
        )
        user_ids = self.env["sc.legacy.user.profile"].sudo().with_context(active_test=False).search(profile_domain).mapped(
            "user_id"
        ).ids
        if not user_ids:
            return domain
        return expression.OR([[("id", "in", user_ids)], domain])

    @api.model
    def _search_sc_runtime_legacy_user_id(self, operator, value):
        if "sc.legacy.user.profile" not in self.env.registry:
            return [("id", "=", 0)]
        if operator not in ("=", "!=", "like", "not like", "ilike", "not ilike"):
            operator = "ilike"
        user_ids = self.env["sc.legacy.user.profile"].sudo().with_context(active_test=False).search(
            [("legacy_user_id", operator, value)]
        ).mapped("user_id").ids
        return [("id", "in", user_ids)]

    @api.model
    def _sc_runtime_company_real_user_ids(self):
        users = self.env["res.users"].sudo().with_context(active_test=False).search(
            [
                ("sc_runtime_user_managed", "=", True),
                ("share", "=", False),
                ("login", "!=", False),
            ]
        )
        if "sc.legacy.user.profile" not in self.env.registry:
            return users.ids
        profiles = self.env["sc.legacy.user.profile"].sudo().with_context(active_test=False).search(
            [("user_id", "!=", False)]
        )
        blocked_name_tokens = ("测试", "临时账号")
        blocked_name_prefixes = ("Demo", "Smoke", "技术")
        for profile in profiles:
            user = profile.user_id
            login = str(user.login or "")
            display_name = str(profile.display_name or user.name or "")
            if not user.active or user.share or not login:
                continue
            if login.startswith(("demo_", "history_system_user_")) or login == "default":
                continue
            if any(token in display_name for token in blocked_name_tokens):
                continue
            if display_name.startswith(blocked_name_prefixes):
                continue
            users |= user
        return users.ids

    def _compute_sc_runtime_company_real_user(self):
        real_user_ids = set(self._sc_runtime_company_real_user_ids())
        for user in self:
            user.sc_runtime_company_real_user = user.id in real_user_ids

    def _search_sc_runtime_company_real_user(self, operator, value):
        real_user_ids = self._sc_runtime_company_real_user_ids()
        positive = operator in ("=", "==") and bool(value) or operator in ("!=", "<>") and not bool(value)
        return [("id", "in" if positive else "not in", real_user_ids)]

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

    @api.model
    def _sc_runtime_user_management_allowed(self):
        return bool(
            self.env.context.get("sc_runtime_user_management")
            and self.env.user.has_group("smart_construction_core.group_sc_cap_business_config_admin")
        )

    @api.model
    def _sc_group_ids_from_commands(self, commands):
        ids = set()
        if not commands:
            return ids
        if isinstance(commands, (int, str)):
            try:
                return {int(commands)}
            except Exception:
                return set()
        for command in commands:
            if isinstance(command, int):
                ids.add(command)
                continue
            if not isinstance(command, (list, tuple)) or not command:
                continue
            op = int(command[0] or 0)
            if op == 6 and len(command) > 2 and isinstance(command[2], (list, tuple)):
                ids = {int(group_id) for group_id in command[2] if int(group_id or 0) > 0}
            elif op == 4 and len(command) > 1 and int(command[1] or 0) > 0:
                ids.add(int(command[1]))
            elif op == 3 and len(command) > 1:
                ids.discard(int(command[1] or 0))
            elif op == 5:
                ids.clear()
        return ids

    @api.model
    def _sc_runtime_user_safe_vals(self, vals, existing_user=False):
        allowed_fields = {
            "login",
            "name",
            "active",
            "phone",
            "email",
            "company_id",
            "password",
        }
        safe_vals = {key: vals[key] for key in allowed_fields if key in vals}
        safe_vals["share"] = False
        safe_vals["sc_runtime_user_managed"] = True

        role_commands = vals.get("sc_user_role_group_ids")
        if role_commands is None:
            role_commands = vals.get("sc_user_permission_group_ids")
        if role_commands is not None:
            assignable = self._sc_assignable_groups()
            requested = self.env["res.groups"].sudo().browse(list(self._sc_group_ids_from_commands(role_commands)))
            target_groups = requested & assignable
            if existing_user:
                target_groups |= existing_user.sudo().groups_id - assignable
            internal_group = self._sc_internal_group()
            if internal_group:
                target_groups |= internal_group
            safe_vals["groups_id"] = [(6, 0, target_groups.ids)]
        elif not existing_user:
            internal_group = self._sc_internal_group()
            if internal_group:
                safe_vals["groups_id"] = [(4, internal_group.id)]

        if not existing_user and not safe_vals.get("password"):
            initial_password = self.env.context.get("sc_default_initial_password")
            if not initial_password:
                raise ValidationError(_("创建用户必须通过受控运行时提供初始密码。"))
            safe_vals["password"] = initial_password
        return safe_vals

    @api.model_create_multi
    def create(self, vals_list):
        if self._sc_runtime_user_management_allowed() and not self.env.context.get("sc_runtime_user_management_sudo"):
            safe_vals_list = [self._sc_runtime_user_safe_vals(dict(vals or {})) for vals in vals_list]
            return self.sudo().with_context(
                dict(self.env.context, sc_runtime_user_management_sudo=True, no_reset_password=True)
            ).create(safe_vals_list).with_env(self.env)

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
                initial_password = self.env.context.get("sc_default_initial_password")
                if not initial_password:
                    raise ValidationError(_("创建用户必须通过受控运行时提供初始密码。"))
                vals["password"] = initial_password
        return super().create(vals_list)

    def write(self, vals):
        if self._sc_runtime_user_management_allowed() and not self.env.context.get("sc_runtime_user_management_sudo"):
            for user in self:
                safe_vals = self._sc_runtime_user_safe_vals(dict(vals or {}), existing_user=user)
                user.sudo().with_context(
                    dict(self.env.context, sc_runtime_user_management_sudo=True, no_reset_password=True)
                ).write(safe_vals)
            return True
        return super().write(vals)
