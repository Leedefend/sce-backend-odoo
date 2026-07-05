# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo import api
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry

from odoo.addons.smart_core.core.navigation_entry_target import resolve_scene_key
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first

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
        model = _text(getattr(action, "res_model", ""))
        if model:
            return model
        model = _text(getattr(action, "model_name", ""))
        if model:
            return model
        model_id = getattr(action, "model_id", None)
        model = _text(getattr(model_id, "model", ""))
        if model:
            return model
        binding_model_id = getattr(action, "binding_model_id", None)
        return _text(getattr(binding_model_id, "model", ""))
    except Exception:
        return ""


def _action_view_modes(action: Any) -> list[str]:
    try:
        value = _text(getattr(action, "view_mode", ""))
    except Exception:
        value = ""
    return [_text(item) for item in value.split(",") if _text(item)]


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

    def _catalog_source_db(self) -> str:
        try:
            configured = self.env["ir.config_parameter"].sudo().get_param(
                "smart_core.release_operator.catalog_source_db",
                "",
            )
        except Exception:
            configured = ""
        current_db = _text(getattr(getattr(self.env, "cr", None), "dbname", ""))
        return _text(configured) or current_db

    def _catalog_source_config(self, source_env) -> dict[str, str]:
        hook_payload = call_extension_hook_first(self.env, "smart_core_product_policy_catalog_source", self.env, source_env)
        payload = hook_payload if isinstance(hook_payload, dict) else {}
        module = _text(payload.get("module"))
        xmlid_prefix = _text(payload.get("xmlid_prefix"))
        root_label = _text(payload.get("root_label"))
        return {
            "module": module,
            "xmlid_prefix": xmlid_prefix,
            "root_label": root_label,
        }

    def _candidate_user_menus(self, source_env):
        config = self._catalog_source_config(source_env)
        module = _text(config.get("module"))
        if not module:
            return source_env["ir.ui.menu"].sudo().search([], order="sequence,id")
        try:
            rows = source_env["ir.model.data"].sudo().search(
                [
                    ("module", "=", module),
                    ("model", "=", "ir.ui.menu"),
                ]
            )
            menu_ids = [int(row.res_id or 0) for row in rows if int(row.res_id or 0) > 0]
            if menu_ids:
                menus = source_env["ir.ui.menu"].sudo().browse(menu_ids).exists()
                return sorted(menus, key=lambda menu: (int(getattr(menu, "sequence", 0) or 0), int(menu.id or 0)))
        except Exception:
            pass

        return source_env["ir.ui.menu"].sudo().search([], order="sequence,id")

    def _extract_user_menu_pages(self, source_env) -> list[dict[str, Any]]:
        # ir.ui.menu.search() applies menu visibility rules, and action is a
        # reference field whose domains may miss menus that still expose a
        # valid Python action.  The product policy is a platform catalog of the
        # real extension-owned menu surface, so resolve configured menu XMLIDs
        # through ir.model.data and browse the records directly.
        config = self._catalog_source_config(source_env)
        xmlid_prefix = _text(config.get("xmlid_prefix"))
        root_label = _text(config.get("root_label"))
        menus = self._candidate_user_menus(source_env)
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for menu in menus:
            if hasattr(menu, "active") and not bool(getattr(menu, "active")):
                continue
            xmlid = _menu_xmlid(menu)
            if xmlid_prefix and not xmlid.startswith(xmlid_prefix):
                continue
            action = menu.action
            action_id = _action_id(action)
            if action_id <= 0:
                continue
            path = _menu_path(menu)
            if not path:
                continue
            current_root_label = path[0] if path else ""
            if root_label and current_root_label != root_label:
                continue
            children = getattr(menu, "child_id", None)
            if children and any(bool(getattr(child, "active", True)) for child in children):
                continue
            page_key = xmlid
            if page_key in seen:
                continue
            seen.add(page_key)
            group_label = path[1] if len(path) > 1 else root_label
            page_label = path[-1]
            menu_id = int(menu.id or 0)
            res_model = _action_model(action)
            view_modes = _action_view_modes(action)
            resolved_scene_key = resolve_scene_key(
                source_env,
                menu_id=menu_id,
                action_id=action_id,
                model=res_model,
                view_modes=view_modes,
            )
            rows.append(
                {
                    "app_id": _slug(group_label),
                    "group_key": f"catalog.{_slug(group_label)}",
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
                    "target_scene_key": resolved_scene_key,
                    "action_id": action_id,
                    "action_model": _text(getattr(action, "_name", "")),
                    "res_model": res_model,
                    "view_modes": view_modes,
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
        source_db = self._catalog_source_db()
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

    def build_catalog_policy_payload(self, *, product_key: str) -> dict[str, Any]:
        identity = resolve_product_identity(product_key=product_key)
        menu_pages, menu_source = self._load_source_user_menu_pages()
        if menu_pages:
            return self._build_catalog_policy_payload_from_menu_pages(
                identity=identity,
                menu_pages=menu_pages,
                menu_source=menu_source,
            )
        label = self._catalog_product_label(identity=identity)
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

    def _catalog_product_label(self, *, identity: dict[str, str]) -> str:
        hook_payload = call_extension_hook_first(
            self.env,
            "smart_core_product_policy_catalog_label",
            self.env,
            identity,
        )
        value = _text(hook_payload)
        if value:
            return value
        return identity["product_key"]

    def _build_catalog_policy_payload_from_menu_pages(
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
        emitted_page_signatures: set[tuple[str, str, str]] = set()
        for index, page in enumerate(menu_pages, start=1):
            group_key = _text(page.get("group_key")) or "catalog.menu"
            group = groups_by_key.setdefault(
                group_key,
                {
                    "group_key": group_key,
                    "group_label": _text(page.get("group_label")) or "业务目录",
                    "category": "user_visible_menu",
                    "menus": [],
                },
            )
            page_key = _text(page.get("page_key"))
            label = _text(page.get("page_label") or page.get("label")) or page_key
            res_model = _text(page.get("res_model"))
            page_signature = (group_key, label, res_model)
            if res_model and page_signature in emitted_page_signatures:
                continue
            if res_model:
                emitted_page_signatures.add(page_signature)
            capability_key = f"catalog.menu.{_slug(page_key)}"
            target_scene_key = _text(page.get("target_scene_key"))
            menu = {
                "menu_key": _text(page.get("menu_key")) or page_key,
                "label": label,
                "page_key": page_key,
                "page_label": label,
                "route": _text(page.get("route")),
                "scene_key": _text(page.get("scene_key")),
                "product_key": _text(page.get("app_id")),
                "capability_key": capability_key,
                "target_scene_key": target_scene_key,
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
                "res_model": res_model,
                "view_modes": page.get("view_modes") if isinstance(page.get("view_modes"), list) else [],
                "sequence": index,
            }
            group["menus"].append(menu)
            if target_scene_key and target_scene_key not in scene_bindings:
                scene_rows.append(
                    {
                        "scene_key": target_scene_key,
                        "label": label,
                        "route": f"/s/{target_scene_key}",
                        "product_key": _text(page.get("app_id")),
                        "capability_key": capability_key,
                        "description": "Platform release projection for an industry menu/action page.",
                        "scope": menu["visible_menu_path"],
                        "source_kind": "ir.ui.menu",
                        "menu_xmlid": _text(page.get("menu_xmlid")),
                        "action_id": int(page.get("action_id") or 0),
                        "res_model": res_model,
                    }
                )
                scene_bindings[target_scene_key] = {"version": "v1", "channel": "stable"}
            capability_rows.append(
                {
                    "capability_key": capability_key,
                    "label": label,
                    "group_key": group_key,
                    "group_label": _text(page.get("group_label")) or "业务目录",
                    "target_scene_key": target_scene_key,
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
        label = self._catalog_product_label(identity=identity)
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
        if self._is_catalog_backed_product(identity=identity):
            return self.build_catalog_policy_payload(product_key=identity["product_key"])
        return ProductPolicyService(self.env).get_policy(product_key=identity["product_key"])

    def _is_catalog_backed_product(self, *, identity: dict[str, str]) -> bool:
        hook_payload = call_extension_hook_first(
            self.env,
            "smart_core_product_policy_catalog_base_keys",
            self.env,
        )
        values = hook_payload if isinstance(hook_payload, (list, tuple, set)) else []
        base_keys = {_text(item) for item in values if _text(item)}
        return _text(identity.get("base_product_key")) in base_keys

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
