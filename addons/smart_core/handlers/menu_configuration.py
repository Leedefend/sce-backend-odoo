# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any

from odoo.exceptions import AccessError, ValidationError

from ..core.base_handler import BaseIntentHandler
from ..utils.backend_contract_boundaries import (
    LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
    MENU_CONFIG_INTENTS,
    MENU_CONFIG_POLICY_MODEL,
    MENU_CONFIG_RUNTIME_SOURCE_CONTRACT,
    MENU_CONFIG_RUNTIME_SOURCE_POLICY,
    MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
    ensure_menu_orchestration_source_status,
)
from ..utils.extension_hooks import call_extension_hook_first


BUSINESS_CONFIG_GROUP = "smart_core.group_smart_core_business_config_admin"
PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"
_logger = logging.getLogger(__name__)


def _to_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _m2o_payload(record) -> dict | None:
    if not record:
        return None
    return {"id": int(record.id), "name": _to_text(record.display_name or record.name)}


def _menu_action_value(action: Any) -> str:
    if not action:
        return ""
    if isinstance(action, str):
        return _to_text(action)
    model_name = _to_text(getattr(action, "_name", ""))
    action_id = _to_int(getattr(action, "id", 0))
    if model_name and action_id:
        return "%s,%s" % (model_name, action_id)
    return _to_text(action)


def _xmlid_record(env, xmlid: str):
    try:
        return env.ref(xmlid, raise_if_not_found=False)
    except Exception:
        return None


def _menu_config_contract_name(company_id: int) -> str:
    return "menu.config.company.%s" % int(company_id or 0)


def _business_menu_scope_group_label(group) -> str:
    label = _to_text(group.display_name or group.name)
    for prefix in (
        "Smart Construction / SC 角色 - ",
        "Smart Construction / 角色-",
        "Smart Construction / ",
        "SC 角色 - ",
        "角色-",
    ):
        if label.startswith(prefix):
            label = label[len(prefix):].strip()
    return label or _to_text(group.name)


def _menu_policy_contract_row(policy) -> dict:
    menu = policy.menu_id
    target_parent = policy.target_parent_menu_id
    return {
        "policy_id": int(policy.id),
        "menu_id": int(menu.id or 0) if menu else 0,
        "menu_label": _to_text(getattr(menu, "name", "")) if menu else "",
        "menu_complete_name": _to_text(getattr(menu, "complete_name", "")) if menu else "",
        "target_parent_menu_id": int(target_parent.id or 0) if target_parent else 0,
        "target_parent_label": _to_text(getattr(target_parent, "complete_name", "")) if target_parent else "",
        "custom_label": _to_text(policy.custom_label),
        "sequence_override": int(policy.sequence_override or 0),
        "visible": bool(policy.visible),
        "active": bool(policy.active),
        "role_group_ids": [int(group.id) for group in policy.role_group_ids],
        "role_group_names": [_to_text(group.display_name or group.name) for group in policy.role_group_ids],
        "effect_summary": _to_text(policy.effect_summary),
        "scope_summary": _to_text(policy.scope_summary),
    }


def _menu_config_contract_json(company_id: int, policies) -> dict:
    rows = [_menu_policy_contract_row(policy) for policy in policies]
    return {
        "menu_orchestration": {
            "schema_version": "menu_orchestration.v1",
            "source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
            "source_status": LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
            "runtime_source": MENU_CONFIG_RUNTIME_SOURCE_POLICY,
            "company_id": int(company_id or 0),
            "policies": rows,
            "policy_count": len(rows),
        }
    }


def _menu_config_contract_json_from_rows(company_id: int, rows: list[dict]) -> dict:
    return {
        "menu_orchestration": {
            "schema_version": "menu_orchestration.v1",
            "source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
            "source_status": LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
            "runtime_source": MENU_CONFIG_RUNTIME_SOURCE_POLICY,
            "company_id": int(company_id or 0),
            "policies": rows,
            "policy_count": len(rows),
        }
    }


def _menu_orchestration_policies(contract_json: dict) -> list[dict]:
    if not isinstance(contract_json, dict):
        return []
    orchestration = contract_json.get("menu_orchestration")
    if not isinstance(orchestration, dict):
        return []
    if str(orchestration.get("schema_version") or "").strip() != "menu_orchestration.v1":
        return []
    policies = orchestration.get("policies")
    return policies if isinstance(policies, list) else []


def _menu_orchestration_summary(contract_json: dict) -> dict:
    rows = [row for row in _menu_orchestration_policies(contract_json) if isinstance(row, dict)]
    return {
        "policy_count": len(rows),
        "hidden_count": sum(1 for row in rows if not _to_bool(row.get("visible"), True)),
        "renamed_count": sum(1 for row in rows if bool(_to_text(row.get("custom_label")))),
        "reordered_count": sum(1 for row in rows if bool(_to_int(row.get("sequence_override")))),
        "moved_count": sum(1 for row in rows if bool(_to_int(row.get("target_parent_menu_id")))),
        "active_count": sum(1 for row in rows if _to_bool(row.get("active"), True)),
    }


