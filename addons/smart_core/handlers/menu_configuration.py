# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.exceptions import AccessError

from ..core.base_handler import BaseIntentHandler


BUSINESS_CONFIG_GROUP = "smart_core.group_smart_core_business_config_admin"
PLATFORM_ADMIN_GROUP = "smart_core.group_smart_core_admin"


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


def _xmlid_record(env, xmlid: str):
    try:
        return env.ref(xmlid, raise_if_not_found=False)
    except Exception:
        return None


class MenuConfigurationLoadHandler(BaseIntentHandler):
    INTENT_TYPE = "ui.menu_config.panel.get"
    DESCRIPTION = "读取菜单配置面板数据"
    VERSION = "1.0.0"
    SOURCE_KIND = "ui_menu_config_panel_projection"
    SOURCE_AUTHORITIES = ("ir.ui.menu", "ui.menu.config.policy", "res.groups")
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
        action = _to_text(getattr(menu, "action", ""))
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
        groups = self.env["res.groups"].sudo()
        groups |= menus.mapped("groups_id")
        groups |= policies.mapped("role_group_ids")
        for xmlid in (BUSINESS_CONFIG_GROUP, PLATFORM_ADMIN_GROUP):
            group = _xmlid_record(self.env, xmlid)
            if group:
                groups |= group.sudo()
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
        if requested_menu_ids:
            policy_records = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False).search([
                ("company_id", "=", company_id),
                ("active", "=", True),
                ("menu_id", "!=", False),
            ])
            policy_menu_ids = policy_records.mapped("menu_id").ids
            target_parent_ids = policy_records.mapped("target_parent_menu_id").ids
            requested_menus = MenuAll.browse(sorted(set(requested_menu_ids + policy_menu_ids + target_parent_ids))).exists()
            menu_ids_with_parents = self._expand_with_parent_ids(requested_menus)
            menus = MenuAll.search([("id", "in", menu_ids_with_parents)], order="parent_id, sequence, id")
        else:
            visible_ids = list(Menu.with_user(self.env.user)._visible_menu_ids())
            menus = Menu.search([("id", "in", visible_ids)], order="parent_id, sequence, id")
        menu_ids = [int(menu.id) for menu in menus]
        xmlids = self._xmlids_by_id("ir.ui.menu", menu_ids)
        menu_rows = [self._serialize_menu(menu, xmlids) for menu in menus]

        Policy = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False)
        policies = Policy.search([
            ("company_id", "=", company_id),
            ("menu_id", "in", menu_ids),
        ], order="id desc")
        policy_by_menu: dict[int, dict] = {}
        for policy in policies:
            policy_by_menu.setdefault(int(policy.menu_id.id), self._serialize_policy(policy))

        effective_menu_rows = self._effective_menu_rows(menu_rows, policy_by_menu)

        groups = self._group_option_records(menus, policies)
        group_rows = [
            {
                "id": int(group.id),
                "name": _to_text(group.name),
                "display_name": _to_text(group.display_name or group.name),
                "category": _to_text(group.category_id.display_name or group.category_id.name) if group.category_id else "",
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
                "requested_menu_count": len(requested_menu_ids),
                "group_option_count": len(group_rows),
            },
        }


class MenuConfigurationSaveHandler(MenuConfigurationLoadHandler):
    INTENT_TYPE = "ui.menu_config.panel.set"
    DESCRIPTION = "保存菜单配置面板数据"
    VERSION = "1.0.0"
    REQUIRED_GROUPS = [BUSINESS_CONFIG_GROUP]

    @classmethod
    def source_authority_contract(cls) -> dict:
        source = super().source_authority_contract()
        source.update({
            "kind": "ui_menu_config_panel_write_proxy",
            "write_proxy": True,
            "runtime_carrier": cls.INTENT_TYPE,
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

    def handle(self, payload=None, ctx=None):
        del ctx
        self._ensure_access()
        params = (payload or {}).get("params") if isinstance(payload, dict) else {}
        params = params if isinstance(params, dict) else {}
        company_id = self._company_id(params)
        rows = params.get("rows") if isinstance(params.get("rows"), list) else []
        Policy = self.env["ui.menu.config.policy"].sudo().with_context(active_test=False)
        saved = []
        for raw in rows:
            row = self._normalize_row(raw)
            if not row["menu_id"]:
                continue
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
            saved.append(self._serialize_policy(policy))

        return {
            "data": {
                "saved": saved,
                "saved_count": len(saved),
            },
            "meta": {
                "intent": self.INTENT_TYPE,
                "source_authority": self.source_authority_contract(),
            },
        }
