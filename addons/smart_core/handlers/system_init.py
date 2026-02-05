# smart_core/handlers/system_init.py
# -*- coding: utf-8 -*-
import logging
import time
import json
import hashlib
import os
from typing import Iterable, Dict, List, Tuple

from odoo import api, SUPERUSER_ID

from ..core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.utils.misc import stable_etag, format_versions
from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY
from odoo.addons.smart_core.core.extension_loader import run_extension_hooks

_logger = logging.getLogger(__name__)

# Contract/API version markers for client compatibility
CONTRACT_VERSION = "v0.1"
API_VERSION = "v1"

# ===================== 工具函数（权限 / 指纹 / 导航净化） =====================

def _diagnostics_enabled(env) -> bool:
    env_flag = (os.environ.get("ENV") or "").lower()
    if env_flag in {"dev", "test", "local"}:
        return True
    try:
        return env.user.has_group("base.group_system")
    except Exception:
        return False

def _user_group_xmlids(user) -> set:
    """把用户组转为 xmlid 集合（与菜单过滤口径一致）"""
    ext_map = user.groups_id.sudo().get_external_id()  # {id: 'module.xmlid' or False}
    return {xml for xml in ext_map.values() if xml}

def _to_group_xmlid(env, g) -> str | None:
    """把 group 标识（xmlid 或 int id 或 res.groups 记录）统一转 xmlid"""
    if not g:
        return None
    if isinstance(g, str):
        # 允许直接是 xmlid（module.name）
        return g if "." in g else None
    if isinstance(g, int):
        imd = env["ir.model.data"].sudo().search([("model", "=", "res.groups"), ("res_id", "=", g)], limit=1)
        return f"{imd.module}.{imd.name}" if imd and imd.module and imd.name else None
    if getattr(g, "_name", None) == "res.groups":
        imd = env["ir.model.data"].sudo().search([("model", "=", "res.groups"), ("res_id", "=", g.id)], limit=1)
        return f"{imd.module}.{imd.name}" if imd and imd.module and imd.name else None
    return None

def _normalize_required_groups(env, required: Iterable) -> List[str]:
    """把 handler.REQUIRED_GROUPS 规范成 xmlid 列表（空=对所有登录用户开放）"""
    if not required:
        return []
    out = []
    for r in required:
        xmlid = _to_group_xmlid(env, r)
        if xmlid:
            out.append(xmlid)
    return out

def _has_required_groups(user_xmlids: set, required_xmlids: Iterable[str]) -> bool:
    req = set(required_xmlids or [])
    return (not req) or req.issubset(user_xmlids)

def _fingerprint(obj: dict) -> str:
    """稳定指纹（用于导航/顶层 ETag 计算）"""
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(payload.encode("utf-8")).hexdigest()

def _is_menu_node(node: dict) -> bool:
    """仅保留真正菜单节点（有 menu_id 或有 children 的分组）"""
    return bool(node.get("menu_id") or node.get("children"))

def _clean_nav(nodes: list) -> list:
    """去除“sig:*”等非菜单节点，递归清洗"""
    cleaned = []
    for n in nodes or []:
        if not _is_menu_node(n):
            continue
        c = dict(n)
        c["children"] = _clean_nav(n.get("children") or [])
        cleaned.append(c)
    return cleaned
# 在文件工具函数区追加：
def _to_xmlid_list(env, maybe_ids_or_xmlids):
    """
    输入可能是 [xmlid(str)] 或 [int id] 或混合，统一转 [xmlid(str)]
    """
    if not maybe_ids_or_xmlids:
        return []
    out = []
    int_ids = []
    for g in maybe_ids_or_xmlids:
        if isinstance(g, str) and "." in g:
            out.append(g)
        elif isinstance(g, int):
            int_ids.append(g)
    if int_ids:
        imds = env["ir.model.data"].sudo().search([
            ("model", "=", "res.groups"),
            ("res_id", "in", int_ids)
        ])
        # 建字典以便 O(1) 查找
        id2xml = {imd.res_id: f"{imd.module}.{imd.name}" for imd in imds if imd.module and imd.name}
        for gid in int_ids:
            if gid in id2xml:
                out.append(id2xml[gid])
    # 去重并保持稳定排序
    return sorted(set(out))