class MenuConfigurationLoadHandler(BaseIntentHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["panel_get"]
    DESCRIPTION = "读取菜单配置面板数据"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_menu_config_panel_projection"
    SOURCE_AUTHORITIES = ("ir.ui.menu", MENU_CONFIG_POLICY_MODEL, "res.groups")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _ensure_access(self):
        user = self.env.user
        if user.has_group(BUSINESS_CONFIG_GROUP) or user.has_group(PLATFORM_ADMIN_GROUP):
            return
        raise AccessError("只有业务配置管理员或平台管理员可以配置菜单。")

    def _company_id(self, params: dict) -> int:
        return _to_int(params.get("company_id")) or int(self.env.company.id or 0)

    def _requested_menu_ids(self, params: dict) -> list[int]:
        raw = params.get("menu_ids") or params.get("menuIds") or []
        if not isinstance(raw, list):
            return []
        ids: list[int] = []
        for item in raw:
            menu_id = _to_int(item)
            if menu_id and menu_id not in ids:
                ids.append(menu_id)
        return ids

    def _root_menu_id(self, params: dict) -> int:
        root_menu_id = _to_int(params.get("root_menu_id") or params.get("rootMenuId"))
        if root_menu_id:
            return root_menu_id
        root_menu_xmlid = _to_text(params.get("root_menu_xmlid") or params.get("rootMenuXmlid"))
        if not root_menu_xmlid:
            return 0
        menu = _xmlid_record(self.env, root_menu_xmlid)
        if menu and getattr(menu, "_name", "") == "ir.ui.menu":
            return int(menu.id or 0)
        return 0

    def _default_business_root_menu_id(self) -> int:
        hook_xmlid = call_extension_hook_first(self.env, "smart_core_business_root_menu_xmlid", self.env)
        hook_xmlid = _to_text(hook_xmlid)
        if hook_xmlid and hasattr(self.env, "ref"):
            menu = _xmlid_record(self.env, hook_xmlid)
            if menu and getattr(menu, "_name", "ir.ui.menu") == "ir.ui.menu":
                return int(menu.id or 0)
        try:
            root_menu_xmlid = str(
                self.env["ir.config_parameter"].sudo().get_param("smart_core.business_root_menu_xmlid", "") or ""
            ).strip()
        except Exception:
            root_menu_xmlid = ""
        if root_menu_xmlid and hasattr(self.env, "ref"):
            menu = _xmlid_record(self.env, root_menu_xmlid)
            if menu and getattr(menu, "_name", "ir.ui.menu") == "ir.ui.menu":
                return int(menu.id or 0)
        return 0

    def _scope_root_menu_id(self, params: dict | None = None) -> int:
        params = params if isinstance(params, dict) else {}
        return self._root_menu_id(params) or self._default_business_root_menu_id()

    def _menu_under_root(self, menu, root_menu_id: int) -> bool:
        root_menu_id = _to_int(root_menu_id)
        if not root_menu_id:
            return True
        current = menu.exists() if menu and hasattr(menu, "exists") else menu
        seen: set[int] = set()
        while current:
            menu_id = _to_int(getattr(current, "id", 0))
            if not menu_id or menu_id in seen:
                return False
            if menu_id == root_menu_id:
                return True
            seen.add(menu_id)
            current = getattr(current, "parent_id", None)
        return False

    def _policy_in_menu_config_scope(self, policy, root_menu_id: int) -> bool:
        root_menu_id = _to_int(root_menu_id)
        if not root_menu_id:
            return True
        menu = getattr(policy, "menu_id", None)
        if not menu or not self._menu_under_root(menu, root_menu_id):
            return False
        formal_scope_ids = self._formal_product_menu_scope_ids(root_menu_id)
        if formal_scope_ids and _to_int(getattr(menu, "id", 0)) not in formal_scope_ids:
            return False
        target_parent = getattr(policy, "target_parent_menu_id", None)
        if target_parent and not self._menu_under_root(target_parent, root_menu_id):
            return False
        if formal_scope_ids and target_parent and _to_int(getattr(target_parent, "id", 0)) not in formal_scope_ids:
            return False
        return True

    def _policies_in_menu_config_scope(self, policies, root_menu_id: int):
        if not _to_int(root_menu_id):
            return policies
        if hasattr(policies, "filtered"):
            return policies.filtered(lambda policy: self._policy_in_menu_config_scope(policy, root_menu_id))
        return [policy for policy in policies if self._policy_in_menu_config_scope(policy, root_menu_id)]

    def _ensure_menu_config_scope(self, menu_id: int, root_menu_id: int, *, field_label: str = "菜单"):
        menu_id = _to_int(menu_id)
        root_menu_id = _to_int(root_menu_id)
        if not menu_id or not root_menu_id:
            return
        menu = self.env["ir.ui.menu"].sudo().with_context(active_test=False).browse(menu_id).exists()
        if not menu or not self._menu_under_root(menu, root_menu_id):
            raise ValidationError("%s超出菜单配置范围，只能配置当前业务根菜单下的业务办理菜单。" % field_label)
        formal_scope_ids = self._formal_product_menu_scope_ids(root_menu_id)
        if formal_scope_ids and menu_id not in formal_scope_ids:
            raise ValidationError("%s超出正式产品菜单范围，只能配置当前产品已发布菜单。" % field_label)

    def _scope_contract_json(self, company_id: int, contract_json: dict) -> dict:
        root_menu_id = self._scope_root_menu_id({})
        scoped_rows = []
        for row in _menu_orchestration_policies(contract_json):
            if not isinstance(row, dict):
                continue
            menu_id = _to_int(row.get("menu_id"))
            if not menu_id:
                continue
            try:
                self._ensure_menu_config_scope(menu_id, root_menu_id)
                target_parent_id = _to_int(row.get("target_parent_menu_id"))
                if target_parent_id:
                    self._ensure_menu_config_scope(target_parent_id, root_menu_id, field_label="上级菜单")
            except ValidationError:
                _logger.debug(
                    "MENU_CONFIG_POLICY_FILTERED_OUT_OF_SCOPE menu_id=%s target_parent_menu_id=%s root_menu_id=%s",
                    menu_id,
                    _to_int(row.get("target_parent_menu_id")),
                    root_menu_id,
                )
                continue
            scoped_rows.append(dict(row))
        return ensure_menu_orchestration_source_status(
            _menu_config_contract_json_from_rows(company_id, scoped_rows),
            LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
        )

    def _menu_subtree_ids(self, menus, root_menu_id: int) -> list[int]:
        root_menu_id = _to_int(root_menu_id)
        if not root_menu_id:
            return []
        by_parent: dict[int, list[int]] = {}
        all_ids: set[int] = set()
        for menu in menus:
            menu_id = _to_int(getattr(menu, "id", 0))
            if not menu_id:
                continue
            all_ids.add(menu_id)
            parent_id = _to_int(getattr(getattr(menu, "parent_id", None), "id", 0))
            by_parent.setdefault(parent_id, []).append(menu_id)
        if root_menu_id not in all_ids:
            return []
        scoped_ids = {root_menu_id}
        stack = list(by_parent.get(root_menu_id, []))
        while stack:
            menu_id = stack.pop()
            if menu_id in scoped_ids:
                continue
            scoped_ids.add(menu_id)
            stack.extend(by_parent.get(menu_id, []))
        return sorted(scoped_ids)

    def _current_product_key(self) -> str:
        identity = call_extension_hook_first(self.env, "smart_core_resolve_startup_delivery_identity", self.env, {})
        if isinstance(identity, dict):
            product_key = _to_text(identity.get("product_key"))
            if product_key:
                return product_key
        return "construction.standard"

    def _formal_product_menu_scope_ids(self, root_menu_id: int) -> set[int]:
        if "sc.product.policy" not in self.env:
            return set()
        product_key = self._current_product_key()
        policy = self.env["sc.product.policy"].sudo().search([
            ("product_key", "=", product_key),
            ("active", "=", True),
        ], limit=1)
        if not policy:
            return set()
        Menu = self.env["ir.ui.menu"].sudo().with_context(active_test=False)
        ConfigPolicy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False) if MENU_CONFIG_POLICY_MODEL in self.env else None
        configured_target_by_menu: dict[int, int] = {}
        if ConfigPolicy is not None:
            for row in ConfigPolicy.search([
                ("company_id", "=", int(self.env.company.id or 0)),
                ("active", "=", True),
                ("menu_id", "!=", False),
                ("target_parent_menu_id", "!=", False),
            ]):
                configured_target_by_menu[int(row.menu_id.id)] = int(row.target_parent_menu_id.id)
        scoped_ids: set[int] = set()

        def add_menu_with_parent_chain(menu) -> None:
            while menu:
                current_id = _to_int(getattr(menu, "id", 0))
                if not current_id:
                    break
                scoped_ids.add(current_id)
                if root_menu_id and current_id == root_menu_id:
                    break
                menu = getattr(menu, "parent_id", None)

        for group in policy.menu_groups or []:
            if not isinstance(group, dict):
                continue
            group_label = _to_text(group.get("group_label") or group.get("label") or group.get("group_key"))
            if root_menu_id and group_label:
                group_menu = Menu.search([
                    ("parent_id", "=", root_menu_id),
                    ("name", "=", group_label),
                ], limit=1)
                if group_menu:
                    scoped_ids.add(int(group_menu.id))
            for item in group.get("menus") or []:
                if not isinstance(item, dict):
                    continue
                if item.get("enabled") is False or _to_text(item.get("release_state")) not in {"", "released"}:
                    continue
                menu_id = _to_int(item.get("menu_id"))
                if not menu_id:
                    continue
                menu = Menu.browse(menu_id).exists()
                target_parent_id = configured_target_by_menu.get(menu_id)
                if target_parent_id:
                    if menu:
                        scoped_ids.add(int(menu.id))
                    target_parent = Menu.browse(target_parent_id).exists()
                    add_menu_with_parent_chain(target_parent)
                else:
                    add_menu_with_parent_chain(menu)
        if root_menu_id:
            scoped_ids.add(root_menu_id)
        return scoped_ids

    def _menu_config_candidate_ids(self, root_menu_id: int, requested_menu_ids: list[int], all_menus) -> set[int]:
        requested_set = {int(menu_id) for menu_id in requested_menu_ids if int(menu_id or 0)}
        formal_scope_ids = self._formal_product_menu_scope_ids(root_menu_id)
        if formal_scope_ids:
            return requested_set & formal_scope_ids if requested_set else set(formal_scope_ids)
        if requested_set:
            return set(requested_set)
        return set(self._menu_subtree_ids(all_menus, root_menu_id))

    def _expand_with_parent_ids(self, menus) -> list[int]:
        ids = set(int(menu.id) for menu in menus)
        parent = menus.mapped("parent_id")
        while parent:
            next_parent = self.env["ir.ui.menu"].sudo()
            for menu in parent:
                menu_id = int(menu.id or 0)
                if not menu_id or menu_id in ids:
                    continue
                ids.add(menu_id)
                if menu.parent_id:
                    next_parent |= menu.parent_id
            parent = next_parent
        return sorted(ids)

    def _xmlids_by_id(self, model_name: str, ids: list[int]) -> dict[int, str]:
        if not ids:
            return {}
        rows = self.env["ir.model.data"].sudo().search([
            ("model", "=", model_name),
            ("res_id", "in", ids),
        ])
        out: dict[int, str] = {}
        for row in rows:
            res_id = int(row.res_id or 0)
            out.setdefault(res_id, "%s.%s" % (row.module, row.name))
        return out

    def _serialize_menu(self, menu, xmlids: dict[int, str]) -> dict:
        action = _menu_action_value(getattr(menu, "action", ""))
        return {
            "id": int(menu.id),
            "menu_id": int(menu.id),
            "name": _to_text(menu.name),
            "display_name": _to_text(menu.display_name),
            "complete_name": _to_text(menu.complete_name),
            "parent_id": int(menu.parent_id.id or 0) if menu.parent_id else 0,
            "parent_name": _to_text(menu.parent_id.display_name or menu.parent_id.name) if menu.parent_id else "",
            "sequence": int(menu.sequence or 0),
            "action": action,
            "web_icon": _to_text(getattr(menu, "web_icon", "")),
            "xmlid": xmlids.get(int(menu.id), ""),
            "group_ids": [int(group.id) for group in menu.groups_id],
            "group_names": [_to_text(group.display_name or group.name) for group in menu.groups_id],
            "children": [],
        }

    def _effective_menu_rows(self, rows: list[dict], policy_by_menu: dict[int, dict]) -> list[dict]:
        by_id = {int(row["id"]): dict(row) for row in rows}
        for menu_id, policy in policy_by_menu.items():
            row = by_id.get(int(menu_id or 0))
            if not row:
                continue
            target_parent_id = _to_int(policy.get("target_parent_menu_id"))
            if target_parent_id and target_parent_id != int(row.get("id") or 0):
                target_parent = by_id.get(target_parent_id)
                row["parent_id"] = target_parent_id
                row["parent_name"] = _to_text(target_parent.get("complete_name") or target_parent.get("name")) if target_parent else ""
            custom_label = _to_text(policy.get("custom_label"))
            if custom_label:
                row["name"] = custom_label
                row["display_name"] = custom_label
            sequence = _to_int(policy.get("sequence_override"))
            if sequence:
                row["sequence"] = sequence
        return list(by_id.values())

    def _filter_rows_to_root_scope(self, rows: list[dict], root_menu_id: int) -> list[dict]:
        root_menu_id = _to_int(root_menu_id)
        if not root_menu_id:
            return rows
        by_parent: dict[int, list[int]] = {}
        row_ids = set()
        for row in rows:
            row_id = _to_int(row.get("id") or row.get("menu_id"))
            if not row_id:
                continue
            row_ids.add(row_id)
            by_parent.setdefault(_to_int(row.get("parent_id")), []).append(row_id)
        if root_menu_id not in row_ids:
            return rows
        scoped_ids = {root_menu_id}
        stack = list(by_parent.get(root_menu_id, []))
        while stack:
            menu_id = stack.pop()
            if menu_id in scoped_ids:
                continue
            scoped_ids.add(menu_id)
            stack.extend(by_parent.get(menu_id, []))
        return [row for row in rows if _to_int(row.get("id") or row.get("menu_id")) in scoped_ids]

    def _build_tree(self, rows: list[dict]) -> list[dict]:
        by_id = {int(row["id"]): dict(row, children=[]) for row in rows}
        roots: list[dict] = []
        for row in by_id.values():
            parent_id = int(row.get("parent_id") or 0)
            parent = by_id.get(parent_id)
            if parent:
                parent.setdefault("children", []).append(row)
            else:
                roots.append(row)

        def sort_branch(items: list[dict]) -> list[dict]:
            items.sort(key=lambda item: (int(item.get("sequence") or 0), int(item.get("id") or 0)))
            for item in items:
                sort_branch(item.get("children") or [])
            return items

        return sort_branch(roots)

    def _serialize_policy(self, policy) -> dict:
        return {
            "id": int(policy.id),
            "menu_id": int(policy.menu_id.id or 0),
            "company_id": int(policy.company_id.id or 0),
            "target_parent_menu_id": int(policy.target_parent_menu_id.id or 0) if policy.target_parent_menu_id else 0,
            "custom_label": _to_text(policy.custom_label),
            "sequence_override": int(policy.sequence_override or 0),
            "visible": bool(policy.visible),
            "active": True,
            "role_group_ids": [int(group.id) for group in policy.role_group_ids],
            "note": _to_text(policy.note),
            "effect_summary": _to_text(policy.effect_summary),
            "scope_summary": _to_text(policy.scope_summary),
            "preview_summary": _to_text(policy.preview_summary),
        }

    def _group_option_records(self, menus, policies):
        del menus, policies
        groups = self.env["res.groups"].sudo().search([("sc_assignable_user_permission", "=", True)])
        return groups.sorted(key=lambda group: (
            _to_text(group.category_id.display_name or group.category_id.name) if group.category_id else "",
            _to_text(group.display_name or group.name),
            int(group.id or 0),
        ))

    def handle(self, payload=None, ctx=None):
        del ctx
        self._ensure_access()
        params = (payload or {}).get("params") if isinstance(payload, dict) else {}
        params = params if isinstance(params, dict) else {}
        company_id = self._company_id(params)

        Menu = self.env["ir.ui.menu"].sudo()
        MenuAll = Menu.with_context(active_test=False)
        requested_menu_ids = self._requested_menu_ids(params)
        explicit_requested_menu_ids = list(requested_menu_ids)
        root_menu_id = self._scope_root_menu_id(params)
        if root_menu_id and root_menu_id not in requested_menu_ids:
            requested_menu_ids.append(root_menu_id)
        if root_menu_id:
            requested_set = {int(menu_id) for menu_id in requested_menu_ids if int(menu_id or 0)}
            all_menus = MenuAll.search([], order="parent_id, sequence, id")
            candidate_ids = self._menu_config_candidate_ids(root_menu_id, explicit_requested_menu_ids, all_menus)
            policy_records = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False).search([
                ("company_id", "=", company_id),
                ("active", "=", True),
                ("menu_id", "!=", False),
                ("menu_id", "in", sorted(candidate_ids)),
            ])
            policy_records = self._policies_in_menu_config_scope(policy_records, root_menu_id)
            for policy in policy_records:
                menu_id = _to_int(getattr(getattr(policy, "menu_id", None), "id", 0))
                target_parent_id = _to_int(getattr(getattr(policy, "target_parent_menu_id", None), "id", 0))
                if not requested_set or menu_id in candidate_ids:
                    candidate_ids.add(menu_id)
                if target_parent_id:
                    candidate_ids.add(target_parent_id)
            requested_menus = MenuAll.browse(sorted(candidate_ids)).exists()
            menu_ids_with_parents = self._expand_with_parent_ids(requested_menus)
            menus = MenuAll.browse(menu_ids_with_parents).exists().sorted(
                key=lambda menu: (
                    int(menu.parent_id.id or 0) if menu.parent_id else 0,
                    int(menu.sequence or 0),
                    int(menu.id or 0),
                )
            )
        elif requested_menu_ids:
            policy_records = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False).search([
                ("company_id", "=", company_id),
                ("active", "=", True),
                ("menu_id", "!=", False),
                ("menu_id", "in", requested_menu_ids),
            ])
            target_parent_records = policy_records.mapped("target_parent_menu_id")
            target_parent_ids = getattr(target_parent_records, "ids", target_parent_records or [])
            requested_menus = MenuAll.browse(sorted(set(requested_menu_ids + target_parent_ids))).exists()
            menu_ids_with_parents = self._expand_with_parent_ids(requested_menus)
            menus = MenuAll.browse(menu_ids_with_parents).exists().sorted(
                key=lambda menu: (
                    int(menu.parent_id.id or 0) if menu.parent_id else 0,
                    int(menu.sequence or 0),
                    int(menu.id or 0),
                )
            )
        else:
            visible_ids = list(Menu.with_user(self.env.user)._visible_menu_ids())
            menus = Menu.search([("id", "in", visible_ids)], order="parent_id, sequence, id")
        menu_ids = [int(menu.id) for menu in menus]
        xmlids = self._xmlids_by_id("ir.ui.menu", menu_ids)
        menu_rows = [self._serialize_menu(menu, xmlids) for menu in menus]

        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        policies = Policy.search([
            ("company_id", "=", company_id),
            ("menu_id", "in", menu_ids),
        ], order="id desc")
        policies = self._policies_in_menu_config_scope(policies, root_menu_id)
        policy_by_menu: dict[int, dict] = {}
        for policy in policies:
            policy_by_menu.setdefault(int(policy.menu_id.id), self._serialize_policy(policy))

        effective_menu_rows = self._effective_menu_rows(menu_rows, policy_by_menu)
        effective_menu_rows = self._filter_rows_to_root_scope(effective_menu_rows, root_menu_id)
        scoped_menu_ids = {int(row["id"]) for row in effective_menu_rows}
        policy_by_menu = {
            menu_id: policy
            for menu_id, policy in policy_by_menu.items()
            if int(menu_id or 0) in scoped_menu_ids
        }

        groups = self._group_option_records(menus, policies)
        group_rows = [
            {
                "id": int(group.id),
                "name": _to_text(group.name),
                "display_name": _business_menu_scope_group_label(group),
                "category": "业务角色",
            }
            for group in groups
        ]

        return {
            "data": {
                "company": _m2o_payload(self.env["res.company"].sudo().browse(company_id)),
                "menus": effective_menu_rows,
                "tree": self._build_tree(effective_menu_rows),
                "policies": policy_by_menu,
                "groups": group_rows,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
                "menu_count": len(menu_rows),
                "policy_count": len(policy_by_menu),
                "scope_root_menu_id": root_menu_id,
                "scope_root_valid": bool(root_menu_id),
                "scoped_menu_count": len(effective_menu_rows),
                "requested_menu_count": len(requested_menu_ids),
                "group_option_count": len(group_rows),
            },
        }


