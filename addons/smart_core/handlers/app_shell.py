# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.request_params import parse_positive_int
from odoo.addons.smart_core.core.scene_provider import load_scenes_from_db_or_fallback
from odoo.addons.smart_core.core.unified_page_contract_v2_client import (
    resolve_client_type,
    resolve_delivery_profile,
    trim_navigation_contract_for_client,
)
from odoo.addons.smart_core.delivery.native_config_menu_projection import (
    native_config_app_children,
    native_config_available,
)
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
try:
    from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin
except Exception:
    def user_is_platform_admin(user):
        return False


def _md5(payload: Any) -> str:
    return hashlib.md5(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def _text(value: Any) -> str:
    return str(value or "").strip()


PLATFORM_APP_TAXONOMY: dict[str, dict[str, Any]] = {
    "workspace": {"label": "角色首页", "category": "platform", "sequence": 0, "primary_scene": "workspace.home"},
    "my_work": {"label": "我的工作", "category": "productivity", "sequence": 70, "primary_scene": "my_work.workspace"},
    "data": {"label": "数据中心", "category": "platform", "sequence": 200, "primary_scene": "data.dictionary"},
    "config": {"label": "业务配置", "category": "platform", "sequence": 210, "primary_scene": "config.center"},
    "enterprise": {"label": "企业组织", "category": "platform", "sequence": 220, "primary_scene": "enterprise.company"},
    "portal": {"label": "门户工作台", "category": "platform", "sequence": 230, "primary_scene": "portal.dashboard"},
    "delivery": {"label": "交付控制", "category": "platform", "sequence": 240, "primary_scene": "delivery.command"},
}

APP_TAXONOMY = PLATFORM_APP_TAXONOMY
APP_ALIASES: dict[str, str] = {}

HIDDEN_APP_IDS = {"default", "scene_smoke_default"}
PLATFORM_ADMIN_SCENE_APP_IDS = {"delivery"}

ADMIN_APP_DEFS: dict[str, dict[str, Any]] = {
    "release_management": {
        "label": "产品发布",
        "category": "platform_admin",
        "sequence": -20,
        "route": "/admin/release-operator?product_key=platform.standard",
        "scene_key": "release.operator",
        "intent": "release.operator.surface",
        "action_xmlid": "smart_core.action_sc_product_policy",
        "menu_xmlid": "smart_core.menu_smart_core_release_root",
    },
    "company_access": {
        "label": "公司访问",
        "category": "platform_admin",
        "sequence": -10,
        "action_xmlid": "smart_core.action_sc_subscription_plan",
        "menu_xmlid": "smart_core.menu_smart_core_company_access_root",
    },
}


def _scene_list(env) -> List[Dict[str, Any]]:
    payload = load_scenes_from_db_or_fallback(env, drift=None, logger=None) or {}
    scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    return [scene for scene in scenes if isinstance(scene, dict)]


def _scene_key(scene: Dict[str, Any]) -> str:
    return _text(scene.get("code") or scene.get("key"))


def _scene_label(scene: Dict[str, Any]) -> str:
    return _text(scene.get("title") or scene.get("label") or scene.get("name") or _scene_key(scene))


def _app_shell_contract(env) -> dict[str, Any]:
    payload = call_extension_hook_first(env, "smart_core_app_shell_contract", env)
    return payload if isinstance(payload, dict) else {}


def _app_taxonomy_registry(env=None) -> dict[str, dict[str, Any]]:
    registry = {key: dict(value) for key, value in PLATFORM_APP_TAXONOMY.items()}
    extension_taxonomy = _app_shell_contract(env).get("taxonomy")
    if isinstance(extension_taxonomy, dict):
        for key, value in extension_taxonomy.items():
            app_id = _text(key)
            if app_id and isinstance(value, dict):
                registry[app_id] = dict(value)
    return registry


def _app_aliases(env=None) -> dict[str, str]:
    aliases = {}
    extension_aliases = _app_shell_contract(env).get("aliases")
    if isinstance(extension_aliases, dict):
        aliases.update({_text(key): _text(value) for key, value in extension_aliases.items() if _text(key) and _text(value)})
    return aliases


def _scene_app_id(scene_key: str, env=None) -> str:
    key = _text(scene_key).lower()
    if not key:
        return "workspace"
    head = key.split(".", 1)[0]
    return _app_aliases(env).get(head, head) or "workspace"


def _is_publishable_scene(scene: Dict[str, Any]) -> bool:
    key = _scene_key(scene)
    if not key:
        return False
    app_id = _scene_app_id(key)
    if app_id in HIDDEN_APP_IDS:
        return False
    return True


def _app_taxonomy(app_id: str, env=None) -> dict[str, Any]:
    app_key = _text(app_id)
    return _app_taxonomy_registry(env).get(app_key) or {
        "label": app_key,
        "category": "industry",
        "sequence": 900,
        "primary_scene": "",
    }


def _app_label(app_id: str, env=None) -> str:
    return _text(_app_taxonomy(app_id, env=env).get("label")) or app_id


def _app_category(app_id: str, env=None) -> str:
    return _text(_app_taxonomy(app_id, env=env).get("category")) or "industry"


def _app_sequence(app_id: str, env=None) -> int:
    try:
        value = _app_taxonomy(app_id, env=env).get("sequence")
        return int(value) if value is not None else 900
    except Exception:
        return 900


def _scene_sequence(scene: dict[str, Any], env=None) -> tuple[int, str]:
    key = _scene_key(scene)
    app_id = _scene_app_id(key, env=env)
    primary = _text(_app_taxonomy(app_id, env=env).get("primary_scene"))
    if key == primary:
        return (0, key)
    return (100, key)


def _scene_sort_key(scene: dict[str, Any], env=None) -> tuple[int, str]:
    return _scene_sequence(scene, env=env)


def _primary_scene_for_app(app_id: str, scenes: list[dict[str, Any]], env=None) -> str:
    primary = _text(_app_taxonomy(app_id, env=env).get("primary_scene"))
    scene_keys = {_scene_key(scene) for scene in scenes}
    if primary and primary in scene_keys:
        return primary
    ordered = sorted([scene for scene in scenes if _scene_key(scene)], key=lambda scene: _scene_sort_key(scene, env=env))
    return _scene_key(ordered[0]) if ordered else ""


def _scene_route(scene: Dict[str, Any]) -> str:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    route = _text(target.get("route"))
    if route:
        return route
    key = _scene_key(scene)
    return f"/s/{key}" if key else "/"


def _xmlid_record(env, xmlid: str):
    try:
        return env.ref(xmlid, raise_if_not_found=False)
    except Exception:
        return None


def _record_visible_to_user(record: Any, user: Any) -> bool:
    groups = getattr(record, "groups_id", None)
    if not groups:
        return True
    user_groups = getattr(user, "groups_id", None)
    try:
        if user_groups and groups & user_groups:
            return True
    except Exception:
        pass
    try:
        group_xmlids = groups.get_external_id()
    except Exception:
        group_xmlids = {}
    for group in groups:
        xmlid = group_xmlids.get(getattr(group, "id", None)) if isinstance(group_xmlids, dict) else ""
        if not xmlid:
            continue
        try:
            if user.has_group(xmlid):
                return True
        except Exception:
            continue
    return False


def _scene_accessible_for_user(env, scene: dict[str, Any]) -> bool:
    key = _scene_key(scene)
    app_id = _scene_app_id(key, env=env)
    if app_id == "workspace":
        return True
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    xmlids = [
        _text(target.get("menu_xmlid")),
        _text(target.get("action_xmlid")),
    ]
    declared_xmlids = [xmlid for xmlid in xmlids if xmlid]
    for xmlid in declared_xmlids:
        record = _xmlid_record(env, xmlid)
        if _is_platform_admin_user(env) and not getattr(record, "groups_id", None):
            continue
        if record and _record_visible_to_user(record, env.user):
            return True
    if declared_xmlids:
        return False
    if _is_platform_admin_user(env):
        return app_id in PLATFORM_ADMIN_SCENE_APP_IDS
    return True


def _is_platform_admin_user(env) -> bool:
    try:
        return bool(user_is_platform_admin(env.user))
    except Exception:
        return False


def _is_scene_app_visible_for_user(env, app_id: str) -> bool:
    token = _text(app_id)
    if token in PLATFORM_ADMIN_SCENE_APP_IDS:
        return _is_platform_admin_user(env)
    return True


def _admin_app_rows(env) -> list[dict[str, Any]]:
    if not _is_platform_admin_user(env):
        return []
    rows: list[dict[str, Any]] = []
    for app_id, spec in ADMIN_APP_DEFS.items():
        action = _xmlid_record(env, _text(spec.get("action_xmlid")))
        if not action:
            continue
        rows.append(
            {
                "key": f"app:{app_id}",
                "label": _text(spec.get("label")) or app_id,
                "icon": None,
                "badges": {"count": 0},
                "meta": {
                    "app_id": app_id,
                    "category": _text(spec.get("category")) or "platform_admin",
                    "sequence": int(spec.get("sequence") or 0),
                    "action_xmlid": _text(spec.get("action_xmlid")),
                    "menu_xmlid": _text(spec.get("menu_xmlid")),
                    "admin_only": True,
                },
            }
        )
    return rows


def _admin_app_target(env, app_id: str) -> dict[str, Any]:
    spec = ADMIN_APP_DEFS.get(_text(app_id)) or {}
    route = _text(spec.get("route"))
    if route:
        return {
            "subject": "ui.contract",
            "scene_key": _text(spec.get("scene_key")) or app_id,
            "route": route,
            "intent": _text(spec.get("intent")),
            "name": _text(spec.get("label")) or app_id,
        }
    action = _xmlid_record(env, _text(spec.get("action_xmlid")))
    if not action:
        return {}
    return {
        "subject": "action",
        "id": int(action.id),
        "action_id": int(action.id),
        "model": _text(getattr(action, "res_model", "")),
        "view_type": _text(getattr(action, "view_mode", "")).split(",", 1)[0] or "tree",
        "name": _text(getattr(action, "name", "")),
    }


def _headers(request) -> dict[str, Any]:
    try:
        http_request = getattr(request, "httprequest", None)
        headers = getattr(http_request, "headers", None)
        if headers:
            return dict(headers)
    except Exception:
        pass
    return {}


def _params(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("params")
    if isinstance(nested, dict):
        merged = dict(payload)
        merged.update(nested)
        return merged
    return dict(payload)


class _SceneDeliveryAppShellMixin:
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": cls.INTENT_TYPE,
        }

    def _source_meta(self, *, ts0: float, extra: dict | None = None) -> dict:
        meta = {
            "intent": self.INTENT_TYPE,
            "elapsed_ms": int((time.time() - ts0) * 1000),
            "source_kind": self.SOURCE_KIND,
            "source_authorities": list(self.SOURCE_AUTHORITIES),
            "source_authority": self.source_authority_contract(),
        }
        if isinstance(extra, dict):
            meta.update(extra)
        return meta

    def _err(self, code: int, message: str, *, ts0: float):
        return {
            "status": "error",
            "ok": False,
            "code": code,
            "error": {"code": code, "message": message},
            "data": None,
            "meta": self._source_meta(ts0=ts0),
        }


class AppCatalogHandler(_SceneDeliveryAppShellMixin, BaseIntentHandler):
    INTENT_TYPE = "app.catalog"
    DESCRIPTION = "平台级应用目录（通用兜底）"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    REQUIRED_GROUPS = []
    SOURCE_KIND = "scene_delivery_catalog_projection"
    SOURCE_AUTHORITIES = ("sc.scene", "ui_base_contract_asset")

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        scenes = [
            scene
            for scene in _scene_list(self.env)
            if _is_publishable_scene(scene)
            and _is_scene_app_visible_for_user(self.env, _scene_app_id(_scene_key(scene), env=self.env))
            and _scene_accessible_for_user(self.env, scene)
        ]
        app_scenes: Dict[str, list[dict[str, Any]]] = {}
        for scene in scenes:
            app_id = _scene_app_id(_scene_key(scene), env=self.env)
            app_scenes.setdefault(app_id, []).append(scene)

        apps = [
            {
                "key": f"app:{app_id}",
                "label": _app_label(app_id, env=self.env),
                "icon": None,
                "badges": {"count": len(items)},
                "meta": {
                    "app_id": app_id,
                    "category": _app_category(app_id, env=self.env),
                    "sequence": _app_sequence(app_id, env=self.env),
                    "primary_scene": _primary_scene_for_app(app_id, items, env=self.env),
                },
            }
            for app_id, items in app_scenes.items()
        ]
        apps = sorted(
            apps,
            key=lambda item: (
                int((item.get("meta") or {}).get("sequence") if (item.get("meta") or {}).get("sequence") is not None else 900),
                str(item.get("label") or ""),
            ),
        )
        apps = _admin_app_rows(self.env) + apps
        app_ids = {
            _text((item.get("meta") or {}).get("app_id"))
            for item in apps
            if isinstance(item.get("meta"), dict)
        }
        if "config" not in app_ids and native_config_available(self.env):
            config_children = native_config_app_children(self.env)
            apps.append(
                {
                    "key": "app:config",
                    "label": _app_label("config", env=self.env),
                    "icon": None,
                    "badges": {"count": len(config_children)},
                    "meta": {
                        "app_id": "config",
                        "category": _app_category("config", env=self.env),
                        "sequence": _app_sequence("config", env=self.env),
                        "primary_scene": _text(_app_taxonomy("config", env=self.env).get("primary_scene")),
                        "source": "native_odoo_menu_fallback",
                    },
                }
            )
            apps = sorted(
                apps,
                key=lambda item: (
                    int((item.get("meta") or {}).get("sequence") if (item.get("meta") or {}).get("sequence") is not None else 900),
                    str(item.get("label") or ""),
                ),
            )
        if "workspace" not in app_scenes and "workspace" not in app_ids:
            apps.insert(
                0,
                {
                    "key": "app:workspace",
                    "label": _app_label("workspace", env=self.env),
                    "icon": None,
                    "badges": {"count": 0},
                    "meta": {
                        "app_id": "workspace",
                        "category": _app_category("workspace", env=self.env),
                        "sequence": _app_sequence("workspace", env=self.env),
                        "primary_scene": "workspace.home",
                        "fallback": True,
                    },
                },
            )
        if not apps:
            apps = [{
                "key": "app:workspace",
                "label": _app_label("workspace", env=self.env),
                "icon": None,
                "badges": {"count": 0},
                "meta": {
                    "app_id": "workspace",
                    "category": _app_category("workspace", env=self.env),
                    "sequence": _app_sequence("workspace", env=self.env),
                    "primary_scene": "workspace.home",
                },
            }]

        fp = _md5({"uid": self.env.uid, "apps": [item.get("key") for item in apps]})
        return {
            "status": "success",
            "ok": True,
            "data": {"apps": apps, "meta": {"fingerprint": fp, "scene": "web"}},
            "meta": self._source_meta(ts0=ts0, extra={"etag": fp}),
        }


class AppNavHandler(_SceneDeliveryAppShellMixin, BaseIntentHandler):
    INTENT_TYPE = "app.nav"
    DESCRIPTION = "平台级应用导航（通用兜底）"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    REQUIRED_GROUPS = []
    SOURCE_KIND = "scene_delivery_navigation_projection"
    SOURCE_AUTHORITIES = ("sc.scene", "ui_base_contract_asset")

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        env = self.env
        payload = _params(payload)
        client_type = resolve_client_type(_headers(self.request), payload)
        delivery_profile = resolve_delivery_profile(client_type, payload)
        max_items, max_items_error = _read_optional_positive(payload, "max_items", "maxItems")
        if max_items_error:
            return self._err(400, "max_items 无效", ts0=ts0)
        max_depth, max_depth_error = _read_optional_positive(payload, "max_depth", "maxDepth")
        if max_depth_error:
            return self._err(400, "max_depth 无效", ts0=ts0)
        raw_app_id = _text(payload.get("app") or "workspace")
        app_id = _app_aliases(env).get(raw_app_id, raw_app_id)
        if app_id in ADMIN_APP_DEFS and _is_platform_admin_user(env):
            target = _admin_app_target(env, app_id)
            if target:
                return {
                    "status": "success",
                    "ok": True,
                    "data": {
                        "sections": [
                            {
                                "key": f"section:{app_id}:admin",
                                "label": "管理",
                                "children": [
                                    {
                                        "key": f"feature:{app_id}:default",
                                        "label": _text(target.get("name")) or _text(ADMIN_APP_DEFS[app_id].get("label")),
                                        "children": [],
                                        "meta": {"app": app_id, "feature": "default", "kind": "admin", "open": target},
                                    }
                                ],
                                "meta": {"section": "admin"},
                            }
                        ],
                        "meta": {"fingerprint": _md5({"uid": env.uid, "app": app_id, "admin": True})},
                    },
                    "meta": self._source_meta(ts0=ts0, extra={"etag": _md5({"uid": env.uid, "app": app_id, "admin": True})}),
                }
        scenes = [
            scene
            for scene in _scene_list(self.env)
            if _is_publishable_scene(scene)
            and _scene_app_id(_scene_key(scene), env=env) == app_id
            and _is_scene_app_visible_for_user(env, app_id)
            and _scene_accessible_for_user(env, scene)
        ]

        children = [
            {
                "key": _scene_key(scene),
                "label": _scene_label(scene),
                "children": [],
                "meta": {
                    "app": app_id,
                    "feature": _scene_key(scene),
                    "kind": "work",
                    "open": {"internal_route": _scene_route(scene), "scene_key": _scene_key(scene)},
                },
            }
            for scene in sorted(scenes, key=lambda scene: _scene_sort_key(scene, env=env))
            if _scene_key(scene)
        ]
        if app_id == "config":
            native_children = native_config_app_children(env)
            if native_children:
                children = native_children

        sections = []
        if children:
            sections.append({"key": f"section:{app_id}:work", "label": "工作", "children": children, "meta": {"section": "work"}})

        fp = _md5({"uid": self.env.uid, "app": app_id, "sections": [row.get("key") for row in sections]})
        data = trim_navigation_contract_for_client(
            {"sections": sections, "meta": {"fingerprint": fp}},
            client_type=client_type,
            delivery_profile=delivery_profile,
            max_items=max_items,
            max_depth=max_depth,
        )
        return {
            "status": "success",
            "ok": True,
            "data": data,
            "meta": self._source_meta(
                ts0=ts0,
                extra={
                    "etag": fp,
                    "client_type": client_type,
                    "delivery_profile": delivery_profile,
                },
            ),
        }


def _read_optional_positive(payload: dict[str, Any], *keys: str):
    for key in keys:
        if key in payload:
            value, error = parse_positive_int(payload.get(key), allow_empty=True)
            return value, error
    return None, None


class AppOpenHandler(_SceneDeliveryAppShellMixin, BaseIntentHandler):
    INTENT_TYPE = "app.open"
    DESCRIPTION = "平台级应用打开（通用兜底）"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = []
    SOURCE_KIND = "scene_delivery_open_projection"
    SOURCE_AUTHORITIES = ("sc.scene", "ui_base_contract_asset", "ui.contract")

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        payload = _params(payload)
        feature_key = _text(payload.get("feature") or payload.get("scene_key"))
        scene_key = feature_key
        if not scene_key:
            raw_app_id = _text(payload.get("app") or "workspace")
            app_id = _app_aliases(self.env).get(raw_app_id, raw_app_id)
            if app_id in ADMIN_APP_DEFS and _is_platform_admin_user(self.env):
                target = _admin_app_target(self.env, app_id)
                if target:
                    return {
                        "status": "success",
                        "ok": True,
                        "data": target,
                        "meta": self._source_meta(ts0=ts0),
                    }
            scenes = [
                scene
                for scene in _scene_list(self.env)
                if _is_publishable_scene(scene)
                and _scene_app_id(_scene_key(scene), env=self.env) == app_id
                and _is_scene_app_visible_for_user(self.env, app_id)
                and _scene_accessible_for_user(self.env, scene)
            ]
            primary_scene = _primary_scene_for_app(app_id, scenes, env=self.env)
            if primary_scene:
                scene_key = primary_scene
            for scene in sorted(scenes, key=lambda scene: _scene_sort_key(scene, env=self.env)):
                if scene_key:
                    break
                key = _scene_key(scene)
                if key and _scene_app_id(key, env=self.env) == app_id:
                    scene_key = key
                    break
            if not scene_key and app_id == "workspace":
                scene_key = "workspace.home"
        if not scene_key:
            raise ValueError("missing param: app / feature")

        return {
            "status": "success",
            "ok": True,
            "data": {"subject": "ui.contract", "scene_key": scene_key, "route": f"/s/{scene_key}"},
            "meta": self._source_meta(ts0=ts0),
        }