def _normalize_nav_groups(env, nodes):
    """
    递归把 nav[*].meta.groups_xmlids 统一成 xmlid(str) 列表
    """
    for n in nodes or []:
        meta = n.get("meta") or {}
        if "groups_xmlids" in meta and meta["groups_xmlids"]:
            meta["groups_xmlids"] = _to_xmlid_list(env, meta["groups_xmlids"])
            n["meta"] = meta
        if n.get("children"):
            _normalize_nav_groups(env, n["children"])

def _resolve_action_ids(env, action_xmlids: Dict[str, str]) -> Dict[int, str]:
    resolved = {}
    for xmlid, scene_key in action_xmlids.items():
        try:
            rec = env.ref(xmlid, raise_if_not_found=False)
            if rec and rec.id:
                resolved[rec.id] = scene_key
        except Exception:
            continue
    return resolved

def _normalize_view_mode(raw: str | None) -> str | None:
    if not raw:
        return None
    val = str(raw).strip().lower()
    if val in {"tree", "list", "kanban"}:
        return "list"
    if val in {"form"}:
        return "form"
    return val

def _apply_scene_keys(env, nodes):
    """
    Inject nav.node.scene_key using priority:
      menu_xmlid -> action_id -> model/view_mode
    Also ensure node.xmlid is emitted if menu_xmlid exists.
    """
    menu_map = {
        "smart_construction_demo.menu_sc_project_list_showcase": "projects.list",
        "smart_construction_core.menu_sc_project_initiation": "projects.intake",
    }
    action_xmlid_map = {
        "smart_construction_demo.action_sc_project_list_showcase": "projects.list",
        "smart_construction_core.action_project_initiation": "projects.intake",
    }
    action_id_map = _resolve_action_ids(env, action_xmlid_map)
    model_view_map = {
        ("project.project", "list"): "projects.list",
        ("project.project", "form"): "projects.intake",
    }

    for n in nodes or []:
        meta = n.get("meta") or {}
        menu_xmlid = meta.get("menu_xmlid") or n.get("xmlid")
        if menu_xmlid:
            n["xmlid"] = menu_xmlid
        scene_key = None
        if menu_xmlid and menu_xmlid in menu_map:
            scene_key = menu_map[menu_xmlid]
        if not scene_key:
            action_id = meta.get("action_id")
            if action_id in action_id_map:
                scene_key = action_id_map[action_id]
        if not scene_key:
            model = meta.get("model")
            view_mode = meta.get("view_mode") or meta.get("view_type")
            if not view_mode:
                view_modes = meta.get("view_modes")
                if isinstance(view_modes, list) and view_modes:
                    view_mode = view_modes[0]
            key = (model, _normalize_view_mode(view_mode)) if model else None
            if key in model_view_map:
                scene_key = model_view_map[key]
        if scene_key:
            n["scene_key"] = scene_key
            meta["scene_key"] = scene_key
            n["meta"] = meta
        if n.get("children"):
            _apply_scene_keys(env, n["children"])



def collect_available_intents(env, user) -> Tuple[List[str], Dict[str, dict]]:
    """
    从 HANDLER_REGISTRY 动态收集可用意图（按权限过滤）。
    返回：
      - intents: 只包含“主名”（INTENT_TYPE）的有序列表
      - intents_meta: 含版本与别名，供前端/调试可选使用
    """
    user_xmlids = _user_group_xmlids(user)
    intents: List[str] = []
    meta: Dict[str, dict] = {}

    # 遍历注册表（支持别名注册到同一类）
    for name, cls in HANDLER_REGISTRY.items():
        primary = getattr(cls, "INTENT_TYPE", None) or name
        version = getattr(cls, "VERSION", None)
        required = _normalize_required_groups(env, getattr(cls, "REQUIRED_GROUPS", []) or [])
        enabled = getattr(cls, "IS_ENABLED", True)
        aliases = []
        try:
            aliases = list(getattr(cls, "ALIASES") or [])
        except Exception:
            aliases = []

        # 仅按“主名”去重与授权（别名只进 meta，不重复入列）
        if not enabled:
            continue
        if not _has_required_groups(user_xmlids, required):
            continue
        if primary in intents:
            # 已收录主名，补齐 meta 即可
            if primary in meta:
                meta[primary].setdefault("aliases", [])
                meta[primary]["aliases"] = sorted(set((meta[primary]["aliases"] or []) + aliases))
            continue

        intents.append(primary)
        m = {}
        if version:
            m["version"] = version
        if aliases:
            m["aliases"] = aliases
        if required:
            m["required_groups"] = required  # 已是 xmlid
        meta[primary] = m

    intents.sort()
    return intents, meta

