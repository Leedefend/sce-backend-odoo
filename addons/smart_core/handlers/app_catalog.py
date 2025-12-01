# -*- coding: utf-8 -*-
# smart_core/handlers/app_catalog.py
import json, hashlib, logging, time
from typing import Any, Dict, List, Set

from odoo import api, SUPERUSER_ID
from ..core.base_handler import BaseIntentHandler

_logger = logging.getLogger(__name__)

# ====== 最小可跑：内置一个 App 定义（后续替换为 DB/YAML/服务加载） ======
APP_DEFS: List[Dict[str, Any]] = [
    {
        "id": "project_management",
        "label": "项目管理",
        "icon": "project,static/description/icon.png",
        "scene": "web",
        "category": "运营",
        "requires": ["project", "documents"],
        "plans": ["base", "pro", "enterprise"],
        "flags": [],  # 例如 ["ai_enabled"]
        "features": [
            {
                "key": "project_overview",
                "label": "项目总览",
                "kind": "work",
                "open": {"odoo_action_xmlid": "project.action_project_project"},
                "required_permissions": ["project.view_all"],
            },
            {
                "key": "task_board",
                "label": "任务看板",
                "kind": "work",
                "open": {"odoo_action_xmlid": "project.action_view_task_kanban"},
                "required_permissions": ["project.view_all"],
            },
            {
                "key": "report_task_analysis",
                "label": "任务分析报表",
                "kind": "reporting",
                "open": {"odoo_action_xmlid": "project.action_project_task_report"},
                "required_permissions": ["project.report_task"],
            },
            {
                "key": "config_stage",
                "label": "阶段模板配置",
                "kind": "config",
                "open": {"odoo_menu_xmlid": "project.menu_project_config_project"},
                "required_permissions": ["project.manage_stage"],
            },
            {
                "key": "ai_risk_summary",
                "label": "AI 风险摘要",
                "kind": "ai",
                "open": {"internal_route": "/ai/project/risk_summary"},
                "required_permissions": ["ai.analysis"],
            },
        ],
    },
]

def _md5(d: Any) -> str:
    return hashlib.md5(json.dumps(d, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

def _xmlid_to_id(su_env, xmlid: str | None) -> int | None:
    if not xmlid: return None
    rec = su_env.ref(xmlid, raise_if_not_found=False)
    return int(rec.id) if rec else None

def _installed_modules(su_env) -> Set[str]:
    return set(su_env["ir.module.module"].search([("state","=","installed")]).mapped("name"))

def _visible_menu_ids(env) -> Set[int]:
    try:
        return set(env["ir.ui.menu"]._visible_menu_ids())
    except Exception:
        return set()

def _current_perms(env) -> Set[str]:
    try:
        return set(env["perm.aggregator"].current_permissions())
    except Exception:
        return set()

def _feature_visible(env, su_env, f: Dict[str,Any], visible_mids: Set[int], perms: Set[str]) -> bool:
    need = set(f.get("required_permissions") or [])
    if need and not need.issubset(perms):
        return False
    o = f.get("open") or {}
    mid = _xmlid_to_id(su_env, o.get("odoo_menu_xmlid"))
    aid = _xmlid_to_id(su_env, o.get("odoo_action_xmlid"))
    # 目标可达性：菜单可见 或 指定动作存在 或 内部路由/工作流
    reachable = (mid and mid in visible_mids) or (aid is not None) or o.get("internal_route") or o.get("workflow_id")
    return bool(reachable)

def _app_allowed(env, su_env, app: Dict[str,Any], scene: str) -> bool:
    if app.get("scene","web") != scene:
        return False
    installed = _installed_modules(su_env)
    if not set(app.get("requires") or []).issubset(installed):
        return False
    plan = getattr(env["tenant.context"], "plan", lambda: "base")()
    plans = set(app.get("plans") or [])
    if plans and plan not in plans:
        return False
    flags_need = set(app.get("flags") or [])
    user_flags = set(getattr(env["feature.flag"], "flags_for", lambda u: [])(env.user))
    if flags_need and not flags_need.issubset(user_flags):
        return False
    visible_mids = _visible_menu_ids(env)
    perms = _current_perms(env)
    return any(_feature_visible(env, su_env, f, visible_mids, perms) for f in app.get("features", []))

def _apps_fingerprint(env, su_env, apps_out: List[Dict[str,Any]]) -> str:
    visible_mids = list(_visible_menu_ids(env))
    max_write = None
    if visible_mids:
        max_write = max(su_env["ir.ui.menu"].browse(visible_mids).mapped("write_date") or [None])
    payload = {
        "apps": [a.get("meta",{}).get("app_id") or a.get("key") for a in apps_out],
        "uid": env.uid,
        "groups": sorted(set(env.user.get_external_id().values() or [])),
        "visible_count": len(visible_mids),
        "visible_max_write": str(max_write),
        "installed": sorted(_installed_modules(su_env)),
    }
    return _md5(payload)

class AppCatalogHandler(BaseIntentHandler):
    """
    意图：app.catalog
    返回“当前用户可用的 App 列表”，用于登录后渲染左侧应用目录。
    """
    INTENT_TYPE = "app.catalog"
    DESCRIPTION = "获取用户可用的产品级应用列表"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    REQUIRED_GROUPS = []  # 登录用户皆可

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        ts0 = time.time()
        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
        scene = payload.get("scene") or "web"

        apps_out: List[Dict[str,Any]] = []
        for app in APP_DEFS:
            if _app_allowed(env, su_env, app, scene):
                apps_out.append({
                    "key": f"app:{app['id']}",
                    "label": app["label"],
                    "icon": app.get("icon"),
                    "badges": self._badges_for(app),
                    "meta": {"app_id": app["id"], "category": app.get("category")},
                })

        fp = _apps_fingerprint(env, su_env, apps_out)
        data = {"apps": apps_out, "meta": {"fingerprint": fp, "scene": scene}}
        meta = {"elapsed_ms": int((time.time()-ts0)*1000), "intent": self.INTENT_TYPE}
        # 顶层 ETag：以 fingerprint 为主
        top_etag = _md5({"fp": fp, "uid": env.uid})
        return {"status":"success","data":data,"meta":{**meta,"etag":top_etag},"ok":True}

    # 简易徽标：可并发/超时降级，这里做一个“我的未完成任务数”示意
    def _badges_for(self, app: Dict[str,Any]) -> Dict[str,int]:
        try:
            if app["id"] == "project_management":
                todo = self.env["project.task"].search_count([
                    ("user_ids","in",[self.env.uid]),
                    ("stage_id.fold","=",False)
                ])
                return {"todo": int(todo)}
        except Exception:
            return {}
        return {}
