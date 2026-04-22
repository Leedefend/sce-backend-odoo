# smart_core/handlers/system_init.py
# -*- coding: utf-8 -*-
import json
import logging
import time
from typing import List

from odoo import api, SUPERUSER_ID

from ..core.base_handler import BaseIntentHandler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.app_config_engine.utils.misc import format_versions
from odoo.addons.smart_core.core.scene_provider import (
    load_scene_contract as provider_load_scene_contract,
    load_scenes_from_db_or_fallback as provider_load_scenes_from_db_or_fallback,
    merge_missing_scenes_from_registry as provider_merge_missing_scenes_from_registry,
    resolve_scene_channel as provider_resolve_scene_channel,
)
from odoo.addons.smart_core.core.capability_provider import (
    build_capability_groups as provider_build_capability_groups,
    load_capabilities_for_user as provider_load_capabilities_for_user,
    load_capabilities_for_user_with_timings as provider_load_capabilities_for_user_with_timings,
)
from odoo.addons.smart_core.core.intent_surface_builder import IntentSurfaceBuilder
from odoo.addons.smart_core.core.hash_utils import stable_fingerprint
from odoo.addons.smart_core.core.system_init_components_factory import SystemInitComponentsFactory
from odoo.addons.smart_core.core.request_diagnostics import RequestDiagnosticsCollector
from odoo.addons.smart_core.core.scene_channel_policy import SceneChannelPolicy
from odoo.addons.smart_core.core.scene_diagnostics_builder import SceneDiagnosticsBuilder
from odoo.addons.smart_core.core.system_init_diagnostics_helper import SystemInitDiagnosticsHelper
from odoo.addons.smart_core.core.system_init_identity_payload import SystemInitIdentityPayload
from odoo.addons.smart_core.core.system_init_nav_request_builder import SystemInitNavRequestBuilder
from odoo.addons.smart_core.core.system_init_payload_builder import SystemInitPayloadBuilder
from odoo.addons.smart_core.core.system_init_response_meta_builder import SystemInitResponseMetaBuilder
from odoo.addons.smart_core.core.system_init_preload_builder import SystemInitPreloadBuilder
from odoo.addons.smart_core.core.scene_runtime_orchestrator import SceneRuntimeOrchestrator
from odoo.addons.smart_core.core.system_init_runtime_context import SystemInitRuntimeContext
from odoo.addons.smart_core.core.system_init_surface_context import SystemInitSurfaceContext
from odoo.addons.smart_core.core.system_init_surface_builder import SystemInitSurfaceBuilder
from odoo.addons.smart_core.core.system_init_extension_fact_merger import (
    apply_extension_fact_contributions,
    merge_extension_facts,
)
from odoo.addons.smart_core.core.system_init_scene_runtime_surface_context import SystemInitSceneRuntimeSurfaceContext
from odoo.addons.smart_core.core.system_init_scene_runtime_surface_builder import SystemInitSceneRuntimeSurfaceBuilder
from odoo.addons.smart_core.core.system_init_dictionary_data_helper import apply_dictionary_startup_data
from odoo.addons.smart_core.core.intent_execution_result import IntentExecutionResult
from odoo.addons.smart_core.core.workspace_home_contract_builder import build_workspace_home_contract
from odoo.addons.smart_core.core.runtime_page_contract_builder import mirror_workspace_home_role_context
from odoo.addons.smart_core.core.scene_governance_payload_builder import build_scene_governance_payload_v1
from odoo.addons.smart_core.core.ui_base_contract_asset_event_queue import get_queue_metrics
from odoo.addons.smart_core.core.release_navigation_contract_builder import build_release_navigation_contract
from odoo.addons.smart_core.core.scene_delivery_policy import (
    filter_delivery_scenes,
    resolve_delivery_policy_runtime,
)
from odoo.addons.smart_core.core.scene_nav_contract_builder import build_scene_nav_contract
from odoo.addons.smart_core.core.scene_ready_contract_builder import build_scene_ready_contract_v1
from odoo.addons.smart_core.core.ui_base_contract_asset_repository import bind_scene_assets
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService
from odoo.addons.smart_core.delivery.release_audit_trail_service import ReleaseAuditTrailService
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.governance.scene_drift_engine import append_resolve_error as drift_append_resolve_error
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver
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
CONTRACT_VERSION = "1.0.0"
API_VERSION = "v1"

