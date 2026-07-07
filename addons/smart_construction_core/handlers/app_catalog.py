# -*- coding: utf-8 -*-
# smart_construction_core/handlers/app_catalog.py
import json, hashlib, logging, time
from typing import Any, Dict, List, Set

from odoo import api, SUPERUSER_ID
from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin

_logger = logging.getLogger(__name__)

APP_DELIVERY_SOURCE_AUTHORITY = {
    "kind": "app_delivery_catalog_projection",
    "authorities": [
        "ir.ui.menu",
        "ir.actions",
        "ir.module.module",
        "res.groups",
        "perm.aggregator",
        "project.task",
    ],
    "projection_only": True,
    "delivery_only": True,
    "no_business_fact_authority": True,
}

# Built-in delivery catalog used when runtime package metadata is not provided.
APP_DEFS: List[Dict[str, Any]] = [
    {
        "id": "project_management",
        "label": "项目管理",
        "icon": "project,static/description/icon.png",
        "scene": "web",
        "category": "运营",
        "requires": ["project"],
        "plans": ["base", "pro", "enterprise"],
        "flags": [],  # 例如 ["ai_enabled"]
        "features": [
            {
                "key": "project_initiation",
                "label": "项目立项",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_project_initiation"},
            },
            {
                "key": "my_projects",
                "label": "我的项目",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_project_my_list"},
            },
            {
                "key": "project_ledger",
                "label": "项目台账",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_project_list"},
            },
            {
                "key": "project_dashboard",
                "label": "项目驾驶舱",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_project_dashboard"},
            },
            {
                "key": "contract_overview",
                "label": "合同汇总",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_project_contract_overview"},
            },
            {
                "key": "project_cost_ledger",
                "label": "成本台账",
                "kind": "reporting",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_project_cost_ledger_my"},
            },
            {
                "key": "project_documents",
                "label": "项目资料",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_project_document"},
            },
        ],
    },
    {
        "id": "contract_management",
        "label": "合同管理",
        "icon": None,
        "scene": "web",
        "category": "运营",
        "requires": ["smart_construction_core"],
        "plans": ["base", "pro", "enterprise"],
        "flags": [],
        "features": [
            {
                "key": "my_contracts",
                "label": "我的合同",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_construction_contract_my"},
            },
            {
                "key": "income_contracts",
                "label": "收入合同台账",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_income_contract_ledger"},
            },
            {
                "key": "expense_contracts",
                "label": "支出合同台账",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_expense_contract_ledger"},
            },
            {
                "key": "general_contracts",
                "label": "一般合同",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_general_contract"},
            },
            {
                "key": "my_contract_reviews",
                "label": "待我审批",
                "kind": "work",
                "open": {"odoo_action_xmlid": "smart_construction_core.action_sc_tier_review_my_construction_contract"},
            },
        ],
    },
]

def _md5(d: Any) -> str:
    return hashlib.md5(json.dumps(d, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()

def _params(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("params")
    if isinstance(nested, dict):
        merged = dict(payload)
        merged.update(nested)
        return merged
    return dict(payload)

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

def _is_system_admin(env) -> bool:
    try:
        return bool(user_is_platform_admin(env.user))
    except Exception:
        return False

def _current_plan(env) -> str:
    try:
        model = env["tenant.context"]
    except Exception:
        return "base"
    try:
        plan_fn = getattr(model, "plan", None)
        if callable(plan_fn):
            return str(plan_fn() or "base")
    except Exception:
        _logger.debug("Unable to resolve tenant plan for app catalog.", exc_info=True)
    return "base"

def _feature_flags_for_user(env) -> Set[str]:
    try:
        model = env["feature.flag"]
    except Exception:
        return set()
    try:
        flags_for = getattr(model, "flags_for", None)
        if callable(flags_for):
            return set(flags_for(env.user) or [])
    except Exception:
        _logger.debug("Unable to resolve feature flags for app catalog.", exc_info=True)
    return set()

def _feature_visible(env, su_env, f: Dict[str,Any], visible_mids: Set[int], perms: Set[str]) -> bool:
    need = set(f.get("required_permissions") or [])
    if need and not need.issubset(perms) and not _is_system_admin(env):
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
    plan = _current_plan(env)
    plans = set(app.get("plans") or [])
    if plans and plan not in plans:
        return False
    flags_need = set(app.get("flags") or [])
    user_flags = _feature_flags_for_user(env)
    if flags_need and not flags_need.issubset(user_flags) and not _is_system_admin(env):
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
        payload = _params(payload)
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

        if not any((app.get("meta") or {}).get("app_id") == "workspace" for app in apps_out):
            apps_out.insert(0, {
                "key": "app:workspace",
                "label": "角色首页",
                "icon": None,
                "badges": {"todo": 0},
                "meta": {"app_id": "workspace", "category": "platform", "fallback": True},
            })

        if not apps_out:
            apps_out.append({
                "key": "app:workspace",
                "label": "角色首页",
                "icon": None,
                "badges": {"todo": 0},
                "meta": {"app_id": "workspace", "category": "platform", "fallback": True},
            })

        fp = _apps_fingerprint(env, su_env, apps_out)
        data = {"apps": apps_out, "meta": {"fingerprint": fp, "scene": scene}}
        meta = {"elapsed_ms": int((time.time()-ts0)*1000), "intent": self.INTENT_TYPE, "source_authority": APP_DELIVERY_SOURCE_AUTHORITY}
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
