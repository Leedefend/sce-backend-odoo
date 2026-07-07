# -*- coding: utf-8 -*-
from __future__ import annotations

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.smart_core.utils.backend_contract_boundaries import (
    LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS,
    MENU_CONFIG_CONFIG_ONLY_PARAM,
    MENU_CONFIG_POLICY_MODEL,
    MENU_CONFIG_RUNTIME_SOURCE_CONTRACT,
    MENU_CONFIG_RUNTIME_SOURCE_POLICY,
)

_PROTECTED_NODE_EXCLUDED_FINGERPRINT_TOKENS: set[str] = set()

_CONFIG_ONLY_RECOVERY_MENU_XMLIDS = frozenset({
    "smart_construction_core.menu_sc_business_config_center",
    "smart_construction_core.menu_sc_business_config_workbench",
    "smart_construction_core.menu_ui_menu_config_policy_business_config",
}) | LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS


def register_protected_node_excluded_fingerprint_token(token: str) -> None:
    text = str(token or "").strip()
    if text:
        _PROTECTED_NODE_EXCLUDED_FINGERPRINT_TOKENS.add(text)


def protected_node_excluded_fingerprint_tokens() -> tuple[str, ...]:
    return tuple(sorted(_PROTECTED_NODE_EXCLUDED_FINGERPRINT_TOKENS))


def _to_int(value) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _to_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


