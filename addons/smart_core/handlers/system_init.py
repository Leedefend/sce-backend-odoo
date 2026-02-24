# smart_core/handlers/system_init.py
# -*- coding: utf-8 -*-
import logging
import time
import json
import hashlib
import os
from typing import Iterable, Dict, List, Tuple

from odoo import api, fields, SUPERUSER_ID

from ..core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.utils.misc import stable_etag, format_versions
from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY
from odoo.addons.smart_core.core.extension_loader import run_extension_hooks
from odoo.addons.smart_core.core.scene_provider import (
    load_scene_contract as provider_load_scene_contract,
    load_scenes_from_db_or_fallback as provider_load_scenes_from_db_or_fallback,
    merge_missing_scenes_from_registry as provider_merge_missing_scenes_from_registry,
    resolve_scene_channel as provider_resolve_scene_channel,
)
from odoo.addons.smart_core.core.capability_provider import (
    build_capability_groups as provider_build_capability_groups,
    load_capabilities_for_user as provider_load_capabilities_for_user,
)
from odoo.addons.smart_core.core.contract_assembler import ContractAssembler
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.governance.scene_drift_engine import (
    SceneDriftEngine,
    append_resolve_error as drift_append_resolve_error,
    is_critical_drift_warn as drift_is_critical_drift_warn,
)
from odoo.addons.smart_core.governance.capability_surface_engine import CapabilitySurfaceEngine
from odoo.addons.smart_core.governance.scene_normalizer import SceneNormalizer
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver
from odoo.addons.smart_core.runtime.auto_degrade_engine import AutoDegradeEngine
from odoo.addons.smart_core.utils.reason_codes import (
    REASON_OK,
    REASON_PERMISSION_DENIED,
    failure_meta_for_reason,
)
from odoo.addons.smart_core.utils.contract_governance import (
    apply_contract_governance,
    is_truthy,
    normalize_capabilities,
    resolve_contract_mode,
)

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

def _load_capabilities_for_user(env, user) -> List[dict]:
    return provider_load_capabilities_for_user(env, user)


def _merge_extension_facts(data: dict) -> None:
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        return
    # Transitional compatibility: keep top-level reads stable while enforcing
    # extension hooks to write facts into a namespaced container only.
    core_facts = ext_facts.get("smart_construction_core")
    if isinstance(core_facts, dict):
        for key in ("entitlements", "usage"):
            if key in core_facts and key not in data:
                data[key] = core_facts.get(key)

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

def _get_request_header(name: str) -> str | None:
    try:
        from odoo import http
        request = http.request
        if not request or not request.httprequest:
            return None
        return request.httprequest.headers.get(name)
    except Exception:
        return None

def _resolve_scene_channel(env, user, params: dict | None) -> tuple[str, str, str]:
    return provider_resolve_scene_channel(env, user, params, get_header=_get_request_header)

def _load_scene_contract(env, scene_channel: str, use_pinned: bool) -> tuple[dict | None, str]:
    return provider_load_scene_contract(env, scene_channel, use_pinned, logger=_logger)
