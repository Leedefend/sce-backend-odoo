# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from ..core.base_handler import BaseIntentHandler
from ..core.handler_registry import HANDLER_REGISTRY
from ..core.intent_execution_result import IntentExecutionResult
from ..core.request_params import parse_positive_int
from ..core.unified_page_contract_v2_assembler import CONTRACT_VERSION
from ..core.unified_page_contract_v2_client import resolve_client_type, resolve_delivery_profile


class TerminalShellV2Handler(BaseIntentHandler):
    INTENT_TYPE = "terminal.shell.v2"
    DESCRIPTION = "终端启动契约 v2；后端定义 app、默认入口、裁剪菜单和打开目标"
    VERSION = CONTRACT_VERSION
    SOURCE_KIND = "terminal_shell_contract_v2"
    SOURCE_AUTHORITIES = ("app.catalog", "app.nav", "app.open", "ui.contract.v2")
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

    def handle(self, payload: Optional[Dict[str, Any]] = None, ctx: Optional[Dict[str, Any]] = None):
        ts0 = time.time()
        params = self._params(payload)
        client_type = resolve_client_type(self._headers(), params)
        delivery_profile = resolve_delivery_profile(client_type, params)
        selected_app = str(params.get("app") or params.get("app_id") or params.get("appId") or "").strip()
        max_items, max_items_error = self._read_optional_positive(params, "max_items", "maxItems")
        if max_items_error:
            return self._error(400, "max_items 无效", ts0=ts0, client_type=client_type, delivery_profile=delivery_profile)
        max_depth, max_depth_error = self._read_optional_positive(params, "max_depth", "maxDepth")
        if max_depth_error:
            return self._error(400, "max_depth 无效", ts0=ts0, client_type=client_type, delivery_profile=delivery_profile)

        catalog = self._call("app.catalog", {
            "client_type": client_type,
            "delivery_profile": delivery_profile,
            "scene": params.get("scene") or "web",
        }, ctx)
        apps = self._apps(catalog.get("data"))
        default_app = selected_app or self._default_app_id(catalog.get("data"), apps)

        nav = self._call("app.nav", {
            "app": default_app,
            "client_type": client_type,
            "delivery_profile": delivery_profile,
            "max_items": max_items or 8,
            "max_depth": max_depth or 2,
        }, ctx) if default_app else {"ok": True, "data": {"sections": [], "meta": {}}}

        default_entry = self._default_entry(default_app, nav.get("data"))
        open_target = {}
        if default_entry.get("appId") and default_entry.get("featureKey"):
            opened = self._call("app.open", {
                "app": default_entry.get("appId"),
                "feature": default_entry.get("featureKey"),
                "client_type": client_type,
                "delivery_profile": delivery_profile,
            }, ctx)
            open_target = opened.get("data") if isinstance(opened.get("data"), dict) else {}
        elif default_entry.get("sceneKey"):
            open_target = {
                "subject": "ui.contract",
                "scene_key": default_entry.get("sceneKey"),
                "route": f"/s/{default_entry.get('sceneKey')}",
            }
        elif default_app:
            opened = self._call("app.open", {
                "app": default_app,
                "client_type": client_type,
                "delivery_profile": delivery_profile,
            }, ctx)
            open_target = opened.get("data") if isinstance(opened.get("data"), dict) else {}
        if not default_entry and open_target:
            scene_key = self._text(open_target.get("scene_key"))
            default_entry = {
                "key": scene_key or "default.open",
                "label": scene_key or "默认入口",
                "appId": default_app,
                "featureKey": "",
                "sceneKey": scene_key,
                "open": open_target,
            }

        data = {
            "shellVersion": CONTRACT_VERSION,
            "clientType": client_type,
            "deliveryProfile": delivery_profile,
            "apps": apps,
            "activeAppId": default_app,
            "navigation": nav.get("data") if isinstance(nav.get("data"), dict) else {"sections": [], "meta": {}},
            "defaultEntry": default_entry,
            "defaultOpenTarget": open_target,
            "renderContractIntent": "ui.contract.v2",
            "meta": {
                "catalogIntent": "app.catalog",
                "navIntent": "app.nav",
                "openIntent": "app.open",
            },
        }
        return IntentExecutionResult(
            ok=True,
            data=data,
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "contract_version": CONTRACT_VERSION,
                "client_type": client_type,
                "delivery_profile": delivery_profile,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": self.source_authority_contract(),
            },
        )

    def _error(self, code: int, message: str, *, ts0: float, client_type: str, delivery_profile: str):
        return IntentExecutionResult(
            ok=False,
            data=None,
            error={"code": code, "message": message},
            code=code,
            meta={
                "intent": self.INTENT_TYPE,
                "version": self.VERSION,
                "contract_version": CONTRACT_VERSION,
                "client_type": client_type,
                "delivery_profile": delivery_profile,
                "elapsed_ms": int((time.time() - ts0) * 1000),
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": self.source_authority_contract(),
            },
        )

    def _read_optional_positive(self, params: dict[str, Any], *keys: str):
        for key in keys:
            if key in params:
                value, error = parse_positive_int(params.get(key), allow_empty=True)
                return value, error
        return None, None

    def _call(self, intent: str, params: dict[str, Any], ctx: Optional[Dict[str, Any]]) -> dict[str, Any]:
        handler_cls = HANDLER_REGISTRY.get(intent)
        if handler_cls is None:
            return {"ok": False, "error": {"code": 404, "message": f"Unknown intent: {intent}"}, "data": {}}
        handler = handler_cls(
            env=self.env,
            su_env=self.su_env,
            request=self.request,
            context=ctx or self.context,
            payload=params,
        )
        result = handler.run(payload={"intent": intent, "params": params, "context": ctx or {}}, ctx=ctx or {})
        return self._envelope(result)

    def _apps(self, data: Any) -> list[dict[str, Any]]:
        rows = []
        for row in self._list(self._dict(data).get("apps")):
            if not isinstance(row, dict):
                continue
            meta = self._dict(row.get("meta"))
            app_id = self._text(meta.get("app_id") or row.get("app_id") or row.get("id") or row.get("key")).removeprefix("app:")
            if not app_id:
                continue
            rows.append({
                "id": app_id,
                "key": self._text(row.get("key"), app_id),
                "label": self._text(row.get("label") or row.get("title"), app_id),
                "icon": row.get("icon"),
                "badges": self._dict(row.get("badges")),
                "meta": meta,
            })
        return rows

    def _default_app_id(self, data: Any, apps: list[dict[str, Any]]) -> str:
        meta = self._dict(self._dict(data).get("meta"))
        configured = self._text(meta.get("default_app_id") or meta.get("defaultAppId"))
        if configured:
            return configured
        for app in apps:
            if not bool(self._dict(app.get("meta")).get("fallback")):
                return self._text(app.get("id"))
        return self._text(apps[0].get("id")) if apps else "workspace"

    def _default_entry(self, app_id: str, nav_data: Any) -> dict[str, Any]:
        first = self._first_leaf(self._list(self._dict(nav_data).get("sections")))
        if not first:
            return {}
        meta = self._dict(first.get("meta"))
        open_payload = self._dict(meta.get("open"))
        feature_key = self._text(meta.get("feature") or first.get("key")).removeprefix(f"feature:{app_id}:")
        scene_key = self._text(open_payload.get("scene_key") or meta.get("scene_key") or first.get("scene_key"))
        return {
            "key": self._text(first.get("key"), scene_key or feature_key),
            "label": self._text(first.get("label") or first.get("title"), scene_key or feature_key),
            "appId": self._text(meta.get("app"), app_id),
            "featureKey": feature_key,
            "sceneKey": scene_key,
            "open": open_payload,
        }

    def _first_leaf(self, rows: list[Any]) -> dict[str, Any]:
        for row in rows:
            if not isinstance(row, dict):
                continue
            children = self._list(row.get("children"))
            if not children:
                meta = self._dict(row.get("meta"))
                if self._dict(meta.get("open")) or self._text(meta.get("feature")) or self._text(row.get("scene_key")):
                    return row
                continue
            child = self._first_leaf(children)
            if child:
                return child
        return {}

    def _params(self, payload: Optional[Dict[str, Any]]) -> dict[str, Any]:
        if isinstance(payload, dict):
            nested = payload.get("params")
            if isinstance(nested, dict):
                merged = dict(payload)
                merged.update(nested)
                return merged
            return dict(payload)
        return dict(self.params) if isinstance(self.params, dict) else {}

    def _headers(self) -> dict[str, Any]:
        try:
            http_request = getattr(self.request, "httprequest", None)
            headers = getattr(http_request, "headers", None)
            if headers:
                return dict(headers)
        except Exception:
            pass
        return {}

    def _envelope(self, result: Any) -> dict[str, Any]:
        if isinstance(result, IntentExecutionResult):
            return result.to_legacy_dict()
        if isinstance(result, dict):
            return result
        return {"ok": True, "data": result or {}, "meta": {}}

    def _dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _list(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def _text(self, value: Any, fallback: str = "") -> str:
        text = str(value or "").strip()
        return text or fallback
