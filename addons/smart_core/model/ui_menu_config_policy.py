# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    menu_complete_name = fields.Char(string="菜单路径", compute="_compute_menu_preview_fields", readonly=True)
    original_label = fields.Char(string="原菜单名称", compute="_compute_menu_preview_fields", readonly=True)
    current_parent_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="当前所属分组",
        compute="_compute_menu_preview_fields",
        readonly=True,
    )
    current_parent_menu_complete_name = fields.Char(
        string="当前分组路径",
        compute="_compute_menu_preview_fields",
        readonly=True,
    )
    target_parent_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="调整到菜单分组",
        help="留空表示保留原分组；选择后，该菜单会显示到所选分组下面。",
    )
    target_parent_menu_complete_name = fields.Char(
        string="目标分组路径",
        compute="_compute_menu_preview_fields",
        readonly=True,
    )
    custom_label = fields.Char(string="显示名称")
    sequence_override = fields.Integer(string="显示顺序")
    visible = fields.Boolean(string="显示菜单", default=True, index=True)
    role_group_ids = fields.Many2many(
        "res.groups",
        "ui_menu_config_policy_group_rel",
        "policy_id",
        "group_id",
        string="适用用户组",
        help="留空表示对当前公司所有用户生效；填写后仅对这些用户组中的用户生效。",
    )
    note = fields.Text(string="说明")
    active = fields.Boolean(string="启用", default=True, index=True)
    effect_summary = fields.Char(string="配置结果", compute="_compute_user_summaries")
    scope_summary = fields.Char(string="适用范围", compute="_compute_user_summaries")
    preview_summary = fields.Char(string="生效说明", compute="_compute_user_summaries")

    @api.depends("menu_id", "custom_label", "visible")
    def _compute_name(self):
        for record in self:
            label = record.custom_label or record.menu_id.display_name or "菜单配置"
            state = "显示" if record.visible else "隐藏"
            record.name = "%s - %s" % (label, state)

    @api.depends("menu_id", "target_parent_menu_id")
    def _compute_menu_preview_fields(self):
        for record in self:
            menu = record.menu_id
            parent = menu.parent_id if menu else self.env["ir.ui.menu"]
            target_parent = record.target_parent_menu_id
            record.menu_complete_name = menu.complete_name if menu else False
            record.original_label = menu.name if menu else False
            record.current_parent_menu_id = parent
            record.current_parent_menu_complete_name = parent.complete_name if parent else False
            record.target_parent_menu_complete_name = target_parent.complete_name if target_parent else False

    @api.depends(
        "menu_id",
        "custom_label",
        "sequence_override",
        "visible",
        "role_group_ids",
        "target_parent_menu_id",
        "current_parent_menu_id",
    )
    def _compute_user_summaries(self):
        for record in self:
            menu_label = record.custom_label or record.original_label or record.menu_id.display_name or "未选择菜单"
            current_group = record.current_parent_menu_id.display_name or "顶层菜单"
            target_group = record.target_parent_menu_id.display_name or current_group
            if not record.visible:
                record.effect_summary = "隐藏菜单"
            else:
                parts = []
                if record.target_parent_menu_id:
                    parts.append("放到：%s" % target_group)
                if record.custom_label:
                    parts.append("显示为：%s" % record.custom_label)
                if record.sequence_override:
                    parts.append("排序：%s" % record.sequence_override)
                record.effect_summary = "；".join(parts) if parts else "保持原样显示"
            groups = record.role_group_ids.mapped("display_name")
            record.scope_summary = "、".join(groups) if groups else "当前公司所有用户"
            if not record.visible:
                record.preview_summary = "对%s隐藏菜单“%s”。" % (record.scope_summary, record.original_label or menu_label)
            else:
                record.preview_summary = "对%s显示菜单“%s”，位置：%s。保存后刷新页面生效。" % (
                    record.scope_summary,
                    menu_label,
                    target_group,
                )

    @api.onchange("menu_id")
    def _onchange_menu_id(self):
        for record in self:
            if record.menu_id and record.target_parent_menu_id == record.menu_id:
                record.target_parent_menu_id = False
            record._compute_menu_preview_fields()
            record._compute_user_summaries()

    @api.onchange("target_parent_menu_id", "custom_label", "sequence_override", "visible", "role_group_ids")
    def _onchange_preview_inputs(self):
        for record in self:
            record._compute_menu_preview_fields()
            record._compute_user_summaries()

    @api.constrains("menu_id", "target_parent_menu_id")
    def _check_target_parent_menu(self):
        for record in self:
            if record.menu_id and record.target_parent_menu_id and record.menu_id == record.target_parent_menu_id:
                raise ValidationError("菜单不能移动到自己下面。")
            parent = record.target_parent_menu_id
            while parent:
                if parent == record.menu_id:
                    raise ValidationError("菜单不能移动到自己的下级菜单下面。")
                parent = parent.parent_id

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
            return nav_fact, {"applied_count": 0, "hidden_count": 0, "renamed_count": 0, "reordered_count": 0, "moved_count": 0}
        policies_by_menu = self._runtime_policies_for_user(user=user)
        if not policies_by_menu:
            return nav_fact, {"applied_count": 0, "hidden_count": 0, "renamed_count": 0, "reordered_count": 0, "moved_count": 0}

        stats = {
            "source_authority": self._source_contract(),
            "applied_count": 0,
            "hidden_count": 0,
            "renamed_count": 0,
            "reordered_count": 0,
            "moved_count": 0,
        }
        move_targets = {
            menu_id: policy.target_parent_menu_id
            for menu_id, policy in policies_by_menu.items()
            if policy.visible and policy.target_parent_menu_id and int(policy.target_parent_menu_id.id) != int(menu_id)
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
                    node["label"] = policy.custom_label
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

        def sort_children(nodes: list[dict]) -> list[dict]:
            nodes.sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
            return nodes

        def node_matches_menu(node: dict, menu) -> bool:
            if not menu:
                return False
            menu_id = int(menu.id)
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            for candidate in (node.get("menu_id"), meta.get("menu_id")):
                try:
                    if int(candidate or 0) == menu_id:
                        return True
                except Exception:
                    continue
            labels = {
                str(node.get("name") or "").strip(),
                str(node.get("label") or "").strip(),
                str(node.get("title") or "").strip(),
            }
            return bool(str(menu.name or "").strip() in labels)

        def remove_node(nodes: list[dict], menu_id: int) -> tuple[list[dict], dict | None]:
            removed = None
            next_nodes = []
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                try:
                    current_id = int(node.get("menu_id") or 0)
                except Exception:
                    current_id = 0
                if current_id == menu_id and removed is None:
                    removed = node
                    continue
                children = node.get("children") if isinstance(node.get("children"), list) else []
                if children:
                    next_children, child_removed = remove_node(children, menu_id)
                    if child_removed is not None and removed is None:
                        removed = child_removed
                    node = dict(node)
                    node["children"] = sort_children(next_children)
                next_nodes.append(node)
            return next_nodes, removed

        def insert_node(nodes: list[dict], target_menu, moved_node: dict) -> tuple[list[dict], bool]:
            next_nodes = []
            inserted = False
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node = dict(node)
                children = node.get("children") if isinstance(node.get("children"), list) else []
                if node_matches_menu(node, target_menu):
                    moved = dict(moved_node)
                    moved["parent_id"] = int(target_menu.id)
                    moved_meta = dict(moved.get("meta") if isinstance(moved.get("meta"), dict) else {})
                    moved_meta["parent_menu_id"] = int(target_menu.id)
                    moved_meta["parent_menu_label"] = str(target_menu.name or "")
                    moved["meta"] = moved_meta
                    node["children"] = sort_children(children + [moved])
                    inserted = True
                elif children:
                    next_children, child_inserted = insert_node(children, target_menu, moved_node)
                    node["children"] = next_children
                    inserted = inserted or child_inserted
                next_nodes.append(node)
            return next_nodes, inserted

        def apply_moves(nodes: list[dict]) -> list[dict]:
            next_nodes = nodes
            for menu_id, target_menu in move_targets.items():
                next_nodes, moved_node = remove_node(next_nodes, int(menu_id))
                if moved_node is None:
                    continue
                next_nodes, inserted = insert_node(next_nodes, target_menu, moved_node)
                if inserted:
                    stats["moved_count"] += 1
                else:
                    next_nodes.append(moved_node)
            return sort_children(next_nodes)

        out = dict(nav_fact)
        out["flat"] = [
            applied
            for node in out.get("flat", [])
            if isinstance(node, dict)
            for applied in [apply_node(dict(node))]
            if applied is not None
        ]
        out["flat"].sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
        out["tree"] = apply_moves([
            applied
            for node in out.get("tree", [])
            if isinstance(node, dict)
            for applied in [apply_node(dict(node))]
            if applied is not None
        ])
        return out, stats