_INDUSTRY_EXTENSION_MODULES = (
    "smart_construction_core",
    "smart_construction_scene",
    "smart_construction_portal",
    "smart_construction_demo",
)

# ===================== 工具函数（权限 / 指纹 / 导航净化） =====================

def _load_capabilities_for_user(env, user) -> List[dict]:
    return provider_load_capabilities_for_user(env, user)


def _load_capabilities_for_user_with_timings(env, user) -> tuple[List[dict], dict[str, int]]:
    return provider_load_capabilities_for_user_with_timings(env, user)


def _bind_scene_assets(*args, **kwargs):
    return bind_scene_assets(*args, **kwargs)


def _is_any_module_installed(env, module_names: List[str]) -> bool:
    safe_names = [str(name or "").strip() for name in (module_names or []) if str(name or "").strip()]
    if not safe_names:
        return False
    try:
        count = env["ir.module.module"].sudo().search_count([
            ("name", "in", safe_names),
            ("state", "=", "installed"),
        ])
        return bool(count)
    except Exception:
        return False


def _is_platform_minimum_surface_mode(env) -> bool:
    return not _is_any_module_installed(env, list(_INDUSTRY_EXTENSION_MODULES))


def _build_platform_minimum_nav_contract() -> dict:
    workspace_leaf = {
        "key": "scene:workspace.home",
        "label": "工作台",
        "title": "工作台",
        "menu_id": None,
        "children": [],
        "scene_key": "workspace.home",
        "meta": {
            "scene_key": "workspace.home",
            "action_type": "scene.contract",
            "scene_source": "platform_minimum_surface",
        },
    }
    group_node = {
        "key": "group:role_primary",
        "label": "我的场景",
        "title": "我的场景",
        "menu_id": None,
        "children": [workspace_leaf],
        "meta": {
            "group_key": "role_primary",
            "scene_source": "platform_minimum_surface",
        },
    }
    root_node = {
        "key": "root:scene_contract",
        "label": "场景导航",
        "title": "场景导航",
        "menu_id": None,
        "children": [group_node],
        "meta": {
            "scene_source": "platform_minimum_surface",
            "menu_xmlid": "scene.contract.root",
        },
    }
    default_route = {
        "menu_id": None,
        "scene_key": "workspace.home",
        "route": "/",
        "reason": "platform_minimum_surface",
    }
    return {
        "source": "platform_minimum_surface",
        "nav": [root_node],
        "default_route": default_route,
        "meta": {
            "platform_minimum_surface": True,
            "scene_count": 1,
            "scene_input_count": 1,
            "excluded_scene_count": 0,
            "candidate_count": 1,
            "group_count": 1,
            "remaining_group_count": 0,
            "remaining_hidden": False,
            "policy_applied": False,
        },
    }


