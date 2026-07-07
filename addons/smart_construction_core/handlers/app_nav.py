# -*- coding: utf-8 -*-
# smart_construction_core/handlers/app_nav.py
import json, hashlib, logging, time
from typing import Any, Dict, List, Set
from odoo import api, SUPERUSER_ID
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.core.unified_page_contract_v2_client import (
    resolve_client_type,
    resolve_delivery_profile,
    trim_navigation_contract_for_client,
)
from .app_catalog import APP_DEFS, APP_DELIVERY_SOURCE_AUTHORITY, _feature_visible, _visible_menu_ids, _current_perms

_logger = logging.getLogger(__name__)

def _md5(d: Any) -> str:
    return hashlib.md5(json.dumps(d, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

def _feature_to_node(app_id: str, f: Dict[str,Any]) -> Dict[str,Any]:
    return {
        "key": f"feature:{app_id}:{f['key']}",
        "label": f["label"],
        "children": [],
        "meta": {"app": app_id, "feature": f["key"], "kind": f.get("kind","work"), "open": f.get("open")},
    }

def _params(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("params")
    if isinstance(nested, dict):
        merged = dict(payload)
        merged.update(nested)
        return merged
    return dict(payload)

def _headers(request) -> Dict[str, Any]:
    try:
        http_request = getattr(request, "httprequest", None)
        headers = getattr(http_request, "headers", None)
        if headers:
            return dict(headers)
    except Exception:
        _logger.debug("Unable to read app navigation request headers.", exc_info=True)
    return {}

class AppNavHandler(BaseIntentHandler):
    """
    意图：app.nav
    返回指定 App 的功能分区（work/reporting/config/ai）。
    """
    INTENT_TYPE = "app.nav"
    DESCRIPTION = "获取单个应用的功能分区与功能树"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    REQUIRED_GROUPS = []  # 登录用户皆可

    def handle(self, payload=None, ctx=None):
        payload = _params(payload)
        ts0 = time.time()
        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
        client_type = resolve_client_type(_headers(self.request), payload)
        delivery_profile = resolve_delivery_profile(client_type, payload)

        app_id = payload.get("app")
        if not app_id:
            app_id = "workspace"

        app = next((a for a in APP_DEFS if a["id"] == app_id), None)
        if not app:
            data = {
                "sections": [
                    {
                        "key": f"section:{app_id}:work",
                        "label": "工作",
                        "children": [],
                        "meta": {"section": "work", "fallback": True},
                    }
                ],
                "meta": {"fingerprint": _md5({"app": app_id, "fallback": True})},
            }
            data = trim_navigation_contract_for_client(
                data,
                client_type=client_type,
                delivery_profile=delivery_profile,
                max_items=payload.get("max_items") or payload.get("maxItems"),
                max_depth=payload.get("max_depth") or payload.get("maxDepth"),
            )
            meta = {"elapsed_ms": int((time.time()-ts0)*1000), "intent": self.INTENT_TYPE, "client_type": client_type, "delivery_profile": delivery_profile, "source_authority": APP_DELIVERY_SOURCE_AUTHORITY}
            top_etag = _md5({"fp": data["meta"]["fingerprint"], "uid": env.uid})
            return {"status":"success","data":data,"meta":{**meta,"etag":top_etag},"ok":True}

        visible_mids = _visible_menu_ids(env)
        perms = _current_perms(env)

        buckets = {"work": [], "reporting": [], "config": [], "ai": []}
        for f in app.get("features", []):
            if _feature_visible(env, su_env, f, visible_mids, perms):
                buckets[(f.get("kind") or "work")].append(_feature_to_node(app_id, f))

        sections = []
        for sec,label in (("work","工作"),("reporting","报告"),("config","配置"),("ai","智能")):
            if buckets[sec]:
                sections.append({
                    "key": f"section:{app_id}:{sec}",
                    "label": label,
                    "children": buckets[sec],
                    "meta": {"section": sec},
                })

        fp = _md5({"app": app_id, "ver": _md5(app), "uid": env.uid, "sec": sections})
        data = trim_navigation_contract_for_client(
            {"sections": sections, "meta": {"fingerprint": fp}},
            client_type=client_type,
            delivery_profile=delivery_profile,
            max_items=payload.get("max_items") or payload.get("maxItems"),
            max_depth=payload.get("max_depth") or payload.get("maxDepth"),
        )
        meta = {"elapsed_ms": int((time.time()-ts0)*1000), "intent": self.INTENT_TYPE, "client_type": client_type, "delivery_profile": delivery_profile, "source_authority": APP_DELIVERY_SOURCE_AUTHORITY}
        top_etag = _md5({"fp": fp, "uid": env.uid})
        return {"status":"success","data":data,"meta":{**meta,"etag":top_etag},"ok":True}