class MenuConfigurationSaveHandler(MenuConfigurationLoadHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["panel_set"]
    DESCRIPTION = "保存菜单配置面板数据"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]
    ACL_MODE = "explicit_check"

    @classmethod
    def source_authority_contract(cls) -> dict:
        source = super().source_authority_contract()
        source.update({
            "kind": "ui_menu_config_panel_write_proxy",
            "write_proxy": True,
            "runtime_carrier": cls.INTENT_TYPE,
            "lowcode_boundary": "menu_config",
            "contract_source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
        })
        return source

    def _normalize_row(self, row: Any) -> dict:
        row = row if isinstance(row, dict) else {}
        return {
            "policy_id": _to_int(row.get("policy_id") or row.get("id")),
            "menu_id": _to_int(row.get("menu_id")),
            "target_parent_menu_id": _to_int(row.get("target_parent_menu_id")),
            "custom_label": _to_text(row.get("custom_label")),
            "sequence_override": int(row.get("sequence_override") or 0),
            "visible": _to_bool(row.get("visible"), True),
            "active": True,
            "role_group_ids": [_to_int(item) for item in (row.get("role_group_ids") or []) if _to_int(item)],
            "note": _to_text(row.get("note")),
        }

    def _values_for_row(self, row: dict, company_id: int) -> dict:
        vals = {
            "company_id": company_id,
            "menu_id": row["menu_id"],
            "target_parent_menu_id": row["target_parent_menu_id"] or False,
            "custom_label": row["custom_label"] or False,
            "sequence_override": int(row["sequence_override"] or 0),
            "visible": bool(row["visible"]),
            "active": True,
            "role_group_ids": [(6, 0, row["role_group_ids"])],
            "note": row["note"] or False,
        }
        return vals

    def _deactivate_superseded_policies(self, policy, company_id: int) -> None:
        if not policy or not policy.exists():
            return
        current_role_ids = set(int(group.id) for group in policy.role_group_ids)
        siblings = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False).search([
            ("company_id", "=", company_id),
            ("menu_id", "=", int(policy.menu_id.id or 0)),
            ("active", "=", True),
        ])
        for sibling in siblings:
            if int(sibling.id or 0) == int(policy.id or 0):
                continue
            sibling_role_ids = set(int(group.id) for group in sibling.role_group_ids)
            if sibling_role_ids == current_role_ids:
                sibling.write({"active": False})

    def _mirror_menu_config_contract(self, company_id: int):
        if "ui.business.config.contract" not in self.env:
            return None
        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        root_menu_id = self._scope_root_menu_id({})
        policies = Policy.search([
            ("company_id", "=", company_id),
            ("menu_id", "!=", False),
        ], order="menu_id, id desc")
        policies = self._policies_in_menu_config_scope(policies, root_menu_id)
        Contract = self.env["ui.business.config.contract"].sudo()
        name = _menu_config_contract_name(company_id)
        domain = [
            ("name", "=", name),
            ("company_id", "=", company_id),
            ("model", "=", "ir.ui.menu"),
            ("view_type", "=", False),
            ("action_id", "=", False),
            ("view_id", "=", False),
            ("role_key", "=", False),
        ]
        contract_json = _menu_config_contract_json(company_id, policies)
        vals = {
            "name": name,
            "model": "ir.ui.menu",
            "view_type": False,
            "action_id": False,
            "view_id": False,
            "role_key": False,
            "company_id": company_id,
            "contract_json": contract_json,
            "status": "published",
        }
        rec = Contract.search(domain, limit=1)
        if rec:
            rec.write(vals)
        else:
            rec = Contract.create(vals)
        rec.action_publish()
        return rec

    def handle(self, payload=None, ctx=None):
        del ctx
        self._ensure_access()
        params = (payload or {}).get("params") if isinstance(payload, dict) else {}
        params = params if isinstance(params, dict) else {}
        company_id = self._company_id(params)
        rows = params.get("rows") if isinstance(params.get("rows"), list) else []
        root_menu_id = self._scope_root_menu_id(params)
        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        saved = []
        for raw in rows:
            row = self._normalize_row(raw)
            if not row["menu_id"]:
                continue
            try:
                self._ensure_menu_config_scope(row["menu_id"], root_menu_id)
                if row["target_parent_menu_id"]:
                    self._ensure_menu_config_scope(row["target_parent_menu_id"], root_menu_id, field_label="上级菜单")
            except ValidationError as exc:
                return {
                    "ok": False,
                    "error": {"code": "MENU_CONFIG_SCOPE_VIOLATION", "message": str(exc), "reason_code": "MENU_CONFIG_SCOPE_VIOLATION"},
                    "code": 400,
                }
            vals = self._values_for_row(row, company_id)
            policy = Policy.browse(row["policy_id"]).exists() if row["policy_id"] else Policy
            if policy:
                policy.write(vals)
            else:
                existing = Policy.search([
                    ("company_id", "=", company_id),
                    ("menu_id", "=", row["menu_id"]),
                ], order="id desc", limit=1)
                policy = existing or Policy.create(vals)
                if existing:
                    policy.write(vals)
            self._deactivate_superseded_policies(policy, company_id)
            saved.append(self._serialize_policy(policy))
        try:
            contract = self._mirror_menu_config_contract(company_id)
        except ValidationError as exc:
            return {
                "ok": False,
                "error": {"code": "USER_ERROR", "message": str(exc), "reason_code": "USER_ERROR"},
                "code": 400,
            }

        return {
            "ok": True,
            "data": {
                "saved": saved,
                "saved_count": len(saved),
                "contract": {
                    "id": int(contract.id),
                    "name": str(contract.name or ""),
                    "model": str(contract.model or ""),
                    "status": str(contract.status or ""),
                    "version_no": int(contract.version_no or 1),
                } if contract else None,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
                "contract_mirrored": bool(contract),
                "scope_root_menu_id": root_menu_id,
                "scope_root_valid": bool(root_menu_id),
            },
        }