def _normalize_access_suggested_action(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    access = data.get("access") if isinstance(data.get("access"), dict) else {}
    if not access:
        return data
    reason_code = str(access.get("reason_code") or "").strip()
    suggested_action = str(access.get("suggested_action") or "").strip()
    if not suggested_action and reason_code:
        suggested_action = str(failure_meta_for_reason(reason_code).get("suggested_action") or "").strip()
    if suggested_action:
        next_access = dict(access)
        next_access["suggested_action"] = suggested_action
        data["access"] = next_access
    return data


def _normalize_scene_validation_recovery_strategy(payload) -> dict:
    if not isinstance(payload, dict):
        return {}
    out = {}
    for key in ("default", "by_role", "by_company", "by_company_role"):
        value = payload.get(key)
        if isinstance(value, dict):
            out[key] = value
    return out


def _load_scene_validation_recovery_strategy(env, params: dict, data: dict) -> dict:
    inline = _normalize_scene_validation_recovery_strategy(params.get("scene_validation_recovery_strategy"))
    if inline:
        return inline
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    ext_payload = _normalize_scene_validation_recovery_strategy(ext_facts.get("scene_validation_recovery_strategy"))
    if ext_payload:
        return ext_payload
    try:
        raw = env["ir.config_parameter"].sudo().get_param("smart_core.scene_validation_recovery_strategy_json")
    except Exception:
        raw = ""
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except Exception:
        return {}
    return _normalize_scene_validation_recovery_strategy(loaded)


def _normalize_scene_action_surface_strategy(payload) -> dict:
    if not isinstance(payload, dict):
        return {}

    def _normalize_key_list(value):
        if not isinstance(value, list):
            return []
        out = []
        seen = set()
        for item in value:
            key = str(item or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
        return out

    def _normalize_rule(rule_payload):
        if not isinstance(rule_payload, dict):
            return {}
        normalized = {}
        for rule_key in ("force_primary_keys", "force_secondary_keys", "force_contextual_keys", "hide_keys"):
            key_list = _normalize_key_list(rule_payload.get(rule_key))
            if key_list:
                normalized[rule_key] = key_list
        return normalized

    out = {}
    for key in ("default", "by_role", "by_company", "by_company_role"):
        value = payload.get(key)
        if key == "default":
            normalized_default = _normalize_rule(value)
            if normalized_default:
                out[key] = normalized_default
            continue
        if not isinstance(value, dict):
            continue
        normalized_bucket = {}
        for scope, scope_rule in value.items():
            scope_key = str(scope or "").strip()
            if not scope_key:
                continue
            normalized_rule = _normalize_rule(scope_rule)
            if normalized_rule:
                normalized_bucket[scope_key] = normalized_rule
        if normalized_bucket:
            out[key] = normalized_bucket
    return out


def _load_scene_action_surface_strategy(env, params: dict, data: dict) -> dict:
    inline = _normalize_scene_action_surface_strategy(params.get("scene_action_surface_strategy"))
    if inline:
        return inline
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    ext_payload = _normalize_scene_action_surface_strategy(ext_facts.get("scene_action_surface_strategy"))
    if ext_payload:
        return ext_payload
    try:
        raw = env["ir.config_parameter"].sudo().get_param("smart_core.scene_action_surface_strategy_json")
    except Exception:
        raw = ""
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except Exception:
        return {}
    return _normalize_scene_action_surface_strategy(loaded)


def _strip_ui_base_contract_for_frontend(payload):
    if isinstance(payload, list):
        return [_strip_ui_base_contract_for_frontend(item) for item in payload]
    if not isinstance(payload, dict):
        return payload

    cleaned = {}
    for key, value in payload.items():
        if key in {"ui_base_contract", "ui_base_contract_ref"}:
            continue
        cleaned[key] = _strip_ui_base_contract_for_frontend(value)
    return cleaned


def _parse_with_tokens(value) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, str):
        for part in value.split(","):
            token = str(part or "").strip().lower()
            if token:
                tokens.add(token)
        return tokens
    if isinstance(value, (list, tuple, set)):
        for item in value:
            token = str(item or "").strip().lower()
            if token:
                tokens.add(token)
    return tokens


def _filter_startup_scenes_for_preload(scenes, allowed_scene_keys: list[str] | None) -> list[dict]:
    if not isinstance(scenes, list):
        return []
    allowed = {str(item or "").strip() for item in (allowed_scene_keys or []) if str(item or "").strip()}
    if not allowed:
        return [row for row in scenes if isinstance(row, dict)]
    filtered = []
    for row in scenes:
        if not isinstance(row, dict):
            continue
        scene_key = str(row.get("code") or row.get("key") or "").strip()
        if scene_key in allowed:
            filtered.append(row)
    return filtered


def _build_minimal_intent_surface(intents: list[str], intents_meta: dict) -> list[str]:
    minimal_order = [
        "system.init",
        "ui.contract",
        "meta.intent_catalog",
        "app.nav",
        "app.open",
        "auth.logout",
    ]
    minimal = [name for name in minimal_order if name in (intents or [])]
    _ = intents_meta
    return minimal

def _resolve_scene_channel(env, user, params: dict | None) -> tuple[str, str, str]:
    collector = RequestDiagnosticsCollector()
    return provider_resolve_scene_channel(env, user, params, get_header=collector.get_request_header)

def _load_scene_contract(env, scene_channel: str, use_pinned: bool) -> tuple[dict | None, str]:
    return provider_load_scene_contract(env, scene_channel, use_pinned, logger=_logger)

def _load_scenes_from_db_or_fallback(env, drift=None, logger=None):
    return provider_load_scenes_from_db_or_fallback(
        env,
        drift=drift,
        logger=logger or _logger,
    )

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
        perf0 = time.perf_counter()
        params = payload.get("params") if isinstance(payload, dict) else None
        if not isinstance(params, dict):
            params = payload if isinstance(payload, dict) else {}
        build_mode = SystemInitPayloadBuilder.resolve_build_mode(params)
        startup_timings_ms: dict[str, int] = {}
        startup_subtimings_ms: dict[str, dict[str, int]] = {}

        def _mark(stage: str, started_at: float) -> float:
            startup_timings_ms[stage] = int((time.perf_counter() - started_at) * 1000)
            return time.perf_counter()

        def _mark_substage(stage: str, substage: str, started_at: float) -> float:
            stage_timings = startup_subtimings_ms.setdefault(stage, {})
            stage_timings[substage] = int((time.perf_counter() - started_at) * 1000)
            return time.perf_counter()

        contract_mode = resolve_contract_mode(params)
        trace_id = ""
        try:
            trace_id = str((self.context or {}).get("trace_id") or "")
        except Exception:
            trace_id = ""

        env = self.env
        su_env = self.su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))

        stage_ts = time.perf_counter()
        scene_channel, channel_selector, channel_source_ref = _resolve_scene_channel(env, env.user, params)
        diagnostics_collector = RequestDiagnosticsCollector()
        scene_channel_policy = SceneChannelPolicy()
        scene_channel, rollback_active = scene_channel_policy.resolve(env, params, scene_channel)
        diag_enabled, diagnostic_info = SystemInitDiagnosticsHelper.collect(diagnostics_collector, self.env, params)
        if diag_enabled:
            SystemInitDiagnosticsHelper.log_debug(
                _logger,
                self.env,
                params,
                diagnostic_info,
                self_params=getattr(self, "params", {}),
            )
        stage_ts = _mark("resolve_scene_channel", stage_ts)

        # 如果 finalize_contract 内部不读 ORM，可用 env；若会读，推荐 su_env
        cs = ContractService(su_env)

        # -------- 1) 用户/环境 --------
        scene = params.get("scene") or "web"

        user = env.user
        identity_resolver = IdentityResolver(env)
        user_groups_xmlids = identity_resolver.user_group_xmlids(user)
        user_dict = SystemInitIdentityPayload.build(user, user_groups_xmlids)

        # -------- 2) 导航（净化 + 指纹）--------
        p_nav = SystemInitNavRequestBuilder.build(params, scene)
        try:
            nav_data, nav_versions = NavDispatcher(env, su_env).build_nav(p_nav)
        except KeyError as exc:
            if "app.menu.config" not in str(exc):
                raise
            _logger.warning(
                "system.init: app.menu.config missing, fallback to minimal nav surface trace=%s db=%s",
                trace_id,
                env.cr.dbname,
            )
            nav_data = {
                "nav": [],
                "defaultRoute": {"menu_id": None},
                "feature_flags": {"ai_enabled": True},
            }
            nav_versions = {
                "menu": 1,
                "fingerprint": "fallback-no-app-menu-config",
                "nav_source": "fallback_minimal",
            }
        stage_ts = _mark("build_nav", stage_ts)

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

        # -------- 2.5) 可用意图（最小启动集合 + 独立目录引用）--------
        intents_all, intents_meta_all = IntentSurfaceBuilder().collect(env, user)
        intents = _build_minimal_intent_surface(intents_all, intents_meta_all)
        stage_ts = _mark("collect_intents", stage_ts)

        # -------- 3/4) 首页契约 + 可选预取（仅 etag，不回传整包契约）--------
        home_contract = None
        preload_items = []
        etags = {}
        parts_version = {}
        if build_mode in {SystemInitPayloadBuilder.BUILD_MODE_PRELOAD, SystemInitPayloadBuilder.BUILD_MODE_DEBUG}:
            preload_builder = SystemInitPreloadBuilder()
            home_contract, preload_items, etags, parts_version = preload_builder.build(
                env=env,
                su_env=su_env,
                params=params,
                default_home_action=default_home_action,
                contract_service=cs,
            )
        stage_ts = _mark("build_preload_refs", stage_ts)

        prepare_runtime_context_ts = time.perf_counter()

        capabilities_raw, capability_load_timings_ms = _load_capabilities_for_user_with_timings(env, user)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "load_capabilities_for_user",
            prepare_runtime_context_ts,
        )
        if capability_load_timings_ms:
            startup_subtimings_ms["capability_load"] = dict(capability_load_timings_ms)
        capabilities = normalize_capabilities(capabilities_raw)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "normalize_capabilities",
            prepare_runtime_context_ts,
        )

        # -------- 5) 汇总返回（统一蛇形命名 + 导航指纹 + 动态意图）--------
        data = SystemInitPayloadBuilder.build_base(
            user_dict=user_dict,
            nav_tree=nav_tree,
            nav_meta={
                "fingerprint": nav_fp,
                **(nav_versions or {}),
                "debug_params_keys": sorted(list(params.keys())) if isinstance(params, dict) else [],
                "debug_root_xmlid": params.get("root_xmlid") if isinstance(params, dict) else None,
            },
            default_route=nav_data.get("defaultRoute") or {"menu_id": None},
            intents=intents,
            feature_flags=nav_data.get("feature_flags") or {"ai_enabled": True},
            capabilities=capabilities,
            scene_channel=scene_channel,
            channel_selector=channel_selector,
            channel_source_ref=channel_source_ref,
            contract_mode=contract_mode,
            contract_version=CONTRACT_VERSION,
        )
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "build_base_call",
            prepare_runtime_context_ts,
        )
        # Keep explicit contract_mode mapping in handler for governance coverage guard.
        data.update({"contract_mode": contract_mode})
        scene_diagnostics = {
            **SceneDiagnosticsBuilder.initial(
                data,
                rollback_active=rollback_active,
                channel_selector=channel_selector,
                channel_source_ref=channel_source_ref,
            ),
        }
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "initialize_scene_diagnostics",
            prepare_runtime_context_ts,
        )
        components = SystemInitComponentsFactory.create()
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "create_components",
            prepare_runtime_context_ts,
        )
        scene_normalizer = components["scene_normalizer"]
        scene_drift_engine = components["scene_drift_engine"]
        auto_degrade_engine = components["auto_degrade_engine"]
        capability_surface_engine = components["capability_surface_engine"]
        contract_assembler = components["contract_assembler"]
        scene_normalizer.append_act_url_deprecations(nav_tree, scene_diagnostics["normalize_warnings"])
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "append_act_url_deprecations",
            prepare_runtime_context_ts,
        )
        if build_mode in {SystemInitPayloadBuilder.BUILD_MODE_PRELOAD, SystemInitPayloadBuilder.BUILD_MODE_DEBUG}:
            SystemInitPayloadBuilder.attach_preload(data, home_contract, etags, preload_items)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "attach_preload_when_enabled",
            prepare_runtime_context_ts,
        )

        # 扩展模块 facts contribution（平台 merge owner）
        apply_extension_fact_contributions(data, env, user, context=params)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "apply_extension_fact_contributions",
            prepare_runtime_context_ts,
        )
        merge_extension_facts(data, include_workspace_collections=False)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "merge_extension_facts",
            prepare_runtime_context_ts,
        )
        data["scene_validation_recovery_strategy"] = _load_scene_validation_recovery_strategy(env, params, data)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "load_scene_validation_recovery_strategy",
            prepare_runtime_context_ts,
        )
        data["scene_action_surface_strategy"] = _load_scene_action_surface_strategy(env, params, data)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "load_scene_action_surface_strategy",
            prepare_runtime_context_ts,
        )
        data["scene_action_surface_strategy"] = _normalize_scene_action_surface_strategy(
            dict(
                action_surface_strategy=data.get("scene_action_surface_strategy")
            ).get("action_surface_strategy")
        )
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "normalize_scene_action_surface_strategy",
            prepare_runtime_context_ts,
        )
        stage_ts = _mark("prepare_runtime_context", stage_ts)

        runtime_ctx = SystemInitRuntimeContext(
            env=env,
            user=user,
            params=params,
            data=data,
            nav_tree=nav_tree,
            scene_channel=scene_channel,
            rollback_active=rollback_active,
            trace_id=trace_id,
            diagnostics_collector=diagnostics_collector,
            scene_diagnostics=scene_diagnostics,
            load_scene_contract_fn=_load_scene_contract,
            load_scenes_fallback_fn=_load_scenes_from_db_or_fallback,
            merge_missing_scenes_fn=_merge_missing_scenes_from_registry,
            append_resolve_error_fn=drift_append_resolve_error,
        )
        scene_runtime_orchestrator = SceneRuntimeOrchestrator(logger=_logger)
        runtime_ctx = scene_runtime_orchestrator.execute(
            runtime_ctx=runtime_ctx,
            scene_normalizer=scene_normalizer,
            scene_drift_engine=scene_drift_engine,
            auto_degrade_engine=auto_degrade_engine,
        )
        data = runtime_ctx.data
        scene_channel = runtime_ctx.scene_channel
        rollback_active = runtime_ctx.rollback_active
        scene_diagnostics = runtime_ctx.scene_diagnostics
        stage_ts = _mark("execute_scene_runtime", stage_ts)
        surface_ctx = SystemInitSurfaceContext(
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
        data, scene_diagnostics = SystemInitSurfaceBuilder.apply(surface_ctx=surface_ctx)
        stage_ts = _mark("apply_surface", stage_ts)
        with_tokens = _parse_with_tokens(params.get("with"))
        include_workspace_home = bool(params.get("with_preload", False)) or "workspace_home" in with_tokens
        if include_workspace_home:
            data["workspace_home"] = build_workspace_home_contract(data)
        else:
            data.pop("workspace_home", None)
        mirror_workspace_home_role_context(data)
        stage_ts = _mark("build_workspace_home", stage_ts)
        role_surface = data.get("role_surface") if isinstance(data, dict) else {}
        role_pruned = False
        if isinstance(role_surface, dict) and isinstance(data.get("nav"), list):
            pruned_nav = identity_resolver.filter_nav_for_role_surface(data.get("nav") or [], role_surface)
            role_pruned = pruned_nav != (data.get("nav") or [])
            data["nav"] = pruned_nav
            data["default_route"] = identity_resolver.infer_default_route_from_nav(pruned_nav)
            if isinstance(data.get("nav_meta"), dict):
                data["nav_meta"]["role_surface_pruned"] = role_pruned
                data["nav_meta"]["role_surface_code"] = role_surface.get("role_code")
        stage_ts = _mark("prune_nav_for_role", stage_ts)

        platform_minimum_surface_mode = _is_platform_minimum_surface_mode(env)
        scene_runtime_surface_ctx = SystemInitSceneRuntimeSurfaceContext(
            env=env,
            params=params,
            data=data,
            role_surface=role_surface if isinstance(role_surface, dict) else {},
            contract_mode=contract_mode,
            scene_channel=scene_channel,
            nav_tree=nav_tree,
            platform_minimum_surface_mode=platform_minimum_surface_mode,
            build_platform_minimum_nav_contract_fn=_build_platform_minimum_nav_contract,
            resolve_delivery_policy_runtime_fn=resolve_delivery_policy_runtime,
            filter_delivery_scenes_fn=filter_delivery_scenes,
            startup_scene_subset_resolver_fn=SystemInitPayloadBuilder.resolve_startup_scene_subset,
            filter_startup_scenes_for_preload_fn=_filter_startup_scenes_for_preload,
            bind_scene_assets_fn=_bind_scene_assets,
            build_scene_ready_contract_fn=build_scene_ready_contract_v1,
            build_scene_nav_contract_fn=build_scene_nav_contract,
        )
        scene_runtime_surface_result = SystemInitSceneRuntimeSurfaceBuilder.apply(surface_ctx=scene_runtime_surface_ctx)
        data = scene_runtime_surface_result["data"]
        delivery_result = scene_runtime_surface_result["delivery_result"]
        scene_nav_contract = scene_runtime_surface_result["scene_nav_contract"]
        bind_result = scene_runtime_surface_result["bind_result"]
        data["scene_ready_contract_v1"] = (
            data.get("scene_ready_contract_v1")
            if isinstance(data.get("scene_ready_contract_v1"), dict)
            else {}
        )
        nav_meta = data.get("nav_meta") if isinstance(data.get("nav_meta"), dict) else {}
        if isinstance(bind_result, dict):
            nav_meta["ui_base_contract_asset_scene_count"] = int(bind_result.get("asset_scene_count") or 0)
            nav_meta["ui_base_contract_bound_scene_count"] = int(bind_result.get("bound_scene_count") or 0)
            nav_meta["ui_base_contract_missing_scene_count"] = int(bind_result.get("missing_scene_count") or 0)
        else:
            nav_meta.setdefault("ui_base_contract_asset_scene_count", 0)
            nav_meta.setdefault("ui_base_contract_bound_scene_count", 0)
            nav_meta.setdefault("ui_base_contract_missing_scene_count", 0)
        data["nav_meta"] = nav_meta
        stage_ts = _mark("build_scene_runtime_surface", stage_ts)
        legacy_release_navigation = build_release_navigation_contract(data if isinstance(data, dict) else {})
        delivery_engine = DeliveryEngine(env)
        delivery_edition_key = str(((params or {}).get("edition_key") or "standard")).strip() or "standard"
        delivery_payload = delivery_engine.build(
            data=data if isinstance(data, dict) else {},
            product_key=f"construction.{delivery_edition_key}",
            edition_key=delivery_edition_key,
            base_product_key="construction",
            native_nav=nav_tree,
        )
        release_snapshot_service = EditionReleaseSnapshotService(env)
        release_audit_service = ReleaseAuditTrailService(env)
        data["delivery_engine_v1"] = delivery_payload
        edition_diagnostics = (
            delivery_payload.get("product_policy", {}).get("edition_diagnostics")
            if isinstance(delivery_payload.get("product_policy"), dict)
            else {}
        )
        effective_base_product_key = str(delivery_payload.get("base_product_key") or "construction").strip() or "construction"
        effective_edition_key = str(delivery_payload.get("edition_key") or "standard").strip() or "standard"
        effective_product_key = str(delivery_payload.get("product_key") or f"{effective_base_product_key}.{effective_edition_key}").strip()
        requested_product_key = f"construction.{delivery_edition_key}"
        released_snapshot_lineage = release_snapshot_service.resolve_active_snapshot_lineage(product_key=effective_product_key)
        release_audit_trail_summary = release_audit_service.build_runtime_summary(product_key=effective_product_key)
        runtime_diagnostics = dict(edition_diagnostics) if isinstance(edition_diagnostics, dict) else {}
        if released_snapshot_lineage:
            runtime_diagnostics["released_snapshot_lineage"] = released_snapshot_lineage
            meta = delivery_payload.get("meta")
            if not isinstance(meta, dict):
                meta = {}
                delivery_payload["meta"] = meta
            meta["released_snapshot_lineage"] = released_snapshot_lineage
        if release_audit_trail_summary:
            runtime_diagnostics["release_audit_trail_summary"] = release_audit_trail_summary
            meta = delivery_payload.get("meta")
            if not isinstance(meta, dict):
                meta = {}
                delivery_payload["meta"] = meta
            meta["release_audit_trail_summary"] = release_audit_trail_summary
        data["edition_runtime_v1"] = {
            "contract_version": "v1",
            "requested": {
                "product_key": requested_product_key,
                "base_product_key": "construction",
                "edition_key": delivery_edition_key,
            },
            "effective": {
                "product_key": effective_product_key,
                "base_product_key": effective_base_product_key,
                "edition_key": effective_edition_key,
            },
            "diagnostics": runtime_diagnostics,
        }
        data["release_navigation_v1"] = {
            "contract_version": str(delivery_payload.get("contract_version") or "v1"),
            "source": "delivery_engine_v1",
            "role_code": str(delivery_payload.get("role_code") or ""),
            "nav": delivery_payload.get("nav") if isinstance(delivery_payload.get("nav"), list) else [],
            "meta": {
                "product_key": str(delivery_payload.get("product_key") or ""),
                "edition_key": str(delivery_payload.get("edition_key") or ""),
                "delivery_engine_meta": delivery_payload.get("meta") if isinstance(delivery_payload.get("meta"), dict) else {},
                "legacy_builder_contract_version": str(legacy_release_navigation.get("contract_version") or ""),
            },
        }

        default_route_payload = data.get("default_route") if isinstance(data.get("default_route"), dict) else {}
        landing_scene_key = str(default_route_payload.get("scene_key") or "").strip()
        if not landing_scene_key and isinstance(role_surface, dict):
            landing_scene_key = str(role_surface.get("landing_scene_key") or "").strip()
        if not landing_scene_key:
            landing_scene_key = "workspace.home"
        data["workspace_home_ref"] = {
            "intent": "ui.contract",
            "scene_key": landing_scene_key,
            "loaded": bool(include_workspace_home),
        }
        data["intent_catalog_ref"] = {
            "intent": "meta.intent_catalog",
            "loaded": False,
            "count": len(intents_all or []),
        }

        if build_mode == SystemInitPayloadBuilder.BUILD_MODE_DEBUG:
            data["scene_governance_v1"] = build_scene_governance_payload_v1(
                data=data,
                scene_diagnostics=scene_diagnostics,
                delivery_meta=delivery_result.get("meta") if isinstance(delivery_result, dict) else {},
                nav_contract_meta=scene_nav_contract.get("meta") if isinstance(scene_nav_contract, dict) else {},
                asset_queue_metrics=get_queue_metrics(env),
            )
        else:
            data.pop("scene_governance_v1", None)
        data = _strip_ui_base_contract_for_frontend(data)
        extension_snapshot: dict = {}
        apply_extension_fact_contributions(extension_snapshot, env, user, context=params)
        snapshot_ext = (
            extension_snapshot.get("ext_facts")
            if isinstance(extension_snapshot.get("ext_facts"), dict)
            else {}
        )
        role_entries = []
        home_blocks = []
        for module_facts in snapshot_ext.values():
            if not isinstance(module_facts, dict):
                continue
            candidate = module_facts.get("role_entries")
            if isinstance(candidate, list) and candidate:
                role_entries = candidate
            block_candidate = module_facts.get("home_blocks")
            if isinstance(block_candidate, list) and block_candidate:
                home_blocks = block_candidate
        if isinstance(role_entries, list) and role_entries:
            data["role_entries"] = role_entries
        if isinstance(home_blocks, list) and home_blocks:
            data["home_blocks"] = home_blocks
        startup_inspect = {}
        if build_mode == SystemInitPayloadBuilder.BUILD_MODE_DEBUG:
            startup_inspect = {
                "nav_meta": data.get("nav_meta") if isinstance(data.get("nav_meta"), dict) else {},
                "delivery_policy": delivery_result.get("meta") if isinstance(delivery_result, dict) else {},
                "scene_nav_meta": scene_nav_contract.get("meta") if isinstance(scene_nav_contract, dict) else {},
                "scene_governance_v1": data.get("scene_governance_v1") if isinstance(data.get("scene_governance_v1"), dict) else {},
                "asset_binding": bind_result if isinstance(bind_result, dict) else {},
                "scene_diagnostics": scene_diagnostics if isinstance(scene_diagnostics, dict) else {},
            }
        data = SystemInitPayloadBuilder.build_startup_surface(
            data,
            params=params,
            build_mode=build_mode,
            inspect_payload=startup_inspect,
        )
        try:
            data = apply_dictionary_startup_data(env, data)
        except Exception:
            pass
        data = _normalize_access_suggested_action(data)
        data["contract_mode"] = contract_mode
        if contract_mode == "user":
            data.pop("scene_diagnostics", None)
            data.pop("diagnostic", None)
            data.pop("scene_channel_selector", None)
            data.pop("scene_channel_source_ref", None)
        stage_ts = _mark("finalize_startup_surface", stage_ts)

        # 分部 etag：加入导航
        etags["nav"] = nav_fp

        elapsed_ms = int((time.time() - ts0) * 1000)
        startup_profile = {
            "build_mode": build_mode,
            "timings_ms": startup_timings_ms,
            "subtimings_ms": startup_subtimings_ms,
            "total_ms": int((time.perf_counter() - perf0) * 1000),
            "response_key_count": len(data.keys()) if isinstance(data, dict) else 0,
        }
        scene_trace_meta, meta_with_etag = SystemInitResponseMetaBuilder.build(
            contract_assembler=contract_assembler,
            data=data,
            scene_diagnostics=scene_diagnostics,
            elapsed_ms=elapsed_ms,
            nav_versions=format_versions(nav_versions),
            parts_version=parts_version,
            etags=etags,
            intent_type=self.INTENT_TYPE,
            contract_version=CONTRACT_VERSION,
            api_version=API_VERSION,
            contract_mode=contract_mode,
            nav_fp=nav_fp,
            startup_profile=startup_profile,
        )
        if contract_mode == "hud":
            hud_trace = data.get("hud") if isinstance(data.get("hud"), dict) else {}
            for trace_key in ("scene_source", "scene_contract_ref", "channel_selector", "channel_source_ref"):
                trace_value = scene_trace_meta.get(trace_key)
                if str(trace_value or "").strip():
                    hud_trace[trace_key] = trace_value
            governance_payload = scene_trace_meta.get("governance")
            if isinstance(governance_payload, dict):
                hud_trace["governance"] = governance_payload
            data["hud"] = hud_trace
            if not isinstance(data.get("scene_diagnostics"), dict) and isinstance(scene_diagnostics, dict):
                data["scene_diagnostics"] = scene_diagnostics
        _ = scene_trace_meta
        _ = diag_enabled
        _ = diagnostic_info

        return IntentExecutionResult(
            ok=True,
            status="success",
            data=data,
            meta=meta_with_etag,
        )