def _build_scene_health_payload(data: dict, trace_id: str = "", company_id: int | None = None) -> dict:
    data = data or {}
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    diag = data.get("scene_diagnostics") if isinstance(data.get("scene_diagnostics"), dict) else {}
    resolve_errors = diag.get("resolve_errors") if isinstance(diag.get("resolve_errors"), list) else []
    drift = diag.get("drift") if isinstance(diag.get("drift"), list) else []
    normalize_warnings = diag.get("normalize_warnings") if isinstance(diag.get("normalize_warnings"), list) else []

    critical_resolve_errors = [
        entry for entry in resolve_errors
        if isinstance(entry, dict) and str(entry.get("severity") or "").strip().lower() == "critical"
    ]
    critical_drift_warn = [entry for entry in drift if drift_is_critical_drift_warn(entry)]

    debt = []
    for entry in resolve_errors:
        if not isinstance(entry, dict):
            continue
        severity = str(entry.get("severity") or "").strip().lower()
        if severity != "critical":
            debt.append({"type": "resolve_error", **entry})
    for entry in drift:
        if not isinstance(entry, dict):
            continue
        if not drift_is_critical_drift_warn(entry):
            debt.append({"type": "drift", **entry})
    for entry in normalize_warnings:
        if isinstance(entry, dict):
            debt.append({"type": "normalize_warning", **entry})

    resolved_company_id = company_id
    if resolved_company_id is None:
        raw_company_id = user.get("company_id") if isinstance(user, dict) else None
        try:
            resolved_company_id = int(raw_company_id) if raw_company_id else None
        except Exception:
            resolved_company_id = None

    return {
        "company_id": resolved_company_id,
        "scene_channel": data.get("scene_channel"),
        "rollback_active": bool(diag.get("rollback_active")),
        "scene_version": data.get("scene_version"),
        "schema_version": data.get("schema_version"),
        "contract_ref": data.get("scene_contract_ref"),
        "summary": {
            "critical_resolve_errors_count": len(critical_resolve_errors),
            "critical_drift_warn_count": len(critical_drift_warn),
            "non_critical_debt_count": len(debt),
        },
        "details": {
            "resolve_errors": resolve_errors,
            "drift": drift,
            "debt": debt,
        },
        "auto_degrade": diag.get("auto_degrade") if isinstance(diag.get("auto_degrade"), dict) else {
            "triggered": False,
            "reason_codes": [],
            "action_taken": "none",
        },
        "last_updated_at": fields.Datetime.now(),
        "trace_id": trace_id or "",
    }


def _merge_missing_scenes_from_registry(env, scenes, warnings):
    return provider_merge_missing_scenes_from_registry(env, scenes, warnings)