class UiMenuConfigPolicy(models.Model):
    _name = MENU_CONFIG_POLICY_MODEL
    _description = "User Configurable Menu Policy"
    _rec_name = "name"
    _order = "company_id, menu_id, id"

    SOURCE_KIND = "ui_menu_config_policy_overlay"
    SOURCE_AUTHORITIES = (MENU_CONFIG_POLICY_MODEL, "ir.ui.menu", "res.groups")

    name = fields.Char(string="配置名称", compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company",
        string="适用公司",
        default=lambda self: self.env.company,
        index=True,
        required=True,
    )
    menu_id = fields.Many2one("ir.ui.menu", string="菜单", required=True, index=True, ondelete="cascade")
    menu_complete_name = fields.Char(string="菜单路径", readonly=True)
    original_label = fields.Char(string="原菜单名称", readonly=True)
    current_parent_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="当前所属分组",
        readonly=True,
    )
    current_parent_menu_complete_name = fields.Char(
        string="当前分组路径",
        readonly=True,
    )
    target_parent_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="调整到菜单分组",
        help="留空表示保留原分组；选择后，该菜单会显示到所选分组下面。",
    )
    target_parent_menu_complete_name = fields.Char(
        string="目标分组路径",
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
        string="可见业务角色",
        help="留空表示所有业务角色可见；填写后仅对这些业务角色中的用户生效。",
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

    @api.model
    def _menu_preview_values(self, menu=None, target_parent=None) -> dict:
        menu = menu or self.env["ir.ui.menu"]
        parent = menu.parent_id if menu else self.env["ir.ui.menu"]
        target_parent = target_parent or self.env["ir.ui.menu"]
        return {
            "menu_complete_name": menu.complete_name if menu else False,
            "original_label": menu.name if menu else False,
            "current_parent_menu_id": parent.id if parent else False,
            "current_parent_menu_complete_name": parent.complete_name if parent else False,
            "target_parent_menu_complete_name": target_parent.complete_name if target_parent else False,
        }

    def _apply_menu_preview_values(self):
        for record in self:
            for field_name, value in record._menu_preview_values(record.menu_id, record.target_parent_menu_id).items():
                record[field_name] = value

    @api.model_create_multi
    def create(self, vals_list):
        Menu = self.env["ir.ui.menu"]
        for vals in vals_list:
            menu = Menu.browse(vals.get("menu_id")) if vals.get("menu_id") else Menu
            target_parent = Menu.browse(vals.get("target_parent_menu_id")) if vals.get("target_parent_menu_id") else Menu
            vals.update(self._menu_preview_values(menu, target_parent))
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        if {"menu_id", "target_parent_menu_id"} & set(vals):
            for record in self:
                super(UiMenuConfigPolicy, record).write(
                    record._menu_preview_values(record.menu_id, record.target_parent_menu_id)
                )
        return result

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
            record.scope_summary = "、".join(groups) if groups else "所有业务角色"
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
            record._apply_menu_preview_values()
            record._compute_user_summaries()
            return {"value": record._onchange_preview_values()}

    @api.onchange("target_parent_menu_id", "custom_label", "sequence_override", "visible", "role_group_ids")
    def _onchange_preview_inputs(self):
        for record in self:
            record._apply_menu_preview_values()
            record._compute_user_summaries()
            return {"value": record._onchange_preview_values()}

    def _onchange_preview_values(self) -> dict:
        self.ensure_one()
        values = self._menu_preview_values(self.menu_id, self.target_parent_menu_id)
        current_parent = self.current_parent_menu_id or self.menu_id.parent_id
        if current_parent:
            values["current_parent_menu_id"] = [current_parent.id, current_parent.display_name]
        values.update(
            {
                "effect_summary": self.effect_summary,
                "scope_summary": self.scope_summary,
                "preview_summary": self.preview_summary,
            }
        )
        return values

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
    def _source_contract(self, *, runtime_source: str = MENU_CONFIG_RUNTIME_SOURCE_POLICY) -> dict:
        authorities = ["ir.ui.menu", "res.groups"]
        if runtime_source == MENU_CONFIG_RUNTIME_SOURCE_CONTRACT:
            authorities.insert(0, "ui.business.config.contract")
            authorities.append(MENU_CONFIG_POLICY_MODEL)
        else:
            authorities.insert(0, MENU_CONFIG_POLICY_MODEL)
        return {
            "kind": self.SOURCE_KIND,
            "authorities": authorities,
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": "platform_menu_api.nav_fact",
            "runtime_source": runtime_source,
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
            if existing and existing_specific == current_specific:
                continue
            applicable[menu_id] = policy
        return applicable

    @api.model
    def _runtime_contract_policy_source_for_user(self, user=None) -> tuple[dict, bool]:
        if "ui.business.config.contract" not in self.env:
            return {}, False
        user = user or self.env.user
        user_group_ids = set(user.groups_id.ids)
        Contract = self.env["ui.business.config.contract"].sudo()
        contract = Contract.search([
            ("active", "=", True),
            ("status", "=", "published"),
            ("name", "=", "menu.config.company.%s" % int(self.env.company.id or 0)),
            ("model", "=", "ir.ui.menu"),
            ("company_id", "in", [False, self.env.company.id]),
        ], order="version_no desc, id desc", limit=1)
        if not contract:
            return {}, False
        payload = contract.contract_json if isinstance(contract.contract_json, dict) else {}
        orchestration = payload.get("menu_orchestration") if isinstance(payload.get("menu_orchestration"), dict) else {}
        if str(orchestration.get("schema_version") or "").strip() != "menu_orchestration.v1":
            return {}, False
        rows = orchestration.get("policies") if isinstance(orchestration.get("policies"), list) else []
        applicable = {}
        Menu = self.env["ir.ui.menu"].sudo()
        for row in rows:
            if not isinstance(row, dict) or not _to_bool(row.get("active"), True):
                continue
            role_group_ids = {int(item or 0) for item in (row.get("role_group_ids") or []) if _to_int(item)}
            if role_group_ids and not (role_group_ids & user_group_ids):
                continue
            menu_id = _to_int(row.get("menu_id"))
            if not menu_id:
                continue
            if not Menu.browse(menu_id).exists():
                continue
            parent_id = _to_int(row.get("target_parent_menu_id"))
            if parent_id and not Menu.browse(parent_id).exists():
                row = dict(row)
                row["target_parent_menu_id"] = 0
            existing = applicable.get(menu_id)
            existing_specific = bool(existing and existing.get("role_group_ids"))
            current_specific = bool(role_group_ids)
            if existing and existing_specific and not current_specific:
                continue
            if existing and existing_specific == current_specific:
                continue
            applicable[menu_id] = dict(row)
        return applicable, True

    @api.model
    def _runtime_contract_policies_for_user(self, user=None):
        policies, _contract_found = self._runtime_contract_policy_source_for_user(user=user)
        return policies

    @api.model
    def _runtime_menu_config_source_for_user(self, user=None):
        contract_policies, contract_found = self._runtime_contract_policy_source_for_user(user=user)
        if contract_found:
            return contract_policies, MENU_CONFIG_RUNTIME_SOURCE_CONTRACT
        return self._runtime_policies_for_user(user=user), MENU_CONFIG_RUNTIME_SOURCE_POLICY

    @api.model
    def apply_runtime_overlay(self, nav_fact: dict, user=None) -> tuple[dict, dict]:
        if not isinstance(nav_fact, dict):
            return nav_fact, {"applied_count": 0, "hidden_count": 0, "renamed_count": 0, "reordered_count": 0, "moved_count": 0}
        policies_by_menu, runtime_source = self._runtime_menu_config_source_for_user(user=user)

        def config_only_enabled() -> bool:
            try:
                raw = self.env["ir.config_parameter"].sudo().get_param(
                    MENU_CONFIG_CONFIG_ONLY_PARAM,
                    "1",
                )
            except Exception:
                raw = "1"
            return str(raw or "").strip().lower() not in {"0", "false", "no", "off"}

        if not policies_by_menu:
            config_only = config_only_enabled()
            stats = {
                "source_authority": self._source_contract(runtime_source=runtime_source),
                "runtime_source": runtime_source,
                "applied_count": 0,
                "hidden_count": 0,
                "unconfigured_hidden_count": 0,
                "protected_count": 0,
                "renamed_count": 0,
                "reordered_count": 0,
                "moved_count": 0,
                "parent_aligned_count": 0,
                "config_only": config_only,
            }
            if not config_only:
                return nav_fact, stats

            def count_nodes(nodes) -> int:
                total = 0
                for node in nodes if isinstance(nodes, list) else []:
                    if not isinstance(node, dict):
                        continue
                    total += 1
                    total += count_nodes(node.get("children"))
                return total

            stats["unconfigured_hidden_count"] = count_nodes(nav_fact.get("tree"))
            return {**nav_fact, "tree": [], "flat": []}, stats

        def policy_visible(policy) -> bool:
            return _to_bool(policy.get("visible"), True) if isinstance(policy, dict) else bool(policy.visible)

        def policy_custom_label(policy) -> str:
            return str(policy.get("custom_label") or "").strip() if isinstance(policy, dict) else str(policy.custom_label or "").strip()

        def policy_sequence_override(policy) -> int:
            return _to_int(policy.get("sequence_override")) if isinstance(policy, dict) else _to_int(policy.sequence_override)

        def policy_menu_name(policy) -> str:
            return str(policy.get("menu_label") or "").strip() if isinstance(policy, dict) else str(policy.menu_id.name or "").strip()

        def policy_menu_record(policy):
            if not isinstance(policy, dict):
                return policy.menu_id
            menu_id = _to_int(policy.get("menu_id"))
            return self.env["ir.ui.menu"].browse(menu_id) if menu_id else self.env["ir.ui.menu"]

        def policy_target_parent(policy):
            if not isinstance(policy, dict):
                return policy.target_parent_menu_id
            parent_id = _to_int(policy.get("target_parent_menu_id"))
            return self.env["ir.ui.menu"].browse(parent_id) if parent_id else self.env["ir.ui.menu"].browse(0)

        def policy_menu_exists(policy) -> bool:
            return bool(policy_menu_record(policy).exists())

        stats = {
            "source_authority": self._source_contract(runtime_source=runtime_source),
            "runtime_source": runtime_source,
            "applied_count": 0,
            "hidden_count": 0,
            "unconfigured_hidden_count": 0,
            "protected_count": 0,
            "renamed_count": 0,
            "reordered_count": 0,
            "moved_count": 0,
            "parent_aligned_count": 0,
            "config_only": config_only_enabled(),
        }
        move_targets = [
            {
                "menu_id": int(menu_id),
                "source_menu": policy_menu_record(policy),
                "source_label": policy_menu_name(policy),
                "target_menu": policy_target_parent(policy),
            }
            for menu_id, policy in policies_by_menu.items()
            if policy_visible(policy)
            and policy_menu_exists(policy)
            and policy_target_parent(policy)
            and policy_target_parent(policy).exists()
            and int(policy_target_parent(policy).id or 0) != int(menu_id)
        ]

        def menu_depth(menu) -> int:
            depth = 0
            seen = set()
            current = menu.exists() if menu else None
            while current and int(current.id or 0) not in seen:
                seen.add(int(current.id or 0))
                depth += 1
                current = current.parent_id
            return depth

        move_targets.sort(key=lambda move: (
            menu_depth(move["source_menu"]),
            menu_depth(move["target_menu"]),
            int(move["menu_id"] or 0),
        ))
        policies_by_label = {}
        for policy in policies_by_menu.values():
            label = policy_menu_name(policy)
            if label:
                policies_by_label.setdefault(label, policy)

        def node_menu_id(node: dict) -> int:
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            candidates = []
            for candidate in (node.get("menu_id"), meta.get("menu_id"), node.get("id")):
                try:
                    value = int(candidate or 0)
                except Exception:
                    value = 0
                if value:
                    candidates.append(value)
            return next((value for value in candidates if value in policies_by_menu), candidates[0] if candidates else 0)

        protected_config_menu_xmlids_by_id_cache = None

        def protected_config_menu_xmlids_by_id() -> dict[int, str]:
            nonlocal protected_config_menu_xmlids_by_id_cache
            if protected_config_menu_xmlids_by_id_cache is not None:
                return protected_config_menu_xmlids_by_id_cache
            protected_config_menu_xmlids_by_id_cache = {}
            try:
                ModelData = self.env["ir.model.data"].sudo()
            except Exception:
                return protected_config_menu_xmlids_by_id_cache
            modules = {xmlid.split(".", 1)[0] for xmlid in LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS}
            names = {xmlid.split(".", 1)[1] for xmlid in LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS}
            try:
                rows = ModelData.search([
                    ("model", "=", "ir.ui.menu"),
                    ("module", "in", list(modules)),
                    ("name", "in", list(names)),
                ])
            except Exception:
                rows = []
            for row in rows or []:
                xmlid = "%s.%s" % (str(getattr(row, "module", "") or ""), str(getattr(row, "name", "") or ""))
                menu_id = _to_int(getattr(row, "res_id", 0))
                if xmlid in LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS and menu_id:
                    protected_config_menu_xmlids_by_id_cache[menu_id] = xmlid
            return protected_config_menu_xmlids_by_id_cache

        def node_menu_xmlid(node: dict) -> str:
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            return str(node.get("menu_xmlid") or meta.get("menu_xmlid") or "").strip()

        def is_protected_runtime_config_menu_id(menu_id: int) -> bool:
            menu_id = _to_int(menu_id)
            if not menu_id or menu_id not in protected_config_menu_xmlids_by_id():
                return False
            menu = self.env["ir.ui.menu"].browse(menu_id).exists()
            return bool(menu and menu_visible_to_user(menu))

        def is_protected_runtime_config_xmlid(xmlid: str) -> bool:
            xmlid = str(xmlid or "").strip()
            if xmlid not in LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS:
                return False
            for menu_id, candidate_xmlid in protected_config_menu_xmlids_by_id().items():
                if candidate_xmlid == xmlid:
                    return is_protected_runtime_config_menu_id(menu_id)
            return False

        config_only_recovery_menu_xmlids_by_id_cache = None

        def config_only_recovery_menu_xmlids_by_id() -> dict[int, str]:
            nonlocal config_only_recovery_menu_xmlids_by_id_cache
            if config_only_recovery_menu_xmlids_by_id_cache is not None:
                return config_only_recovery_menu_xmlids_by_id_cache
            config_only_recovery_menu_xmlids_by_id_cache = {}
            try:
                ModelData = self.env["ir.model.data"].sudo()
            except Exception:
                return config_only_recovery_menu_xmlids_by_id_cache
            modules = {xmlid.split(".", 1)[0] for xmlid in _CONFIG_ONLY_RECOVERY_MENU_XMLIDS}
            names = {xmlid.split(".", 1)[1] for xmlid in _CONFIG_ONLY_RECOVERY_MENU_XMLIDS}
            try:
                rows = ModelData.search([
                    ("model", "=", "ir.ui.menu"),
                    ("module", "in", list(modules)),
                    ("name", "in", list(names)),
                ])
            except Exception:
                rows = []
            for row in rows or []:
                xmlid = "%s.%s" % (str(getattr(row, "module", "") or ""), str(getattr(row, "name", "") or ""))
                menu_id = _to_int(getattr(row, "res_id", 0))
                if xmlid in _CONFIG_ONLY_RECOVERY_MENU_XMLIDS and menu_id:
                    config_only_recovery_menu_xmlids_by_id_cache[menu_id] = xmlid
            return config_only_recovery_menu_xmlids_by_id_cache

        def is_config_only_recovery_menu_id(menu_id: int) -> bool:
            menu_id = _to_int(menu_id)
            if not menu_id or menu_id not in config_only_recovery_menu_xmlids_by_id():
                return False
            menu = self.env["ir.ui.menu"].browse(menu_id).exists()
            return bool(menu and menu_visible_to_user(menu))

        def is_protected_runtime_config_node(node: dict) -> bool:
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            menu_id = node_menu_id(node)
            if is_protected_runtime_config_menu_id(menu_id) or is_protected_runtime_config_xmlid(node_menu_xmlid(node)):
                return True
            if stats.get("config_only"):
                return False
            try:
                if int(menu_id or 0) in {727, 729, 735, 770}:
                    return False
            except Exception:
                pass
            fingerprint = "/".join(
                str(value or "").strip()
                for value in (
                    node.get("key"),
                    node.get("name"),
                    node.get("label"),
                    node.get("title"),
                    node.get("menu_xmlid"),
                    node.get("model"),
                    meta.get("menu_xmlid"),
                    meta.get("model"),
                )
                if str(value or "").strip()
            )
            if any(token in fingerprint for token in _PROTECTED_NODE_EXCLUDED_FINGERPRINT_TOKENS):
                return False
            if str(node.get("delivery_bucket") or meta.get("delivery_bucket") or "").strip() == "delivery_business_config":
                return True
            if str(node.get("model") or meta.get("model") or "").strip() == MENU_CONFIG_POLICY_MODEL:
                return True
            return False

        def apply_node(node: dict) -> dict | None:
            normalized_menu_id = node_menu_id(node)
            children = node.get("children")
            policy = policies_by_menu.get(normalized_menu_id)
            policy_matched_by_label = False
            if not policy and not stats.get("config_only"):
                labels = [
                    str(node.get("name") or "").strip(),
                    str(node.get("label") or "").strip(),
                    str(node.get("title") or "").strip(),
                ]
                policy = next((policies_by_label.get(label) for label in labels if label in policies_by_label), None)
                policy_matched_by_label = bool(policy)
            if policy:
                stats["applied_count"] += 1
                skip_policy_effects = False
                if not policy_visible(policy):
                    if not stats.get("config_only") and policy_matched_by_label and isinstance(children, list) and children:
                        stats["protected_count"] += 1
                    elif is_protected_runtime_config_node(node):
                        stats["protected_count"] += 1
                        skip_policy_effects = True
                    else:
                        stats["hidden_count"] += 1
                        return None
                if not skip_policy_effects:
                    custom_label = policy_custom_label(policy)
                    if custom_label:
                        node["name"] = custom_label
                        node["label"] = custom_label
                        node["title"] = custom_label
                        stats["renamed_count"] += 1
                    sequence = policy_sequence_override(policy)
                    if sequence:
                        node["sequence"] = sequence
                        stats["reordered_count"] += 1
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

        def policy_for_node(node: dict):
            normalized_menu_id = node_menu_id(node)
            policy = policies_by_menu.get(normalized_menu_id)
            if policy:
                return policy
            if stats.get("config_only"):
                return None
            labels = [
                str(node.get("name") or "").strip(),
                str(node.get("label") or "").strip(),
                str(node.get("title") or "").strip(),
            ]
            return next((policies_by_label.get(label) for label in labels if label in policies_by_label), None)

        def prune_unconfigured_nodes(nodes: list[dict], *, depth: int = 0) -> list[dict]:
            if not stats.get("config_only"):
                return nodes
            kept = []
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                next_node = dict(node)
                children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
                next_children = prune_unconfigured_nodes(children, depth=depth + 1) if children else []
                if children:
                    next_node["children"] = sort_children(next_children)
                policy = policy_for_node(next_node)
                configured_visible = bool(
                    policy
                    and (
                        policy_visible(policy)
                        or policy_recoverable_in_config_only(_to_int(node_menu_id(next_node)), policy)
                    )
                )
                protected = is_protected_runtime_config_node(next_node)
                if configured_visible or protected:
                    kept.append(next_node)
                    continue
                stats["unconfigured_hidden_count"] += 1
            return sort_children(kept)

        def prune_unconfigured_flat(nodes: list[dict]) -> list[dict]:
            if not stats.get("config_only"):
                return nodes
            kept = []
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                policy = policy_for_node(node)
                if (policy and policy_visible(policy)) or is_protected_runtime_config_node(node):
                    kept.append(node)
            return kept

        def sort_children(nodes: list[dict]) -> list[dict]:
            nodes.sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
            return nodes

        def node_matches_menu(node: dict, menu) -> bool:
            if not menu:
                return False
            menu_id = int(menu.id)
            normalized_menu_id = node_menu_id(node)
            if normalized_menu_id:
                return normalized_menu_id == menu_id
            labels = {
                str(node.get("name") or "").strip(),
                str(node.get("label") or "").strip(),
                str(node.get("title") or "").strip(),
            }
            return bool(str(menu.name or "").strip() in labels)

        def node_matches_policy_source(node: dict, menu_id: int, source_menu, source_label: str) -> bool:
            normalized_menu_id = node_menu_id(node)
            if normalized_menu_id:
                return normalized_menu_id == int(menu_id or 0)
            if stats.get("config_only"):
                return False
            if node_matches_menu(node, source_menu):
                return True
            labels = {
                str(node.get("name") or "").strip(),
                str(node.get("label") or "").strip(),
                str(node.get("title") or "").strip(),
            }
            return bool(source_label and source_label in labels)

        def menu_action_metadata(menu) -> dict:
            action_ref = str(menu.action or "").strip()
            if not action_ref:
                return {
                    "route": "/m/%s" % int(menu.id),
                }
            action_model = ""
            action_id = 0
            match = re.match(r"^([a-zA-Z0-9_.]+)\((\d+),?\)$", action_ref)
            if match:
                action_model = match.group(1)
                action_id = _to_int(match.group(2))
            elif "," in action_ref:
                action_model, action_id_text = action_ref.split(",", 1)
                action_id = _to_int(action_id_text)
            if not action_model:
                return {
                    "action_ref": action_ref,
                    "route": "/m/%s" % int(menu.id),
                }
            meta = {
                "action_ref": action_ref,
                "action_type": action_model,
            }
            if action_model == "ir.actions.act_window" and action_id:
                action = self.env["ir.actions.act_window"].sudo().browse(action_id).exists()
                meta.update({
                    "route": "/a/%s?menu_id=%s" % (action_id, int(menu.id)),
                    "action_id": action_id,
                    "model": str(action.res_model or "") if action else "",
                    "view_modes": [item.strip() for item in str(action.view_mode or "").split(",") if item.strip()] if action else [],
                })
            else:
                meta["route"] = "/m/%s" % int(menu.id)
            return meta

        visible_menu_ids_cache = None

        def visible_menu_ids_for_user() -> set[int] | None:
            nonlocal visible_menu_ids_cache
            if visible_menu_ids_cache is not None:
                return visible_menu_ids_cache
            try:
                menu_env = self.env(user=user)["ir.ui.menu"] if user else self.env["ir.ui.menu"]
                try:
                    visible_menu_ids_cache = {int(menu_id) for menu_id in menu_env._visible_menu_ids(debug=False)}
                except TypeError:
                    visible_menu_ids_cache = {int(menu_id) for menu_id in menu_env._visible_menu_ids()}
            except Exception:
                visible_menu_ids_cache = None
            return visible_menu_ids_cache

        def menu_visible_to_user(menu) -> bool:
            visible_ids = visible_menu_ids_for_user()
            if visible_ids is None:
                return True
            try:
                return int(menu.id or 0) in visible_ids
            except Exception:
                return False

        def policy_recoverable_in_config_only(menu_id: int, policy) -> bool:
            if (
                not stats.get("config_only")
                or runtime_source != MENU_CONFIG_RUNTIME_SOURCE_CONTRACT
                or not policy
            ):
                return False
            return is_config_only_recovery_menu_id(menu_id)

        def is_configured_structural_group(menu, policy) -> bool:
            if not policy or not policy_visible(policy):
                return False
            try:
                if str(menu.action or "").strip():
                    return False
            except Exception:
                return False
            try:
                groups = getattr(menu, "groups_id", None)
                if groups and len(groups):
                    return False
            except Exception:
                return False
            return True

        def complete_overlay_navigation_contract(node: dict, action_meta: dict) -> dict:
            menu_id = int(node.get("menu_id") or 0)
            route = str(action_meta.get("route") or node.get("route") or "").strip()
            action_id = _to_int(action_meta.get("action_id") or node.get("action_id"))
            model = str(action_meta.get("model") or node.get("model") or "").strip()
            view_modes_raw = action_meta.get("view_modes") or node.get("view_modes") or []
            if isinstance(view_modes_raw, (list, tuple)):
                view_modes = [str(item).strip() for item in view_modes_raw if str(item).strip()]
            else:
                view_modes = [item.strip() for item in str(view_modes_raw or "").split(",") if item.strip()]
            native_view_mode = ",".join(view_modes)

            node["is_visible"] = True
            node["scene_key"] = None
            node["native_action_id"] = action_id or None
            node["native_model"] = model or None
            node["native_view_mode"] = native_view_mode or None
            node["confidence"] = "medium"

            if action_id:
                node["target_type"] = "action"
                node["delivery_mode"] = "custom_action"
                node["is_clickable"] = True
                node["compatibility_used"] = True
                node["target"] = {
                    "action_id": action_id,
                    "res_model": model or None,
                    "view_mode": native_view_mode or None,
                }
                node["entry_target"] = {
                    "type": "compatibility",
                    "route": route or "/a/%s?menu_id=%s" % (action_id, menu_id),
                    "compatibility_refs": {
                        "menu_id": menu_id,
                        "action_id": action_id,
                        "model": model or None,
                        "view_modes": view_modes,
                    },
                }
                node["active_match"] = {
                    "menu_id": menu_id,
                    "scene_key": None,
                    "action_id": action_id,
                    "route_prefix": "/a/%s" % action_id,
                }
                node["availability_status"] = "ok"
                node["reason_code"] = ""
            else:
                node["target_type"] = "directory"
                node["delivery_mode"] = "none"
                node["is_clickable"] = False
                node["compatibility_used"] = False
                node["target"] = {}
                node["entry_target"] = {
                    "type": "directory",
                    "route": route or "/m/%s" % menu_id,
                }
                node["active_match"] = {
                    "menu_id": menu_id,
                    "scene_key": None,
                    "action_id": None,
                    "route_prefix": route or "/m/%s" % menu_id,
                }
                node["availability_status"] = "ok"
                node["reason_code"] = "DIRECTORY_ONLY"
            return node

        def build_missing_menu_node(menu, policy=None, seen: set[int] | None = None) -> dict | None:
            menu = menu.exists()
            if not menu:
                return None
            menu_id = int(menu.id or 0)
            seen = set(seen or set())
            policy = policy if policy is not None else policies_by_menu.get(menu_id)
            if menu_id in seen:
                return None
            seen.add(menu_id)
            protected_config_menu = is_protected_runtime_config_menu_id(menu_id)
            recoverable_config_menu = policy_recoverable_in_config_only(menu_id, policy)
            structural_container = bool(policy and is_configured_structural_group(menu, policy))
            if stats.get("config_only") and not policy and not protected_config_menu:
                return None
            if (
                policy
                and not policy_visible(policy)
                and not protected_config_menu
                and not recoverable_config_menu
                and not structural_container
            ):
                return None
            label = policy_custom_label(policy) if policy else ""
            label = label or str(menu.name or "").strip()
            if not label:
                return None
            action_meta = menu_action_metadata(menu)
            sequence = policy_sequence_override(policy) if policy else 0
            sequence = sequence or int(menu.sequence or 0)
            meta = {
                "source": MENU_CONFIG_RUNTIME_SOURCE_POLICY,
                "menu_id": int(menu.id),
                "menu_xmlid": "",
                "parent_menu_id": int(menu.parent_id.id or 0) if menu.parent_id else 0,
                "parent_menu_label": str(menu.parent_id.name or "") if menu.parent_id else "",
                "source_authority": self._source_contract(runtime_source=runtime_source),
                **action_meta,
            }
            node = {
                "key": "menu_config_policy:%s" % int(menu.id),
                "label": label,
                "title": label,
                "name": label,
                "menu_id": int(menu.id),
                "parent_id": int(menu.parent_id.id or 0) if menu.parent_id else 0,
                "sequence": sequence,
                "children": [],
                "meta": meta,
            }
            if action_meta.get("route"):
                node["route"] = action_meta["route"]
            if action_meta.get("action_id"):
                node["action_id"] = action_meta["action_id"]
            if action_meta.get("model"):
                node["model"] = action_meta["model"]
            if action_meta.get("view_modes"):
                node["view_modes"] = action_meta["view_modes"]
            return complete_overlay_navigation_contract(node, action_meta)

        def remove_node(nodes: list[dict], menu_id: int, source_menu=None, source_label: str = "") -> tuple[list[dict], dict | None]:
            removed = None
            next_nodes = []
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if node_matches_policy_source(node, menu_id, source_menu, source_label):
                    if removed is None:
                        removed = node
                    continue
                children = node.get("children") if isinstance(node.get("children"), list) else []
                if children:
                    next_children, child_removed = remove_node(children, menu_id, source_menu, source_label)
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

        def contains_policy_source(nodes: list[dict], menu_id: int, source_menu=None, source_label: str = "") -> bool:
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if node_matches_policy_source(node, menu_id, source_menu, source_label):
                    return True
                children = node.get("children") if isinstance(node.get("children"), list) else []
                if children and contains_policy_source(children, menu_id, source_menu, source_label):
                    return True
            return False

        def effective_parent_menu(menu):
            try:
                menu_id = int(menu.id or 0)
            except Exception:
                menu_id = 0
            policy = policies_by_menu.get(menu_id)
            configured_parent = policy_target_parent(policy) if policy else self.env["ir.ui.menu"].browse(0)
            if configured_parent and configured_parent.exists() and int(configured_parent.id or 0) != menu_id:
                return configured_parent
            return menu.parent_id

        def visible_parent_menu(nodes: list[dict], menu):
            parent = effective_parent_menu(menu)
            seen = {int(menu.id or 0)}
            while parent and parent.exists() and int(parent.id or 0) not in seen:
                parent_id = int(parent.id or 0)
                seen.add(parent_id)
                parent_policy = policies_by_menu.get(parent_id)
                if parent_policy and (policy_visible(parent_policy) or is_protected_runtime_config_menu_id(parent_id)):
                    return parent
                if node_matches_any_menu(nodes, parent):
                    return parent
                parent = effective_parent_menu(parent)
            return self.env["ir.ui.menu"].browse(0)

        def ensure_menu_present(nodes: list[dict], menu) -> list[dict]:
            menu = menu.exists() if menu else menu
            if not menu or node_matches_any_menu(nodes, menu):
                return nodes
            parent = visible_parent_menu(nodes, menu)
            if parent and parent.exists() and int(parent.id or 0) != int(menu.id or 0):
                nodes = ensure_menu_present(nodes, parent)
            policy = policies_by_menu.get(int(menu.id or 0))
            node = build_missing_menu_node(menu, policy)
            if node is None:
                return nodes
            if parent and parent.exists() and int(parent.id or 0) != int(menu.id or 0):
                nodes, inserted = insert_node(nodes, parent, node)
                if inserted:
                    return sort_children(nodes)
            return sort_children(nodes + [node])

        def node_matches_any_menu(nodes: list[dict], menu) -> bool:
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                if node_matches_menu(node, menu):
                    return True
                children = node.get("children") if isinstance(node.get("children"), list) else []
                if children and node_matches_any_menu(children, menu):
                    return True
            return False

        def apply_moves(nodes: list[dict]) -> list[dict]:
            next_nodes = nodes
            for move in move_targets:
                target_menu = move["target_menu"]
                next_nodes = ensure_menu_present(next_nodes, target_menu)
                next_nodes, moved_node = remove_node(
                    next_nodes,
                    int(move["menu_id"]),
                    move["source_menu"],
                    str(move["source_label"] or ""),
                )
                if moved_node is None:
                    if contains_policy_source(
                        next_nodes,
                        int(move["menu_id"]),
                        move["source_menu"],
                        str(move["source_label"] or ""),
                    ):
                        continue
                    policy = policies_by_menu.get(int(move["menu_id"]))
                    moved_node = build_missing_menu_node(move["source_menu"], policy)
                    if moved_node is None:
                        continue
                next_nodes, inserted = insert_node(next_nodes, target_menu, moved_node)
                if inserted:
                    stats["moved_count"] += 1
                else:
                    next_nodes.append(moved_node)
            return sort_children(next_nodes)

        def materialize_visible_configured_nodes(nodes: list[dict]) -> list[dict]:
            next_nodes = nodes
            visible_policies = [
                (int(menu_id), policy)
                for menu_id, policy in policies_by_menu.items()
                if (
                    policy_visible(policy)
                    or is_protected_runtime_config_menu_id(menu_id)
                    or policy_recoverable_in_config_only(menu_id, policy)
                )
                and policy_menu_exists(policy)
            ]
            visible_policies.sort(key=lambda item: (
                menu_depth(policy_menu_record(item[1])),
                int(item[0] or 0),
            ))
            for _menu_id, policy in visible_policies:
                next_nodes = ensure_menu_present(next_nodes, policy_menu_record(policy))
            protected_menus = [
                self.env["ir.ui.menu"].browse(menu_id).exists()
                for menu_id in protected_config_menu_xmlids_by_id()
                if is_protected_runtime_config_menu_id(menu_id)
            ]
            protected_menus = [menu for menu in protected_menus if menu]
            protected_menus.sort(key=lambda menu: (menu_depth(menu), int(menu.id or 0)))
            for menu in protected_menus:
                next_nodes = ensure_menu_present(next_nodes, menu)
            return sort_children(next_nodes)

        def align_visible_configured_parentage(nodes: list[dict]) -> list[dict]:
            next_nodes = nodes
            visible_policies = [
                (int(menu_id), policy)
                for menu_id, policy in policies_by_menu.items()
                if (
                    policy_visible(policy)
                    or is_protected_runtime_config_menu_id(menu_id)
                    or policy_recoverable_in_config_only(menu_id, policy)
                )
                and policy_menu_exists(policy)
            ]
            visible_policies.sort(key=lambda item: (
                menu_depth(policy_menu_record(item[1])),
                int(item[0] or 0),
            ))
            for menu_id, policy in visible_policies:
                source_menu = policy_menu_record(policy)
                parent = visible_parent_menu(next_nodes, source_menu)
                if not parent or not parent.exists() or int(parent.id or 0) == int(menu_id):
                    continue
                next_nodes = ensure_menu_present(next_nodes, parent)
                next_nodes, moved_node = remove_node(
                    next_nodes,
                    menu_id,
                    source_menu,
                    policy_menu_name(policy),
                )
                if moved_node is None:
                    moved_node = build_missing_menu_node(source_menu, policy)
                    if moved_node is None:
                        continue
                actual_parent_id = _to_int(moved_node.get("parent_id"))
                moved_meta = moved_node.get("meta") if isinstance(moved_node.get("meta"), dict) else {}
                actual_parent_id = _to_int(moved_meta.get("parent_menu_id")) or actual_parent_id
                next_nodes, inserted = insert_node(next_nodes, parent, moved_node)
                if inserted and actual_parent_id != int(parent.id or 0):
                    stats["parent_aligned_count"] += 1
                elif not inserted:
                    next_nodes.append(moved_node)
            return sort_children(next_nodes)

        out = dict(nav_fact)
        applied_flat = [
            applied
            for node in out.get("flat", [])
            if isinstance(node, dict)
            for applied in [apply_node(dict(node))]
            if applied is not None
        ]
        out["flat"] = prune_unconfigured_flat(applied_flat)
        out["flat"].sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
        applied_tree = [
            applied
            for node in out.get("tree", [])
            if isinstance(node, dict)
            for applied in [apply_node(dict(node))]
            if applied is not None
        ]
        out["tree"] = align_visible_configured_parentage(
            materialize_visible_configured_nodes(apply_moves(prune_unconfigured_nodes(applied_tree)))
        )
        return out, stats
