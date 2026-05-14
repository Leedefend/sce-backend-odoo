# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import api
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry

from .product_identity import resolve_product_identity
from .product_policy_service import ProductPolicyService


def _text(value: Any) -> str:
    return str(value or "").strip()


def _action_id(action: Any) -> int:
    try:
        return int(action.id or 0) if action else 0
    except Exception:
        return 0


def _action_model(action: Any) -> str:
    try:
        return _text(getattr(action, "res_model", ""))
    except Exception:
        return ""


def _menu_xmlid(menu: Any) -> str:
    try:
        return _text(menu.get_external_id().get(menu.id, ""))
    except Exception:
        return ""


def _menu_path(menu: Any) -> list[str]:
    path: list[str] = []
    current = menu
    while current:
        name = _text(getattr(current, "name", ""))
        if name:
            path.append(name)
        current = getattr(current, "parent_id", None)
    return list(reversed(path))


def _slug(value: str) -> str:
    return _text(value).replace(".", "_").replace("-", "_").replace(" ", "_").lower() or "menu"


class ProductPolicyCatalogSyncService:
    SOURCE_KIND = "product_policy_catalog_sync"
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    def _construction_source_db(self) -> str:
        try:
            configured = self.env["ir.config_parameter"].sudo().get_param(
                "smart_core.release_operator.construction_source_db",
                "",
            )
        except Exception:
            configured = ""
        return _text(configured) or "sc_demo"

    def _extract_user_menu_pages(self, source_env) -> list[dict[str, Any]]:
        menus = source_env["ir.ui.menu"].sudo().search([("action", "!=", False)], order="sequence,id")
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for menu in menus:
            xmlid = _menu_xmlid(menu)
            if not xmlid.startswith("smart_construction_core."):
                continue
            action = menu.action
            action_id = _action_id(action)
            if action_id <= 0:
                continue
            path = _menu_path(menu)
            if not path:
                continue
            page_key = xmlid
            if page_key in seen:
                continue
            seen.add(page_key)
            root_label = path[0] if path else "施工管理"
            group_label = path[1] if len(path) > 1 else root_label
            page_label = path[-1]
            menu_id = int(menu.id or 0)
            rows.append(
                {
                    "app_id": _slug(group_label),
                    "group_key": f"construction.{_slug(group_label)}",
                    "group_label": group_label,
                    "root_label": root_label,
                    "menu_id": menu_id,
                    "menu_xmlid": xmlid,
                    "menu_key": xmlid,
                    "page_key": page_key,
                    "page_label": page_label,
                    "label": page_label,
                    "route": f"/a/{action_id}?menu_id={menu_id}",
                    "scene_key": "",
                    "action_id": action_id,
                    "action_model": _text(getattr(action, "_name", "")),
                    "res_model": _action_model(action),
                    "visible_menu_path": " / ".join(path),
                    "control_granularity": "user_visible_menu_page",
                    "enabled": True,
                    "release_state": "released",
                    "access_level": "public",
                    "control_object": "用户可见菜单页面",
                    "source_kind": "ir.ui.menu",
                }
            )
        return rows

    def _load_source_user_menu_pages(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        source_db = self._construction_source_db()
        current_db = _text(getattr(getattr(self.env, "cr", None), "dbname", ""))
        if source_db == current_db:
            return self._extract_user_menu_pages(self.env), {"source_db": current_db, "source": "current_db_ir_ui_menu"}
        try:
            registry = Registry(source_db)
            with registry.cursor() as cr:
                source_env = api.Environment(cr, SUPERUSER_ID, {})
                return self._extract_user_menu_pages(source_env), {
                    "source_db": source_db,
                    "source": "external_db_ir_ui_menu",
                }
        except Exception as exc:
            return [], {
                "source_db": source_db,
                "source": "external_db_ir_ui_menu_failed",
                "error": str(exc),
            }

    def build_construction_policy_payload(self, *, product_key: str) -> dict[str, Any]:
        identity = resolve_product_identity(product_key=product_key)
        menu_pages, menu_source = self._load_source_user_menu_pages()
        if menu_pages:
            return self._build_construction_policy_payload_from_menu_pages(
                identity=identity,
                menu_pages=menu_pages,
                menu_source=menu_source,
            )
        label = "施工管理预览版" if identity["edition_key"] == "preview" else "施工管理标准版"
        return {
            "product_key": identity["product_key"],
            "base_product_key": identity["base_product_key"],
            "edition_key": identity["edition_key"],
            "state": "preview" if identity["edition_key"] == "preview" else "stable",
            "access_level": "public",
            "allowed_role_codes": [],
            "label": label,
            "version": "v1",
            "scene_version_bindings": {},
            "menu_groups": [],
            "scenes": [],
            "capabilities": [],
            "policy_source_authority": {
                "kind": self.SOURCE_KIND,
                "authorities": ["ir.ui.menu", "ir.actions", "ir.model.data", "delivery_product_identity_resolver"],
                "source_db": _text(menu_source.get("source_db")),
                "source": _text(menu_source.get("source")) or "menu_fact_unavailable",
                "menu_page_count": 0,
                "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            },
        }

    def _build_construction_policy_payload_from_menu_pages(
        self,
        *,
        identity: dict[str, str],
        menu_pages: list[dict[str, Any]],
        menu_source: dict[str, Any],
    ) -> dict[str, Any]:
        groups_by_key: dict[str, dict[str, Any]] = {}
        scene_rows: list[dict[str, Any]] = []
        capability_rows: list[dict[str, Any]] = []
        scene_bindings: dict[str, dict[str, str]] = {}
        for index, page in enumerate(menu_pages, start=1):
            group_key = _text(page.get("group_key")) or "construction.menu"
            group = groups_by_key.setdefault(
                group_key,
                {
                    "group_key": group_key,
                    "group_label": _text(page.get("group_label")) or "施工管理",
                    "category": "user_visible_menu",
                    "menus": [],
                },
            )
            page_key = _text(page.get("page_key"))
            label = _text(page.get("page_label") or page.get("label")) or page_key
            capability_key = f"construction.menu.{_slug(page_key)}"
            menu = {
                "menu_key": _text(page.get("menu_key")) or page_key,
                "label": label,
                "page_key": page_key,
                "page_label": label,
                "route": _text(page.get("route")),
                "scene_key": _text(page.get("scene_key")),
                "product_key": _text(page.get("app_id")),
                "capability_key": capability_key,
                "visible_menu_path": _text(page.get("visible_menu_path")) or label,
                "control_granularity": "user_visible_menu_page",
                "enabled": bool(page.get("enabled", True)),
                "release_state": _text(page.get("release_state")) or "released",
                "access_level": _text(page.get("access_level")) or "public",
                "control_object": "用户可见菜单页面",
                "source_kind": "ir.ui.menu",
                "menu_id": int(page.get("menu_id") or 0),
                "menu_xmlid": _text(page.get("menu_xmlid")),
                "action_id": int(page.get("action_id") or 0),
                "action_model": _text(page.get("action_model")),
                "res_model": _text(page.get("res_model")),
                "sequence": index,
            }
            group["menus"].append(menu)
            capability_rows.append(
                {
                    "capability_key": capability_key,
                    "label": label,
                    "group_key": group_key,
                    "group_label": _text(page.get("group_label")) or "施工管理",
                    "target_scene_key": _text(page.get("scene_key")),
                    "target_page_key": page_key,
                    "product_key": _text(page.get("app_id")),
                    "delivery_level": "exclusive",
                    "entry_kind": "user_visible_menu_page",
                    "visible_menu_path": menu["visible_menu_path"],
                    "enabled": bool(page.get("enabled", True)),
                    "release_state": _text(page.get("release_state")) or "released",
                    "access_level": _text(page.get("access_level")) or "public",
                    "control_object": "用户可见菜单页面",
                    "source_kind": "ir.ui.menu",
                    "menu_xmlid": _text(page.get("menu_xmlid")),
                    "action_id": int(page.get("action_id") or 0),
                    "res_model": _text(page.get("res_model")),
                }
            )
        menu_groups = [groups_by_key[key] for key in groups_by_key]
        label = "施工管理预览版" if identity["edition_key"] == "preview" else "施工管理标准版"
        return {
            "product_key": identity["product_key"],
            "base_product_key": identity["base_product_key"],
            "edition_key": identity["edition_key"],
            "state": "preview" if identity["edition_key"] == "preview" else "stable",
            "access_level": "public",
            "allowed_role_codes": [],
            "label": label,
            "version": "v1",
            "scene_version_bindings": scene_bindings,
            "menu_groups": menu_groups,
            "scenes": scene_rows,
            "capabilities": capability_rows,
            "policy_source_authority": {
                "kind": self.SOURCE_KIND,
                "authorities": ["ir.ui.menu", "ir.actions", "ir.model.data", "delivery_product_identity_resolver"],
                "source_db": _text(menu_source.get("source_db")),
                "source": _text(menu_source.get("source")),
                "menu_page_count": len(menu_pages),
                "no_business_fact_authority": self.NO_BUSINESS_FACT_AUTHORITY,
            },
            "control_definition": [
                {"key": "included", "label": "是否纳入产品", "meaning": "决定该用户菜单页面是否进入当前产品发布包。"},
                {"key": "release_state", "label": "发布阶段", "meaning": "released 面向正式用户；preview 仅预览；hidden/retired 不进入有效发布范围。"},
                {"key": "access_level", "label": "可见范围", "meaning": "public 全部授权用户；internal 内部；role_restricted 后续按角色策略限制。"},
                {"key": "source_identity", "label": "来源证据", "meaning": "记录真实 ir.ui.menu、action、res_model 与源数据库，保证平台管控对象与用户入口一致。"},
            ],
        }

    def build_policy_payload(self, *, product_key: str) -> dict[str, Any]:
        identity = resolve_product_identity(product_key=product_key)
        if identity["base_product_key"] == "construction":
            return self.build_construction_policy_payload(product_key=identity["product_key"])
        return ProductPolicyService(self.env).get_policy(product_key=identity["product_key"])

    def sync_policy(self, *, product_key: str, preserve_state: bool = True, preserve_access_level: bool = True):
        identity = resolve_product_identity(product_key=product_key)
        payload = self.build_policy_payload(product_key=identity["product_key"])
        model = self.env["sc.product.policy"].sudo()
        rec = model.search([("product_key", "=", identity["product_key"])], limit=1)
        current = rec.to_runtime_dict() if rec else {}
        self._merge_existing_page_controls(payload, current)
        values = {
            "active": True,
            "product_key": identity["product_key"],
            "base_product_key": _text(payload.get("base_product_key")) or identity["base_product_key"],
            "edition_key": _text(payload.get("edition_key")) or identity["edition_key"],
            "state": _text(current.get("state")) if preserve_state and current else (_text(payload.get("state")) or "stable"),
            "access_level": _text(current.get("access_level")) if preserve_access_level and current else (_text(payload.get("access_level")) or "public"),
            "allowed_role_codes": payload.get("allowed_role_codes") if isinstance(payload.get("allowed_role_codes"), list) else [],
            "label": _text(payload.get("label")) or identity["product_key"],
            "version": _text(payload.get("version")) or "v1",
            "scene_version_bindings": payload.get("scene_version_bindings") if isinstance(payload.get("scene_version_bindings"), dict) else {},
            "menu_groups": payload.get("menu_groups") if isinstance(payload.get("menu_groups"), list) else [],
            "scenes": payload.get("scenes") if isinstance(payload.get("scenes"), list) else [],
            "capabilities": payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else [],
            "note": "synced from productized scene catalog",
        }
        if rec:
            rec.write(values)
        else:
            rec = model.create(values)
        return rec

    def _merge_existing_page_controls(self, payload: dict[str, Any], current: dict[str, Any]) -> None:
        current_controls: dict[str, dict[str, Any]] = {}
        for group in current.get("menu_groups") if isinstance(current.get("menu_groups"), list) else []:
            if not isinstance(group, dict):
                continue
            for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
                if not isinstance(menu, dict):
                    continue
                page_key = _text(menu.get("page_key") or menu.get("scene_key") or menu.get("menu_key"))
                if page_key:
                    current_controls[page_key] = menu
        if not current_controls:
            return

        def _apply(row: dict[str, Any]) -> dict[str, Any]:
            page_key = _text(row.get("page_key") or row.get("scene_key") or row.get("target_page_key") or row.get("target_scene_key") or row.get("menu_key"))
            current_row = current_controls.get(page_key) or {}
            if not current_row:
                return row
            next_row = dict(row)
            for key in ("enabled", "release_state", "access_level", "policy_note"):
                if key in current_row:
                    next_row[key] = current_row.get(key)
            return next_row

        menu_groups = []
        for group in payload.get("menu_groups") if isinstance(payload.get("menu_groups"), list) else []:
            if not isinstance(group, dict):
                continue
            next_group = dict(group)
            menus = group.get("menus") if isinstance(group.get("menus"), list) else []
            next_group["menus"] = [_apply(menu) for menu in menus if isinstance(menu, dict)]
            menu_groups.append(next_group)
        payload["menu_groups"] = menu_groups
        scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
        capabilities = payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else []
        payload["scenes"] = [_apply(scene) for scene in scenes if isinstance(scene, dict)]
        payload["capabilities"] = [_apply(capability) for capability in capabilities if isinstance(capability, dict)]
