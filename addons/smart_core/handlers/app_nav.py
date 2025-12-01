# -*- coding: utf-8 -*-
# smart_core/handlers/app_nav.py
import json, hashlib, logging, time
from typing import Any, Dict, List, Set
from odoo import api, SUPERUSER_ID
from ..core.base_handler import BaseIntentHandler
from .app_catalog import APP_DEFS, _xmlid_to_id, _visible_menu_ids, _current_perms, _installed_modules

_logger = logging.getLogger(__name__)

def _md5(d: Any) -> str:
    return hashlib.md5(json.dumps(d, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

def _feature_visible(env, su_env, f: Dict[str,Any], visible_mids: Set[int], perms: Set[str]) -> bool:
    need = set(f.get("required_permissions") or [])
    if need and not need.issubset(perms):
        return False
    o = f.get("open") or {}
    mid = _xmlid_to_id(su_env, o.get("odoo_menu_xmlid"))
    aid = _xmlid_to_id(su_env, o.get("odoo_action_xmlid"))
    return (mid and mid in visible_mids) or (aid is not None) or o.get("internal_route") or o.get("workflow_id")

def _feature_to_node(app_id: str, f: Dict[str,Any]) -> Dict[str,Any]:
    return {
        "key": f"feature:{app_id}:{f['key']}",
        "label": f["label"],
        "children": [],
        "meta": {"app": app_id, "feature": f["key"], "kind": f.get("kind","work"), "open": f.get("open")},
    }

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
        payload = payload or {}
        ts0 = time.time()
        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))

        app_id = payload.get("app")
        if not app_id:
            raise ValueError("missing param: app")

        app = next((a for a in APP_DEFS if a["id"] == app_id), None)
        if not app:
            raise ValueError(f"unknown app: {app_id}")

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
        data = {"sections": sections, "meta": {"fingerprint": fp}}
        meta = {"elapsed_ms": int((time.time()-ts0)*1000), "intent": self.INTENT_TYPE}
        top_etag = _md5({"fp": fp, "uid": env.uid})
        return {"status":"success","data":data,"meta":{**meta,"etag":top_etag},"ok":True}