class MenuConfigurationCreateHandler(MenuConfigurationSaveHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["menu_create"]
    DESCRIPTION = "新增菜单入口"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "menu creation creates ir.ui.menu records"

    @classmethod
    def source_authority_contract(cls) -> dict:
        source = super().source_authority_contract()
        source.update({
            "kind": "ui_menu_config_menu_create_write_proxy",
            "authorities": [
                "ir.ui.menu",
                MENU_CONFIG_POLICY_MODEL,
                "ui.business.config.contract",
                "res.groups",
            ],
            "write_proxy": True,
            "runtime_carrier": cls.INTENT_TYPE,
            "boundary": "runtime_menu_entry_creation",
            "lowcode_boundary": "menu_config",
            "contract_source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
            "delivery_baseline_note": "长期菜单入口需沉淀到用户模块或行业模块。",
        })
        return source

    def _err(self, code: int, message: str, reason_code: str = "USER_ERROR"):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _parent_menu(self, parent_menu_id: int):
        if not parent_menu_id:
            return False
        parent = self.env["ir.ui.menu"].sudo().browse(parent_menu_id).exists()
        if not parent:
            raise ValidationError("请选择有效的上级菜单。")
        return parent

    def _source_menu(self, source_menu_id: int):
        if not source_menu_id:
            return False
        source = self.env["ir.ui.menu"].sudo().browse(source_menu_id).exists()
        if not source:
            raise ValidationError("请选择有效的复制来源菜单。")
        return source

    def _next_sequence(self, parent_menu_id: int) -> int:
        domain = [("parent_id", "=", parent_menu_id or False)]
        siblings = self.env["ir.ui.menu"].sudo().with_context(active_test=False).search(domain, order="sequence desc, id desc", limit=1)
        if not siblings:
            return 10
        return int((siblings.sequence or 0) + 10)

    def handle(self, payload=None, ctx=None):
        del ctx
        self._ensure_access()
        params = (payload or {}).get("params") if isinstance(payload, dict) else {}
        params = params if isinstance(params, dict) else {}
        company_id = self._company_id(params)
        name = _to_text(params.get("name"))
        if not name:
            return self._err(400, "请输入菜单名称。")

        parent_menu_id = _to_int(params.get("parent_menu_id") or params.get("parent_id"))
        source_menu_id = _to_int(params.get("source_menu_id") or params.get("copy_from_menu_id"))
        role_group_ids = [_to_int(item) for item in (params.get("role_group_ids") or []) if _to_int(item)]
        custom_label = _to_text(params.get("custom_label"))
        note = _to_text(params.get("note"))
        visible = _to_bool(params.get("visible"), True)
        sequence = _to_int(params.get("sequence")) or self._next_sequence(parent_menu_id)
        root_menu_id = self._scope_root_menu_id(params)

        try:
            if root_menu_id and not parent_menu_id:
                raise ValidationError("请选择当前业务根菜单下的上级菜单。")
            self._ensure_menu_config_scope(parent_menu_id, root_menu_id, field_label="上级菜单")
            if source_menu_id:
                self._ensure_menu_config_scope(source_menu_id, root_menu_id, field_label="复制来源菜单")
            parent = self._parent_menu(parent_menu_id)
            source = self._source_menu(source_menu_id)
            action = _to_text(params.get("action"))
            if not action and source:
                action = _menu_action_value(getattr(source, "action", ""))
            web_icon = _to_text(params.get("web_icon"))
            if not web_icon and source:
                web_icon = _to_text(getattr(source, "web_icon", ""))
            menu_vals = {
                "name": name,
                "parent_id": int(parent.id) if parent else False,
                "sequence": sequence,
            }
            if action:
                menu_vals["action"] = action
            if web_icon:
                menu_vals["web_icon"] = web_icon
            menu = self.env["ir.ui.menu"].sudo().create(menu_vals)

            Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
            policy_vals = self._values_for_row({
                "menu_id": int(menu.id),
                "target_parent_menu_id": int(parent.id) if parent else 0,
                "custom_label": custom_label,
                "sequence_override": sequence,
                "visible": visible,
                "role_group_ids": role_group_ids,
                "note": note or ("由菜单配置新增；长期使用需沉淀到用户模块。"),
            }, company_id)
            policy = Policy.create(policy_vals)
            contract = self._mirror_menu_config_contract(company_id)
        except ValidationError as exc:
            return self._err(400, str(exc))

        xmlids = self._xmlids_by_id("ir.ui.menu", [int(menu.id)])
        return {
            "ok": True,
            "data": {
                "menu": self._serialize_menu(menu, xmlids),
                "policy": self._serialize_policy(policy),
                "contract": {
                    "id": int(contract.id),
                    "name": str(contract.name or ""),
                    "model": str(contract.model or ""),
                    "status": str(contract.status or ""),
                    "version_no": int(contract.version_no or 1),
                } if contract else None,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
                "contract_mirrored": bool(contract),
                "scope_root_menu_id": root_menu_id,
                "scope_root_valid": bool(root_menu_id),
            },
        }


class MenuConfigurationDeleteHandler(MenuConfigurationSaveHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["menu_delete"]
    DESCRIPTION = "删除菜单配置新增的菜单入口"
    VERSION = "1.0.0"
    NON_IDEMPOTENT_ALLOWED = "menu deletion removes runtime-created ir.ui.menu records"

    @classmethod
    def source_authority_contract(cls) -> dict:
        source = super().source_authority_contract()
        source.update({
            "kind": "ui_menu_config_menu_delete_write_proxy",
            "authorities": [
                "ir.ui.menu",
                "ir.model.data",
                MENU_CONFIG_POLICY_MODEL,
                "ui.business.config.contract",
            ],
            "write_proxy": True,
            "runtime_carrier": cls.INTENT_TYPE,
            "boundary": "runtime_menu_entry_deletion",
            "lowcode_boundary": "menu_config",
            "contract_source": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
        })
        return source

    def _err(self, code: int, message: str, reason_code: str = "USER_ERROR"):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _menu_external_ids(self, menu_ids: list[int]) -> dict[int, str]:
        if not menu_ids:
            return {}
        ModelData = self.env["ir.model.data"].sudo()
        rows = ModelData.search([
            ("model", "=", "ir.ui.menu"),
            ("res_id", "in", menu_ids),
        ])
        out = {}
        for row in rows:
            res_id = _to_int(getattr(row, "res_id", 0))
            if not res_id:
                continue
            out[res_id] = "%s.%s" % (_to_text(getattr(row, "module", "")), _to_text(getattr(row, "name", "")))
        return out

    def _descendant_menu_ids(self, menu_id: int) -> list[int]:
        out: list[int] = []
        Menu = self.env["ir.ui.menu"].sudo().with_context(active_test=False)
        children = Menu.search([("parent_id", "=", menu_id)])
        for child in children:
            child_id = int(child.id or 0)
            if not child_id:
                continue
            out.append(child_id)
            out.extend(self._descendant_menu_ids(child_id))
        return out

    def handle(self, payload=None, ctx=None):
        del ctx
        self._ensure_access()
        params = (payload or {}).get("params") if isinstance(payload, dict) else {}
        params = params if isinstance(params, dict) else {}
        company_id = self._company_id(params)
        menu_id = _to_int(params.get("menu_id") or params.get("id"))
        recursive = _to_bool(params.get("recursive"), False)
        if not menu_id:
            return self._err(400, "请选择要删除的菜单。")

        Menu = self.env["ir.ui.menu"].sudo().with_context(active_test=False)
        menu = Menu.browse(menu_id).exists()
        if not menu:
            return self._err(404, "菜单不存在或已删除。", "NOT_FOUND")
        root_menu_id = self._scope_root_menu_id(params)
        try:
            self._ensure_menu_config_scope(menu_id, root_menu_id)
        except ValidationError as exc:
            return self._err(400, str(exc), "MENU_CONFIG_SCOPE_VIOLATION")

        descendant_ids = self._descendant_menu_ids(menu_id)
        if descendant_ids and not recursive:
            return self._err(400, "该菜单包含下级菜单，请先删除下级菜单。", "HAS_CHILDREN")
        delete_ids = [menu_id] + descendant_ids
        xmlids = self._menu_external_ids(delete_ids)
        if xmlids:
            protected = ", ".join("%s(%s)" % (xmlid, mid) for mid, xmlid in sorted(xmlids.items()))
            return self._err(400, "系统菜单不能物理删除，请关闭“显示菜单”隐藏。受保护菜单：%s" % protected, "PROTECTED_MENU")

        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        policies = Policy.search([
            ("company_id", "=", company_id),
            ("menu_id", "in", delete_ids),
        ])
        for policy in policies:
            policy.write({"active": False, "visible": False})

        deleted = []
        for current_id in reversed(delete_ids):
            current = Menu.browse(current_id).exists()
            if not current:
                continue
            deleted.append({"id": int(current.id), "name": _to_text(current.display_name or current.name)})
            current.unlink()

        contract = self._mirror_menu_config_contract(company_id)
        return {
            "ok": True,
            "data": {
                "deleted": deleted,
                "deleted_count": len(deleted),
                "deleted_menu_ids": delete_ids,
                "deactivated_policy_count": len(policies),
                "contract": {
                    "id": int(contract.id),
                    "name": str(contract.name or ""),
                    "model": str(contract.model or ""),
                    "status": str(contract.status or ""),
                    "version_no": int(contract.version_no or 1),
                } if contract else None,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
                "contract_mirrored": bool(contract),
                "scope_root_menu_id": root_menu_id,
                "scope_root_valid": bool(root_menu_id),
            },
        }


class MenuConfigurationAuditHandler(MenuConfigurationLoadHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["audit"]
    DESCRIPTION = "审计当前公司和业务角色命中的菜单配置"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_menu_config_audit"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _policy_flag_summary(self, policy) -> dict:
        return {
            "hidden": not bool(policy.visible),
            "renamed": bool(_to_text(policy.custom_label)),
            "reordered": bool(int(policy.sequence_override or 0)),
            "moved": bool(policy.target_parent_menu_id),
        }

    def _serialize_audit_policy(self, policy, *, applicable_policy_ids: set[int]) -> dict:
        flags = self._policy_flag_summary(policy)
        menu = policy.menu_id
        target_parent = policy.target_parent_menu_id
        return {
            "id": int(policy.id),
            "menu_id": int(menu.id or 0) if menu else 0,
            "menu_label": _to_text(getattr(menu, "name", "")) if menu else "",
            "menu_complete_name": _to_text(getattr(menu, "complete_name", "")) if menu else "",
            "company_id": int(policy.company_id.id or 0) if policy.company_id else 0,
            "active": bool(policy.active),
            "visible": bool(policy.visible),
            "custom_label": _to_text(policy.custom_label),
            "sequence_override": int(policy.sequence_override or 0),
            "target_parent_menu_id": int(target_parent.id or 0) if target_parent else 0,
            "target_parent_label": _to_text(getattr(target_parent, "complete_name", "")) if target_parent else "",
            "role_group_ids": [int(group.id) for group in policy.role_group_ids],
            "role_group_names": [_to_text(group.display_name or group.name) for group in policy.role_group_ids],
            "scope_summary": _to_text(policy.scope_summary),
            "effect_summary": _to_text(policy.effect_summary),
            "preview_summary": _to_text(policy.preview_summary),
            "applicable": int(policy.id) in applicable_policy_ids,
            "flags": flags,
        }

    def _serialize_runtime_contract_policy(self, policy: dict) -> dict:
        menu_id = _to_int(policy.get("menu_id"))
        visible = _to_bool(policy.get("visible"), True)
        custom_label = _to_text(policy.get("custom_label"))
        sequence_override = _to_int(policy.get("sequence_override"))
        target_parent_id = _to_int(policy.get("target_parent_menu_id"))
        flags = {
            "hidden": not visible,
            "renamed": bool(custom_label),
            "reordered": bool(sequence_override),
            "moved": bool(target_parent_id),
        }
        return {
            "id": _to_int(policy.get("policy_id")),
            "menu_id": menu_id,
            "menu_label": _to_text(policy.get("menu_label")),
            "menu_complete_name": _to_text(policy.get("menu_complete_name")),
            "company_id": _to_int(policy.get("company_id")) or self._company_id(self.params if isinstance(self.params, dict) else {}),
            "active": _to_bool(policy.get("active"), True),
            "visible": visible,
            "custom_label": custom_label,
            "sequence_override": sequence_override,
            "target_parent_menu_id": target_parent_id,
            "target_parent_label": _to_text(policy.get("target_parent_menu_complete_name")),
            "role_group_ids": [_to_int(item) for item in (policy.get("role_group_ids") or []) if _to_int(item)],
            "role_group_names": [],
            "scope_summary": "运行时菜单策略",
            "effect_summary": "隐藏菜单" if not visible else "菜单配置显示",
            "preview_summary": "",
            "applicable": True,
            "runtime_source": MENU_CONFIG_RUNTIME_SOURCE_CONTRACT,
            "flags": flags,
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        company_id = self._company_id(params)
        include_inactive = _to_bool(params.get("include_inactive") or params.get("includeInactive"), False)

        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        domain = [
            ("company_id", "=", company_id),
            ("menu_id", "!=", False),
        ]
        if not include_inactive:
            domain.append(("active", "=", True))
        policies = Policy.search(domain, order="menu_id, id desc")
        scope_root_menu_id = self._scope_root_menu_id(params)
        policies = self._policies_in_menu_config_scope(policies, scope_root_menu_id)
        runtime_model = self.env[MENU_CONFIG_POLICY_MODEL]
        if hasattr(runtime_model, "_runtime_menu_config_source_for_user"):
            applicable_by_menu, runtime_source = runtime_model._runtime_menu_config_source_for_user(user=self.env.user)
        else:
            applicable_by_menu = runtime_model._runtime_policies_for_user(user=self.env.user)
            runtime_source = MENU_CONFIG_RUNTIME_SOURCE_POLICY
        applicable_menu_ids = {int(menu_id or 0) for menu_id in applicable_by_menu}
        applicable_policy_ids = {
            _to_int(policy.get("policy_id")) if isinstance(policy, dict) else int(policy.id)
            for policy in applicable_by_menu.values()
        }

        policy_rows = [
            self._serialize_audit_policy(policy, applicable_policy_ids=applicable_policy_ids)
            for policy in policies
        ]
        if runtime_source == MENU_CONFIG_RUNTIME_SOURCE_CONTRACT:
            applicable_rows = [
                self._serialize_runtime_contract_policy(policy)
                for _menu_id, policy in sorted(applicable_by_menu.items(), key=lambda item: int(item[0] or 0))
                if isinstance(policy, dict)
            ]
        else:
            applicable_rows = [row for row in policy_rows if row["applicable"]]
        summary = {
            "runtime_source": runtime_source,
            "configured_policy_count": len(policy_rows),
            "policy_table_count": len(policy_rows),
            "runtime_policy_count": len(applicable_by_menu),
            "contract_authoritative": runtime_source == MENU_CONFIG_RUNTIME_SOURCE_CONTRACT,
            "applicable_policy_count": len(applicable_rows),
            "hidden_count": sum(1 for row in applicable_rows if row["flags"]["hidden"]),
            "renamed_count": sum(1 for row in applicable_rows if row["flags"]["renamed"]),
            "reordered_count": sum(1 for row in applicable_rows if row["flags"]["reordered"]),
            "moved_count": sum(1 for row in applicable_rows if row["flags"]["moved"]),
            "inactive_policy_count": sum(1 for row in policy_rows if not row["active"]),
            "not_applicable_policy_ids": [row["id"] for row in policy_rows if not row["applicable"]],
            "scope_root_menu_id": scope_root_menu_id,
            "scope_root_valid": bool(scope_root_menu_id),
        }
        return {
            "ok": True,
            "data": {
                "company": _m2o_payload(self.env["res.company"].sudo().browse(company_id)),
                "summary": summary,
                "policies": policy_rows,
                "applicable_policies": applicable_rows,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class MenuConfigurationRollbackHandler(MenuConfigurationLoadHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["rollback"]
    DESCRIPTION = "按菜单配置版本恢复菜单运行时 policy"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_menu_config_rollback"
    NON_IDEMPOTENT_ALLOWED = "menu config rollback restores mutable policy rows"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": [
                "ui.business.config.contract",
                "ui.business.config.contract.version",
                MENU_CONFIG_POLICY_MODEL,
                "ir.ui.menu",
                "res.groups",
            ],
            "projection_only": False,
            "write_proxy": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str = "USER_ERROR"):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _contract_for_company(self, company_id: int):
        if "ui.business.config.contract" not in self.env:
            return None
        return self.env["ui.business.config.contract"].sudo().search([
            ("name", "=", _menu_config_contract_name(company_id)),
            ("company_id", "=", company_id),
            ("model", "=", "ir.ui.menu"),
            ("view_type", "=", False),
            ("action_id", "=", False),
            ("view_id", "=", False),
            ("role_key", "=", False),
        ], limit=1)

    def _target_version(self, contract, version_no: int):
        Version = self.env["ui.business.config.contract.version"].sudo()
        if version_no:
            return Version.search([
                ("contract_id", "=", contract.id),
                ("version_no", "=", version_no),
            ], order="id desc", limit=1)
        versions = Version.search([
            ("contract_id", "=", contract.id),
        ], order="version_no desc, id desc", limit=2)
        return versions[1] if len(versions) >= 2 else None

    def _restore_policy_rows(self, company_id: int, contract_json: dict) -> list[dict]:
        rows = _menu_orchestration_policies(contract_json)
        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        root_menu_id = self._scope_root_menu_id({})
        restored = []
        restored_ids: set[int] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            menu_id = _to_int(row.get("menu_id"))
            if not menu_id:
                continue
            try:
                self._ensure_menu_config_scope(menu_id, root_menu_id)
                target_parent_id = _to_int(row.get("target_parent_menu_id"))
                if target_parent_id:
                    self._ensure_menu_config_scope(target_parent_id, root_menu_id, field_label="上级菜单")
            except ValidationError:
                continue
            policy_id = _to_int(row.get("policy_id"))
            role_group_ids = [_to_int(item) for item in (row.get("role_group_ids") or []) if _to_int(item)]
            vals = {
                "company_id": company_id,
                "menu_id": menu_id,
                "target_parent_menu_id": _to_int(row.get("target_parent_menu_id")) or False,
                "custom_label": _to_text(row.get("custom_label")) or False,
                "sequence_override": int(row.get("sequence_override") or 0),
                "visible": _to_bool(row.get("visible"), True),
                "active": _to_bool(row.get("active"), True),
                "role_group_ids": [(6, 0, role_group_ids)],
                "note": _to_text(row.get("note")) or False,
            }
            policy = Policy.browse(policy_id).exists() if policy_id else Policy
            if not policy:
                policy = Policy.search([
                    ("company_id", "=", company_id),
                    ("menu_id", "=", menu_id),
                ], order="id desc", limit=1)
            if policy:
                policy.write(vals)
            else:
                policy = Policy.create(vals)
            restored_ids.add(int(policy.id))
            restored.append(self._serialize_policy(policy))

        current = Policy.search([
            ("company_id", "=", company_id),
            ("menu_id", "!=", False),
        ])
        for policy in current:
            if int(policy.id) not in restored_ids and policy.active:
                policy.write({"active": False})
        return restored

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        company_id = self._company_id(params)
        version_no = _to_int(params.get("version_no") or params.get("versionNo"))
        contract = self._contract_for_company(company_id)
        if not contract:
            return self._err(404, "未找到菜单配置", "NOT_FOUND")
        target = self._target_version(contract, version_no)
        if not target:
            return self._err(400, "无可回滚的菜单配置版本")
        snapshot = target.snapshot_json or {}
        rows = _menu_orchestration_policies(snapshot)
        if not rows:
            return self._err(400, "目标版本不是可恢复的菜单配置")
        scoped_snapshot = self._scope_contract_json(company_id, snapshot)
        restored = self._restore_policy_rows(company_id, scoped_snapshot)
        contract.write({
            "contract_json": scoped_snapshot,
            "status": "published",
            "version_no": int(target.version_no or contract.version_no or 1),
        })
        contract.action_publish()
        return {
            "ok": True,
            "data": {
                "company": _m2o_payload(self.env["res.company"].sudo().browse(company_id)),
                "contract": {
                    "id": int(contract.id),
                    "name": str(contract.name or ""),
                    "model": str(contract.model or ""),
                    "status": str(contract.status or ""),
                    "version_no": int(contract.version_no or 1),
                },
                "rolled_back_to_version": int(target.version_no or 0),
                "restored_count": len(restored),
                "restored": restored,
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }


class MenuConfigurationVersionsHandler(MenuConfigurationLoadHandler):
    INTENT_TYPE = MENU_CONFIG_INTENTS["versions"]
    DESCRIPTION = "读取菜单配置版本列表和摘要"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_menu_config_versions_projection"

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": [
                "ui.business.config.contract",
                "ui.business.config.contract.version",
                MENU_CONFIG_POLICY_MODEL,
            ],
            "projection_only": True,
            "bootstraps_missing_contract_from_current_policies": False,
            "explicit_bootstrap_required": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _contract_for_company(self, company_id: int):
        if "ui.business.config.contract" not in self.env:
            return None
        return self.env["ui.business.config.contract"].sudo().search([
            ("name", "=", _menu_config_contract_name(company_id)),
            ("company_id", "=", company_id),
            ("model", "=", "ir.ui.menu"),
            ("view_type", "=", False),
            ("action_id", "=", False),
            ("view_id", "=", False),
            ("role_key", "=", False),
        ], limit=1)

    def _bootstrap_contract_from_current_policies(self, company_id: int):
        if "ui.business.config.contract" not in self.env:
            return None
        Policy = self.env[MENU_CONFIG_POLICY_MODEL].sudo().with_context(active_test=False)
        policies = Policy.search([
            ("company_id", "=", company_id),
            ("menu_id", "!=", False),
        ], order="menu_id, id desc")
        policies = self._policies_in_menu_config_scope(policies, self._scope_root_menu_id({}))
        if not policies:
            return None
        Contract = self.env["ui.business.config.contract"].sudo()
        contract_json = _menu_config_contract_json(company_id, policies)
        rec = Contract.create({
            "name": _menu_config_contract_name(company_id),
            "model": "ir.ui.menu",
            "view_type": False,
            "action_id": False,
            "view_id": False,
            "role_key": False,
            "company_id": company_id,
            "contract_json": contract_json,
            "status": "published",
        })
        rec.action_publish()
        return rec

    def _serialize_version(self, version) -> dict:
        contract = getattr(version, "contract_id", None)
        company = getattr(contract, "company_id", None)
        company_id = int(getattr(company, "id", 0) or getattr(self.env.company, "id", 0) or 0)
        snapshot = self._scope_contract_json(company_id, version.snapshot_json or {})
        return {
            "id": int(version.id),
            "version_no": int(version.version_no or 0),
            "status": str(version.status or ""),
            "created_by": _m2o_payload(version.created_by),
            "summary": _menu_orchestration_summary(snapshot),
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        self._ensure_access()
        params = self.params if isinstance(self.params, dict) else {}
        company_id = self._company_id(params)
        allow_bootstrap = _to_bool(
            params.get("allow_bootstrap") or params.get("allowBootstrap") or params.get("bootstrap"),
            False,
        )
        contract = self._contract_for_company(company_id)
        bootstrapped = False
        if not contract and allow_bootstrap:
            contract = self._bootstrap_contract_from_current_policies(company_id)
            bootstrapped = bool(contract)
        if not contract:
            return {
                "ok": True,
                "data": {
                    "company": _m2o_payload(self.env["res.company"].sudo().browse(company_id)),
                    "contract": None,
                    "versions": [],
                },
                "meta": {
                    "intent": self.INTENT_TYPE,
                    "source_authority": self.source_authority_contract(),
                    "bootstrapped_from_current_policies": False,
                    "bootstrap_required": not allow_bootstrap,
                },
            }
        versions = self.env["ui.business.config.contract.version"].sudo().search([
            ("contract_id", "=", contract.id),
        ], order="version_no desc, id desc", limit=20)
        return {
            "ok": True,
            "data": {
                "company": _m2o_payload(self.env["res.company"].sudo().browse(company_id)),
                "contract": {
                    "id": int(contract.id),
                    "name": str(contract.name or ""),
                    "model": str(contract.model or ""),
                    "status": str(contract.status or ""),
                    "version_no": int(contract.version_no or 1),
                    "summary": _menu_orchestration_summary(self._scope_contract_json(company_id, contract.contract_json or {})),
                },
                "versions": [self._serialize_version(version) for version in versions],
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
                "bootstrapped_from_current_policies": bootstrapped,
            },
        }
