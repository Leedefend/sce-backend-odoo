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


def _md5(payload: Any) -> str:
    return hashlib.md5(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _scene_list(env) -> List[Dict[str, Any]]:
    payload = load_scenes_from_db_or_fallback(env, drift=None, logger=None) or {}
    scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    return [scene for scene in scenes if isinstance(scene, dict)]


def _scene_key(scene: Dict[str, Any]) -> str:
    return _text(scene.get("code") or scene.get("key"))


def _scene_label(scene: Dict[str, Any]) -> str:
    return _text(scene.get("title") or scene.get("label") or scene.get("name") or _scene_key(scene))


def _scene_app_id(scene_key: str) -> str:
    key = _text(scene_key).lower()
    if not key:
        return "workspace"
    head = key.split(".", 1)[0]
    return head or "workspace"


def _scene_route(scene: Dict[str, Any]) -> str:
    target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
    route = _text(target.get("route"))
    if route:
        return route
    key = _scene_key(scene)
    return f"/s/{key}" if key else "/"


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
        scenes = _scene_list(self.env)
        app_counts: Dict[str, int] = {}
        for scene in scenes:
            app_id = _scene_app_id(_scene_key(scene))
            app_counts[app_id] = int(app_counts.get(app_id) or 0) + 1

        apps = [
            {
                "key": f"app:{app_id}",
                "label": app_id,
                "icon": None,
                "badges": {"count": count},
                "meta": {"app_id": app_id},
            }
            for app_id, count in sorted(app_counts.items())
        ]
        if "workspace" not in app_counts:
            apps.insert(
                0,
                {
                    "key": "app:workspace",
                    "label": "workspace",
                    "icon": None,
                    "badges": {"count": 0},
                    "meta": {"app_id": "workspace", "fallback": True},
                },
            )
        if not apps:
            apps = [{"key": "app:workspace", "label": "workspace", "icon": None, "badges": {"count": 0}, "meta": {"app_id": "workspace"}}]

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
        payload = _params(payload)
        client_type = resolve_client_type(_headers(self.request), payload)
        delivery_profile = resolve_delivery_profile(client_type, payload)
        max_items, max_items_error = _read_optional_positive(payload, "max_items", "maxItems")
        if max_items_error:
            return self._err(400, "max_items 无效", ts0=ts0)
        max_depth, max_depth_error = _read_optional_positive(payload, "max_depth", "maxDepth")
        if max_depth_error:
            return self._err(400, "max_depth 无效", ts0=ts0)
        app_id = _text(payload.get("app") or "workspace")
        scenes = [scene for scene in _scene_list(self.env) if _scene_app_id(_scene_key(scene)) == app_id]

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
            for scene in scenes
            if _scene_key(scene)
        ]

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
        payload = payload or {}
        feature_key = _text(payload.get("feature") or payload.get("scene_key"))
        scene_key = feature_key
        if not scene_key:
            app_id = _text(payload.get("app") or "workspace")
            for scene in _scene_list(self.env):
                key = _scene_key(scene)
                if key and _scene_app_id(key) == app_id:
                    scene_key = key
                    break
        if not scene_key:
            raise ValueError("missing param: app / feature")

        return {
            "status": "success",
            "ok": True,
            "data": {"subject": "ui.contract", "scene_key": scene_key, "route": f"/s/{scene_key}"},
            "meta": self._source_meta(ts0=ts0),
        }
