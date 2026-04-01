# -*- coding: utf-8 -*-
from odoo import _, api, fields, models

from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver


ROLE_PROFILE_SELECTION = [
    ("owner", "普通员工"),
    ("pm", "项目经理"),
    ("finance", "财务人员"),
    ("executive", "管理层"),
]

ROLE_PROFILE_GROUP_XMLIDS = {
    "owner": [
        "smart_construction_custom.group_sc_role_owner",
        "smart_construction_core.group_sc_cap_project_read",
    ],
    "pm": [
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_core.group_sc_role_project_manager",
        "smart_construction_core.group_sc_cap_project_manager",
    ],
    "finance": [
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_core.group_sc_role_finance_manager",
        "smart_construction_core.group_sc_cap_finance_manager",
    ],
    "executive": [
        "smart_construction_custom.group_sc_role_executive",
    ],
}


class ResUsers(models.Model):
    _inherit = "res.users"

    sc_role_profile = fields.Selection(
        selection=ROLE_PROFILE_SELECTION,
        string="产品角色",
        default="owner",
        help="这里只选择产品角色语义。细粒度 ACL 和高级权限治理仍然保留在原生 groups 中。",
    )
    sc_role_effective = fields.Selection(
        selection=ROLE_PROFILE_SELECTION,
        string="当前生效角色",
        compute="_compute_sc_role_surface_meta",
    )
    sc_role_landing_label = fields.Char(
        string="默认首页",
        compute="_compute_sc_role_surface_meta",
    )

    @api.depends("groups_id", "sc_role_profile")
    def _compute_sc_role_surface_meta(self):
        resolver = IdentityResolver(self.env)
        role_map = resolver.build_role_surface_map_payload()
        selection_keys = {key for key, _label in ROLE_PROFILE_SELECTION}
        for user in self:
            role_code = resolver.resolve_role_code(resolver.user_group_xmlids(user))
            role_code = role_code if role_code in selection_keys else "owner"
            user.sc_role_effective = role_code
            role_meta = role_map.get(role_code) if isinstance(role_map, dict) else {}
            scene_candidates = role_meta.get("scene_candidates") if isinstance(role_meta, dict) else []
            user.sc_role_landing_label = (
                str(scene_candidates[0]).strip() if isinstance(scene_candidates, list) and scene_candidates else ""
            )

    @api.model_create_multi
    def create(self, vals_list):
        normalized_vals_list = []
        for vals in vals_list:
            normalized = dict(vals or {})
            role_code = self._normalize_sc_role_profile(normalized.get("sc_role_profile"))
            normalized["sc_role_profile"] = role_code or "owner"
            normalized = self._normalize_allowed_company_scope(normalized)
            normalized_vals_list.append(normalized)
        users = super().create(normalized_vals_list)
        users._sync_sc_role_profile_groups()
        return users

    def write(self, vals):
        normalized_vals = dict(vals or {})
        role_touched = "sc_role_profile" in normalized_vals
        company_touched = "company_id" in normalized_vals
        if role_touched:
            normalized_vals["sc_role_profile"] = self._normalize_sc_role_profile(normalized_vals.get("sc_role_profile")) or "owner"
        if company_touched:
            normalized_vals = self._normalize_allowed_company_scope(normalized_vals)
        result = super().write(normalized_vals)
        if role_touched:
            self._sync_sc_role_profile_groups()
        return result

    @api.model
    def _normalize_sc_role_profile(self, value):
        role_code = str(value or "").strip().lower()
        allowed = {key for key, _label in ROLE_PROFILE_SELECTION}
        return role_code if role_code in allowed else ""

    @api.model
    def _normalize_allowed_company_scope(self, vals):
        normalized_vals = dict(vals or {})
        company_id = int(normalized_vals.get("company_id") or 0)
        if company_id <= 0:
            return normalized_vals

        raw_company_ids = normalized_vals.get("company_ids")
        if not isinstance(raw_company_ids, list) or not raw_company_ids:
            normalized_vals["company_ids"] = [(6, 0, [company_id])]
            return normalized_vals

        allowed_company_ids = set()
        for command in raw_company_ids:
            if not isinstance(command, (list, tuple)) or not command:
                continue
            op = int(command[0] or 0)
            if op == 6 and len(command) >= 3 and isinstance(command[2], (list, tuple)):
                for cid in command[2]:
                    cid_int = int(cid or 0)
                    if cid_int > 0:
                        allowed_company_ids.add(cid_int)
            elif op == 4 and len(command) >= 2:
                cid_int = int(command[1] or 0)
                if cid_int > 0:
                    allowed_company_ids.add(cid_int)

        if company_id not in allowed_company_ids:
            allowed_company_ids.add(company_id)
            normalized_vals["company_ids"] = [(6, 0, sorted(allowed_company_ids))]

        return normalized_vals

    @api.model
    def _sc_managed_role_group_xmlids(self):
        xmlids = []
        for rows in ROLE_PROFILE_GROUP_XMLIDS.values():
            for xmlid in rows:
                text = str(xmlid or "").strip()
                if text and text not in xmlids:
                    xmlids.append(text)
        return xmlids

    def _resolve_sc_role_group_ids(self, role_code):
        group_ids = []
        for xmlid in ROLE_PROFILE_GROUP_XMLIDS.get(role_code, []):
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group and group.id not in group_ids:
                group_ids.append(group.id)
        base_group = self.env.ref("base.group_user", raise_if_not_found=False)
        if base_group and base_group.id not in group_ids:
            group_ids.append(base_group.id)
        return group_ids

    def _resolve_sc_managed_group_ids(self):
        group_ids = []
        for xmlid in self._sc_managed_role_group_xmlids():
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group and group.id not in group_ids:
                group_ids.append(group.id)
        return group_ids

    def _sync_sc_role_profile_groups(self):
        managed_group_ids = set(self._resolve_sc_managed_group_ids())
        for user in self:
            role_code = self._normalize_sc_role_profile(user.sc_role_profile) or "owner"
            target_group_ids = set(user._resolve_sc_role_group_ids(role_code))
            current_group_ids = set(user.groups_id.ids)
            commands = []
            for gid in sorted(managed_group_ids - target_group_ids):
                if gid in current_group_ids:
                    commands.append((3, gid))
            for gid in sorted(target_group_ids - current_group_ids):
                commands.append((4, gid))
            if commands:
                user.sudo().write({"groups_id": commands})

    def action_open_role_surface_landing(self):
        self.ensure_one()
        resolver = IdentityResolver(self.env)
        role_surface = resolver.build_role_surface(
            resolver.user_group_xmlids(self),
            [],
            set(),
        )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
            "params": {
                "role_code": role_surface.get("role_code"),
                "landing_scene_key": role_surface.get("landing_scene_key"),
            },
        }