def collect_available_intents(env, user) -> Tuple[List[str], Dict[str, dict]]:
    """
    从 HANDLER_REGISTRY 动态收集可用意图（按权限过滤）。
    返回：
      - intents: 只包含“主名”（INTENT_TYPE）的有序列表
      - intents_meta: 含版本与别名，供前端/调试可选使用
    """
    user_xmlids = IdentityResolver().user_group_xmlids(user)
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
        contract_mode = resolve_contract_mode(params)
        trace_id = ""
        try:
            trace_id = str((self.context or {}).get("trace_id") or "")
        except Exception:
            trace_id = ""

        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))

        scene_channel, channel_selector, channel_source_ref = _resolve_scene_channel(env, env.user, params)
        pinned_param = params.get("scene_use_pinned") if isinstance(params, dict) else None
        rollback_param = params.get("scene_rollback") if isinstance(params, dict) else None
        try:
            rollback_active = bool(self.get_bool("scene_use_pinned", False) or self.get_bool("scene_rollback", False))
        except Exception:
            rollback_active = is_truthy(pinned_param) or is_truthy(rollback_param)
        if pinned_param is not None and str(pinned_param).strip() not in {"", "0", "false", "no", "off"}:
            rollback_active = True
        try:
            config = env["ir.config_parameter"].sudo()
            rollback_active = rollback_active or is_truthy(config.get_param("sc.scene.use_pinned")) or                 is_truthy(config.get_param("sc.scene.rollback"))
        except Exception:
            pass
        rollback_active = rollback_active or is_truthy(os.environ.get("SCENE_USE_PINNED")) or             is_truthy(os.environ.get("SCENE_ROLLBACK"))
        if rollback_active:
            scene_channel = "stable"
        
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
                "scene_channel_param": params.get("scene_channel") if isinstance(params, dict) else None,
                "scene_use_pinned_param": params.get("scene_use_pinned") if isinstance(params, dict) else None,
                "scene_rollback_param": params.get("scene_rollback") if isinstance(params, dict) else None,
            }

            _logger.info("[B1] system.init 诊断信息: %s", diagnostic_info)
            _logger.info("[system_init][debug] params: %s", params)
            _logger.info("[system_init][debug] self.params: %s", getattr(self, "params", {}))
            _logger.info("[system_init][debug] self.env.cr.dbname: %s", self.env.cr.dbname)

        # 如果 finalize_contract 内部不读 ORM，可用 env；若会读，推荐 su_env
        cs = ContractService(su_env)

        # -------- 1) 用户/环境 --------
        scene = params.get("scene") or "web"

        user = env.user
        identity_resolver = IdentityResolver()
        user_groups_xmlids = identity_resolver.user_group_xmlids(user)

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
        nav_adapter = OdooNavAdapter()
        nav_adapter.enrich(env, nav_tree)
        nav_fp = _fingerprint({"scene": scene, "nav": nav_tree})
        if nav_versions and nav_versions.get("root_filtered_fallback"):
            _logger.warning(
                "NAV_ROOT_FILTERED_FALLBACK_USED uid=%s root_xmlid=%s trace=%s",
                env.uid,
                params.get("root_xmlid"),
                self.trace_id if hasattr(self, "trace_id") else None,
            )

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
            "capabilities": normalize_capabilities(_load_capabilities_for_user(env, user)),
            "capability_groups": [],
            "preload": [],
            "scenes": [],
            "scene_version": "v1",
            "schema_version": "v1",
            "scene_channel": scene_channel,
            "scene_channel_selector": channel_selector,
            "scene_channel_source_ref": channel_source_ref,
            "scene_contract_ref": None,
            "contract_mode": contract_mode,
            "ext_facts": {},
        }
        scene_diagnostics = {
            "schema_version": data.get("schema_version"),
            "scene_version": data.get("scene_version"),
            "loaded_from": None,
            "normalize_warnings": [],
            "resolve_errors": [],
            "drift": [],
            "rollback_active": bool(rollback_active),
            "rollback_ref": None,
            "channel_selector": channel_selector,
            "channel_source_ref": channel_source_ref,
            "auto_degrade": {"triggered": False, "reason_codes": [], "action_taken": "none"},
            "timings": {},
        }
        scene_normalizer = SceneNormalizer()
        scene_drift_engine = SceneDriftEngine()
        auto_degrade_engine = AutoDegradeEngine()
        capability_surface_engine = CapabilitySurfaceEngine()
        contract_assembler = ContractAssembler()
        scene_normalizer.append_act_url_deprecations(nav_tree, scene_diagnostics["normalize_warnings"])
        if home_contract:
            data["preload"].append({"key": "home", "etag": etags.get("home")})   # ✅ 轻量化 preload
        if preload_items:
            data["preload"].extend(preload_items)

        # 扩展模块可附加场景/能力等（不影响主流程）
        run_extension_hooks(env, "smart_core_extend_system_init", data, env, user)
        _merge_extension_facts(data)

        # Scene orchestration source (contract export or smart_construction_scene)
        contract_payload, contract_ref = _load_scene_contract(env, scene_channel, rollback_active)
        data["scene_contract_ref"] = contract_ref
        if rollback_active:
            scene_diagnostics["rollback_ref"] = contract_ref
        if contract_payload:
            data["scenes"] = contract_payload.get("scenes") or []
            data["scene_version"] = contract_payload.get("scene_version") or data.get("scene_version")
            data["schema_version"] = contract_payload.get("schema_version") or data.get("schema_version")
            scene_diagnostics["scene_version"] = data.get("scene_version")
            scene_diagnostics["schema_version"] = data.get("schema_version")
            scene_diagnostics["loaded_from"] = "contract"
            data["scenes"] = _merge_missing_scenes_from_registry(env, data.get("scenes"), scene_diagnostics["normalize_warnings"])
        else:
            t_load_start = time.time()
            scene_source = provider_load_scenes_from_db_or_fallback(
                env,
                drift=scene_diagnostics["drift"],
                logger=_logger,
            )
            scene_diagnostics["loaded_from"] = scene_source.get("loaded_from") or "fallback"
            scene_diagnostics["timings"]["load_ms"] = int((time.time() - t_load_start) * 1000)
            scenes_payload = scene_source.get("scenes") if isinstance(scene_source.get("scenes"), list) else []
            if scenes_payload:
                data["scenes"] = scenes_payload
                data["scene_version"] = scene_source.get("scene_version") or data.get("scene_version")
                data["schema_version"] = scene_source.get("schema_version") or data.get("schema_version")
                scene_diagnostics["scene_version"] = data.get("scene_version")
                scene_diagnostics["schema_version"] = data.get("schema_version")

        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        t_norm_start = time.time()
        scene_normalizer.normalize_structure(
            scenes_payload,
            nav_tree,
            data.get("capabilities"),
            scene_diagnostics,
        )
        scene_diagnostics["timings"]["normalize_ms"] = int((time.time() - t_norm_start) * 1000)
        nav_targets = scene_normalizer.index_nav_scene_targets(nav_tree)
        t_resolve_start = time.time()
        scene_normalizer.resolve_targets(
            env,
            scenes_payload,
            nav_tree,
            scene_diagnostics,
            nav_targets=nav_targets,
        )
        scene_drift_engine.evaluate(scenes_payload, scene_diagnostics)
        scene_diagnostics["timings"]["resolve_ms"] = int((time.time() - t_resolve_start) * 1000)

        # dev/test 下允许注入 critical 诊断，供 system-bound auto-degrade smoke 使用
        if is_truthy(params.get("scene_inject_critical_error")) and _diagnostics_enabled(env):
            drift_append_resolve_error(
                scene_diagnostics["resolve_errors"],
                scene_key="projects.list",
                kind="target",
                code="TEST_CRITICAL_INJECTED",
                ref="smart_construction_scene.test.injected",
                message="injected critical resolve error for auto-degrade smoke",
                severity="critical",
            )

        auto_degrade = auto_degrade_engine.evaluate(
            env,
            scene_diagnostics,
            user,
            trace_id,
            scene_channel,
        )
        scene_diagnostics["auto_degrade"] = auto_degrade
        if auto_degrade.get("triggered"):
            action_taken = auto_degrade.get("action_taken") or "rollback_pinned"
            scene_channel = "stable"
            rollback_active = action_taken == "rollback_pinned"
            data["scene_channel"] = scene_channel
            data["scene_contract_ref"] = "stable/PINNED.json" if rollback_active else "stable/LATEST.json"
            scene_diagnostics["rollback_active"] = bool(rollback_active)
            scene_diagnostics["rollback_ref"] = data["scene_contract_ref"] if rollback_active else None

            degraded_payload, degraded_ref = _load_scene_contract(env, scene_channel, rollback_active)
            data["scene_contract_ref"] = degraded_ref
            if rollback_active:
                scene_diagnostics["rollback_ref"] = degraded_ref
            if degraded_payload:
                data["scenes"] = degraded_payload.get("scenes") or []
                data["scene_version"] = degraded_payload.get("scene_version") or data.get("scene_version")
                data["schema_version"] = degraded_payload.get("schema_version") or data.get("schema_version")
                scene_diagnostics["scene_version"] = data.get("scene_version")
                scene_diagnostics["schema_version"] = data.get("schema_version")
                scene_diagnostics["loaded_from"] = "contract"
                scene_diagnostics["resolve_errors"] = []
                scene_diagnostics["drift"] = []
                scene_diagnostics["normalize_warnings"] = []
                data["scenes"] = _merge_missing_scenes_from_registry(env, data.get("scenes"), scene_diagnostics["normalize_warnings"])
                t_norm2 = time.time()
                scene_normalizer.normalize_structure(
                    data["scenes"],
                    nav_tree,
                    data.get("capabilities"),
                    scene_diagnostics,
                )
                scene_diagnostics["timings"]["normalize_after_degrade_ms"] = int((time.time() - t_norm2) * 1000)
                t_resolve2 = time.time()
                scene_normalizer.resolve_targets(
                    env,
                    data["scenes"],
                    nav_tree,
                    scene_diagnostics,
                    nav_targets=nav_targets,
                )
                scene_drift_engine.evaluate(data["scenes"], scene_diagnostics)
                scene_diagnostics["timings"]["resolve_after_degrade_ms"] = int((time.time() - t_resolve2) * 1000)
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else scenes_payload
        data["scenes"] = scenes_payload
        pre_governance_scene_count = len(data.get("scenes") or []) if isinstance(data.get("scenes"), list) else 0
        pre_governance_capability_count = (
            len(data.get("capabilities") or []) if isinstance(data.get("capabilities"), list) else 0
        )
        data = apply_contract_governance(data, contract_mode)
        data["capability_groups"] = provider_build_capability_groups(data.get("capabilities") or [])
        data["capability_surface_summary"] = capability_surface_engine.build_summary(
            data.get("capabilities") or [],
            data.get("capability_groups") or [],
        )
        post_governance_scene_count = len(data.get("scenes") or []) if isinstance(data.get("scenes"), list) else 0
        post_governance_capability_count = (
            len(data.get("capabilities") or []) if isinstance(data.get("capabilities"), list) else 0
        )
        scene_diagnostics["governance"] = {
            "contract_mode": contract_mode,
            "before": {
                "scene_count": pre_governance_scene_count,
                "capability_count": pre_governance_capability_count,
            },
            "after": {
                "scene_count": post_governance_scene_count,
                "capability_count": post_governance_capability_count,
            },
            "filtered": {
                "scene_count": max(0, pre_governance_scene_count - post_governance_scene_count),
                "capability_count": max(0, pre_governance_capability_count - post_governance_capability_count),
            },
        }
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        scene_keys_latest = {
            (s.get("code") or s.get("key"))
            for s in scenes_payload
            if isinstance(s, dict) and (s.get("code") or s.get("key"))
        }
        data["role_surface"] = identity_resolver.build_role_surface(user_groups_xmlids, nav_tree, scene_keys_latest)
        data["role_surface_map"] = identity_resolver.build_role_surface_map_payload()
        if contract_mode == "hud":
            data["scene_diagnostics"] = scene_diagnostics

        # 分部 etag：加入导航
        etags["nav"] = nav_fp

        elapsed_ms = int((time.time() - ts0) * 1000)
        scene_trace_meta = contract_assembler.build_scene_trace_meta(data, scene_diagnostics, elapsed_ms)
        meta = contract_assembler.build_meta(
            elapsed_ms=elapsed_ms,
            nav_versions=format_versions(nav_versions),
            parts_version=parts_version,
            etags=etags,
            intent_type=self.INTENT_TYPE,
            contract_version=CONTRACT_VERSION,
            api_version=API_VERSION,
            contract_mode=contract_mode,
            scene_trace_meta=scene_trace_meta,
        )
        if contract_mode == "hud":
            data["hud"] = {
                "trace_id": trace_id,
                "latency_ms": elapsed_ms,
                "contract_version": CONTRACT_VERSION,
                "role_key": data.get("role_surface", {}).get("role_code"),
                **scene_trace_meta,
            }
        if diag_enabled and diagnostic_info is not None and contract_mode == "hud":
            data["diagnostic"] = diagnostic_info

        # 顶层 ETag：纳入用户、导航指纹、默认路由、特性开关、可用意图
        top_etag = contract_assembler.build_top_etag(
            data,
            nav_fp=nav_fp,
            contract_mode=contract_mode,
            contract_version=CONTRACT_VERSION,
            api_version=API_VERSION,
        )

        return {"status": "success", "data": data, "meta": {**meta, "etag": top_etag}, "ok": True}