# ===================== Handler =====================

class SystemInitHandler(BaseIntentHandler):
    """
    意图：system.init（别名：app.init / bootstrap）
    一次性初始化：用户/环境、导航、默认首页契约（无数据）、可选预取
    """
    INTENT_TYPE = "system.init"
    DESCRIPTION = "系统初始化（用户/环境、导航、首页契约、可用意图清单），只读，支持细粒度 ETag"
    VERSION = "1.0.0"
    ETAG_ENABLED = True
    ALIASES = ["app.init", "bootstrap"]
    REQUIRED_GROUPS = []  # 登录用户可用

    def handle(self, payload=None, ctx=None):
        payload = payload or {}
        ts0 = time.time()
        params = payload.get("params") if isinstance(payload, dict) else None
        if not isinstance(params, dict):
            params = payload if isinstance(payload, dict) else {}
        
        diag_enabled = _diagnostics_enabled(self.env)
        diagnostic_info = None
        if diag_enabled:
            # 收集请求头信息（白名单）
            try:
                from odoo import http
                request = http.request
                headers = request.httprequest.headers
                x_odoo_db = headers.get("X-Odoo-DB")
                x_db = headers.get("X-DB")
                authorization = headers.get("Authorization")
            except Exception:
                x_odoo_db = None
                x_db = None
                authorization = None

            diagnostic_info = {
                "effective_db": self.env.cr.dbname if hasattr(self.env, "cr") and self.env.cr else "unknown",
                "db_source": "env_cr",
                "header_x_odoo_db": x_odoo_db,
                "header_x_db": x_db,
                "has_authorization": bool(authorization),
                "effective_root_xmlid": params.get("root_xmlid") if isinstance(params, dict) else None,
                "root_source": "params" if params and params.get("root_xmlid") else "default",
                "uid": self.env.uid,
                "login": self.env.user.login if hasattr(self.env, "user") else "unknown",
                "params_keys": list(params.keys()) if isinstance(params, dict) else [],
            }

            _logger.info("[B1] system.init 诊断信息: %s", diagnostic_info)
            _logger.info("[system_init][debug] params: %s", params)
            _logger.info("[system_init][debug] self.params: %s", getattr(self, "params", {}))
            _logger.info("[system_init][debug] self.env.cr.dbname: %s", self.env.cr.dbname)

        # 统一使用 self.env / self.su_env（不要直接用 odoo.http.request.env）
        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))

        # 如果 finalize_contract 内部不读 ORM，可用 env；若会读，推荐 su_env
        cs = ContractService(su_env)

        # -------- 1) 用户/环境 --------
        scene = params.get("scene") or "web"

        user = env.user
        user_groups_xmlids = _user_group_xmlids(user)

        user_dict = {
            "id": user.id,
            "name": user.name,
            "groups_xmlids": list(user_groups_xmlids),
            "lang": user.lang,
            "tz": user.tz,
            "company_id": user.company_id.id if user.company_id else None,
        }

        # -------- 2) 导航（净化 + 指纹）--------
        p_nav = {"subject": "nav", "scene": scene}
        if params.get("root_xmlid"):
            p_nav["root_xmlid"] = params.get("root_xmlid")
        if params.get("root_menu_id"):
            p_nav["root_menu_id"] = params.get("root_menu_id")
        nav_data, nav_versions = NavDispatcher(env, su_env).build_nav(p_nav)

        nav_tree_raw = nav_data.get("nav") or []
        nav_tree = _clean_nav(nav_tree_raw)
        # ✅ 统一 groups_xmlids 口径（字符串 xmlid）
        _normalize_nav_groups(env, nav_tree)
        _apply_scene_keys(env, nav_tree)
        nav_fp = _fingerprint({"scene": scene, "nav": nav_tree})

        default_home_action = (
            params.get("home_action_id")
            or nav_data.get("default_home_action")
            or None
        )

        # -------- 2.5) 可用意图（动态生成，严格基于注册+权限）--------
        intents, intents_meta = collect_available_intents(env, user)

        # -------- 3) 首页契约（无数据 | 仅算指纹，不直接塞入 preload）--------
        home_contract = None
        etags: Dict[str, str] = {}
        parts_version: Dict[str, str] = {}

        if default_home_action:
            try:
                p_home = {"subject": "action", "action_id": default_home_action, "with_data": False}
                home_data, home_versions = ActionDispatcher(env, su_env).dispatch(p_home)
                fixed = cs.finalize_contract({
                    "ok": True,
                    "data": home_data,
                    "meta": {"subject": "action", "version": format_versions(home_versions)}
                })
                home_contract = fixed.get("data")
                parts_version["home"] = format_versions(home_versions)
                etags["home"] = stable_etag(home_contract)
            except Exception as e:
                _logger.warning("system.init home preload failed: action=%s, err=%s", default_home_action, e)

        # -------- 4) 可选预取（仅结构指纹，不回传整包契约）--------
        preload_items = []
        want_preload = bool(params.get("with_preload", True))
        preload_actions = params.get("preload_actions") or []

        if want_preload and preload_actions:
            for act in preload_actions:
                try:
                    p_pre = {"subject": "action", "action_id": act, "with_data": False}
                    pre_data, pre_versions = ActionDispatcher(env, su_env).dispatch(p_pre)
                    fixed = cs.finalize_contract({
                        "ok": True,
                        "data": pre_data,
                        "meta": {"subject": "action", "version": format_versions(pre_versions)}
                    })
                    contract = fixed.get("data")
                    e = stable_etag(contract)
                    preload_items.append({"key": act, "etag": e})  # ✅ 仅返回 etag
                    parts_version[act] = format_versions(pre_versions)
                    etags[act] = e
                except Exception as e:
                    _logger.warning("system.init preload failed: action=%s, err=%s", act, e)
                    continue

        # -------- 5) 汇总返回（统一蛇形命名 + 导航指纹 + 动态意图）--------
        data = {
            "user": user_dict,
            "nav": nav_tree,
            "nav_meta": {                                                       # ✅ 导航指纹 + scope info
                "fingerprint": nav_fp,
                **(nav_versions or {}),
                "debug_params_keys": sorted(list(params.keys())) if isinstance(params, dict) else [],
                "debug_root_xmlid": params.get("root_xmlid") if isinstance(params, dict) else None,
            },
            "default_route": nav_data.get("defaultRoute") or {"menu_id": None},  # ✅ snake_case
            "intents": intents,                                                  # ✅ 动态意图（主名）
            "intents_meta": intents_meta,                                        # ⬅ 可选（前端可不用）
            "feature_flags": nav_data.get("feature_flags") or {"ai_enabled": True},
            "preload": [],
            "scenes": [],
            "scene_version": "v1",
        }
        if home_contract:
            data["preload"].append({"key": "home", "etag": etags.get("home")})   # ✅ 轻量化 preload
        if preload_items:
            data["preload"].extend(preload_items)

        # 扩展模块可附加场景/能力等（不影响主流程）
        run_extension_hooks(env, "smart_core_extend_system_init", data, env, user)

        # 分部 etag：加入导航
        etags["nav"] = nav_fp

        meta = {
            "elapsed_ms": int((time.time() - ts0) * 1000),
            "parts": {"nav": format_versions(nav_versions), **parts_version},
            "etags": etags,
            "intent": self.INTENT_TYPE,
            "contract_version": CONTRACT_VERSION,
            "api_version": API_VERSION,
        }
        if diag_enabled and diagnostic_info is not None:
            data["diagnostic"] = diagnostic_info

        # 顶层 ETag：纳入用户、导航指纹、默认路由、特性开关、可用意图
        top_etag = stable_etag({
            "user": data["user"],
            "nav_fp": nav_fp,
            "default_route": data["default_route"],
            "feature_flags": data["feature_flags"],
            "intents": data["intents"],
            "scenes": data.get("scenes"),
            "capabilities": data.get("capabilities"),
            "contract_version": CONTRACT_VERSION,
            "api_version": API_VERSION,
        })

        return {"status": "success", "data": data, "meta": {**meta, "etag": top_etag}, "ok": True}
