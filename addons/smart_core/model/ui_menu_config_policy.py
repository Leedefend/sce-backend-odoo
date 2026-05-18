# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models


class UiMenuConfigPolicy(models.Model):
    _name = "ui.menu.config.policy"
    _description = "User Configurable Menu Policy"
    _rec_name = "name"
    _order = "company_id, menu_id, id"

    SOURCE_KIND = "ui_menu_config_policy_overlay"
    SOURCE_AUTHORITIES = ("ui.menu.config.policy", "ir.ui.menu", "res.groups")

    name = fields.Char(string="配置名称", compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company",
        string="适用公司",
        default=lambda self: self.env.company,
        index=True,
        required=True,
    )
    menu_id = fields.Many2one("ir.ui.menu", string="菜单", required=True, index=True, ondelete="cascade")
    menu_complete_name = fields.Char(string="菜单路径", related="menu_id.complete_name", readonly=True)
    custom_label = fields.Char(string="显示名称")
    sequence_override = fields.Integer(string="显示顺序")
    visible = fields.Boolean(string="显示菜单", default=True, index=True)
    role_group_ids = fields.Many2many(
        "res.groups",
        "ui_menu_config_policy_group_rel",
        "policy_id",
        "group_id",
        string="适用角色组",
        help="留空表示对当前公司所有用户生效；填写后仅对命中这些角色组的用户生效。",
    )
    note = fields.Text(string="说明")
    active = fields.Boolean(string="启用", default=True, index=True)

    @api.depends("menu_id", "custom_label", "visible")
    def _compute_name(self):
        for record in self:
            label = record.custom_label or record.menu_id.display_name or "菜单配置"
            state = "显示" if record.visible else "隐藏"
            record.name = "%s - %s" % (label, state)

    @api.model
    def _source_contract(self) -> dict:
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": "platform_menu_api.nav_fact",
        }

    @api.model
    def _runtime_policies_for_user(self, user=None):
        user = user or self.env.user
        user_group_ids = set(user.groups_id.ids)
        policies = self.sudo().search(
            [
                ("active", "=", True),
                ("company_id", "=", self.env.company.id),
                ("menu_id", "!=", False),
            ],
            order="id desc",
        )
        applicable = {}
        for policy in policies:
            role_group_ids = set(policy.role_group_ids.ids)
            if role_group_ids and not (role_group_ids & user_group_ids):
                continue
            menu_id = int(policy.menu_id.id)
            existing = applicable.get(menu_id)
            existing_specific = bool(existing and existing.role_group_ids)
            current_specific = bool(role_group_ids)
            if existing and existing_specific and not current_specific:
                continue
            applicable[menu_id] = policy
        return applicable

    @api.model
    def apply_runtime_overlay(self, nav_fact: dict, user=None) -> tuple[dict, dict]:
        if not isinstance(nav_fact, dict):
            return nav_fact, {"applied_count": 0, "hidden_count": 0, "renamed_count": 0, "reordered_count": 0}
        policies_by_menu = self._runtime_policies_for_user(user=user)
        if not policies_by_menu:
            return nav_fact, {"applied_count": 0, "hidden_count": 0, "renamed_count": 0, "reordered_count": 0}

        stats = {
            "source_authority": self._source_contract(),
            "applied_count": 0,
            "hidden_count": 0,
            "renamed_count": 0,
            "reordered_count": 0,
        }

        def apply_node(node: dict) -> dict | None:
            menu_id = node.get("menu_id")
            try:
                normalized_menu_id = int(menu_id or 0)
            except Exception:
                normalized_menu_id = 0
            policy = policies_by_menu.get(normalized_menu_id)
            if policy:
                stats["applied_count"] += 1
                if not policy.visible:
                    stats["hidden_count"] += 1
                    return None
                if policy.custom_label:
                    node["name"] = policy.custom_label
                    node["title"] = policy.custom_label
                    stats["renamed_count"] += 1
                if policy.sequence_override:
                    node["sequence"] = policy.sequence_override
                    stats["reordered_count"] += 1
            children = node.get("children")
            if isinstance(children, list):
                next_children = []
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    applied_child = apply_node(dict(child))
                    if applied_child is not None:
                        next_children.append(applied_child)
                next_children.sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
                node["children"] = next_children
            return node

        out = dict(nav_fact)
        out["flat"] = [
            applied
            for node in out.get("flat", [])
            if isinstance(node, dict)
            for applied in [apply_node(dict(node))]
            if applied is not None
        ]
        out["flat"].sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
        out["tree"] = [
            applied
            for node in out.get("tree", [])
            if isinstance(node, dict)
            for applied in [apply_node(dict(node))]
            if applied is not None
        ]
        out["tree"].sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
        return out, stats
