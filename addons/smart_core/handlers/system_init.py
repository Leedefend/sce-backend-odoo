# smart_core/handlers/system_init.py
# -*- coding: utf-8 -*-
import logging
import time
from typing import List

from odoo import api, SUPERUSER_ID

from ..core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.utils.misc import format_versions
from odoo.addons.smart_core.core.extension_loader import run_extension_hooks
from odoo.addons.smart_core.core.scene_provider import (
    load_scene_contract as provider_load_scene_contract,
    load_scenes_from_db_or_fallback as provider_load_scenes_from_db_or_fallback,
    merge_missing_scenes_from_registry as provider_merge_missing_scenes_from_registry,
    resolve_scene_channel as provider_resolve_scene_channel,
)
from odoo.addons.smart_core.core.capability_provider import (
    load_capabilities_for_user as provider_load_capabilities_for_user,
)
from odoo.addons.smart_core.core.contract_assembler import ContractAssembler
from odoo.addons.smart_core.core.intent_surface_builder import IntentSurfaceBuilder
from odoo.addons.smart_core.core.hash_utils import stable_fingerprint
from odoo.addons.smart_core.core.request_diagnostics import RequestDiagnosticsCollector
from odoo.addons.smart_core.core.scene_channel_policy import SceneChannelPolicy
from odoo.addons.smart_core.core.scene_diagnostics_builder import SceneDiagnosticsBuilder
from odoo.addons.smart_core.core.system_init_identity_payload import SystemInitIdentityPayload
from odoo.addons.smart_core.core.system_init_preload_builder import SystemInitPreloadBuilder
from odoo.addons.smart_core.core.scene_runtime_orchestrator import SceneRuntimeOrchestrator
from odoo.addons.smart_core.core.system_init_surface_builder import SystemInitSurfaceBuilder
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.governance.scene_drift_engine import (
    SceneDriftEngine,
    append_resolve_error as drift_append_resolve_error,
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
    normalize_capabilities,
    resolve_contract_mode,
)

_logger = logging.getLogger(__name__)

# Contract/API version markers for client compatibility
CONTRACT_VERSION = "v0.1"
API_VERSION = "v1"

# ===================== 工具函数（权限 / 指纹 / 导航净化） =====================

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

def _resolve_scene_channel(env, user, params: dict | None) -> tuple[str, str, str]:
    collector = RequestDiagnosticsCollector()
    return provider_resolve_scene_channel(env, user, params, get_header=collector.get_request_header)

def _load_scene_contract(env, scene_channel: str, use_pinned: bool) -> tuple[dict | None, str]:
    return provider_load_scene_contract(env, scene_channel, use_pinned, logger=_logger)

def _load_scenes_from_db_or_fallback(env, drift):
    return provider_load_scenes_from_db_or_fallback(env, drift=drift, logger=_logger)

def _merge_missing_scenes_from_registry(env, scenes, warnings):
    return provider_merge_missing_scenes_from_registry(env, scenes, warnings)

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
        diagnostics_collector = RequestDiagnosticsCollector()
        scene_channel_policy = SceneChannelPolicy()
        scene_channel, rollback_active = scene_channel_policy.resolve(env, params, scene_channel)
        
        diag_enabled = diagnostics_collector.diagnostics_enabled(self.env)
        diagnostic_info = None
        if diag_enabled:
            diagnostic_info = diagnostics_collector.collect_system_init(self.env, params)

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
        user_dict = SystemInitIdentityPayload.build(user, user_groups_xmlids)

        # -------- 2) 导航（净化 + 指纹）--------
        p_nav = {"subject": "nav", "scene": scene}
        if params.get("root_xmlid"):
            p_nav["root_xmlid"] = params.get("root_xmlid")
        if params.get("root_menu_id"):
            p_nav["root_menu_id"] = params.get("root_menu_id")
        nav_data, nav_versions = NavDispatcher(env, su_env).build_nav(p_nav)

        nav_tree_raw = nav_data.get("nav") or []
        nav_tree = NavTreeCleaner().clean(nav_tree_raw)
        nav_adapter = OdooNavAdapter()
        nav_adapter.enrich(env, nav_tree)
        nav_fp = stable_fingerprint({"scene": scene, "nav": nav_tree})
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
        intents, intents_meta = IntentSurfaceBuilder().collect(env, user)

        # -------- 3/4) 首页契约 + 可选预取（仅 etag，不回传整包契约）--------
        preload_builder = SystemInitPreloadBuilder()
        home_contract, preload_items, etags, parts_version = preload_builder.build(
            env=env,
            su_env=su_env,
            params=params,
            default_home_action=default_home_action,
            contract_service=cs,
        )

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
            **SceneDiagnosticsBuilder.initial(
                data,
                rollback_active=rollback_active,
                channel_selector=channel_selector,
                channel_source_ref=channel_source_ref,
            ),
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

        scene_runtime_orchestrator = SceneRuntimeOrchestrator(logger=_logger)
        data, scene_channel, rollback_active, scene_diagnostics = scene_runtime_orchestrator.execute(
            env=env,
            user=user,
            params=params,
            data=data,
            nav_tree=nav_tree,
            scene_channel=scene_channel,
            rollback_active=rollback_active,
            trace_id=trace_id,
            scene_normalizer=scene_normalizer,
            scene_drift_engine=scene_drift_engine,
            auto_degrade_engine=auto_degrade_engine,
            diagnostics_collector=diagnostics_collector,
            scene_diagnostics=scene_diagnostics,
            load_scene_contract_fn=_load_scene_contract,
            load_scenes_fallback_fn=_load_scenes_from_db_or_fallback,
            merge_missing_scenes_fn=_merge_missing_scenes_from_registry,
            append_resolve_error_fn=drift_append_resolve_error,
        )
        data, scene_diagnostics = SystemInitSurfaceBuilder.apply(
            data=data,
            contract_mode=contract_mode,
            scene_diagnostics=scene_diagnostics,
            capability_surface_engine=capability_surface_engine,
            identity_resolver=identity_resolver,
            user_groups_xmlids=user_groups_xmlids,
            nav_tree=nav_tree,
            scene_diagnostics_builder=SceneDiagnosticsBuilder,
            build_capability_groups_fn=provider_build_capability_groups,
            apply_contract_governance_fn=apply_contract_governance,
        )
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
