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
from odoo.addons.smart_core.core.workspace_home_contract_builder import build_workspace_home_contract
from odoo.addons.smart_core.core.page_contracts_builder import build_page_contracts
from odoo.addons.smart_core.core.scene_nav_contract_builder import build_scene_nav_contract
from odoo.addons.smart_core.core.scene_governance_payload_builder import build_scene_governance_payload_v1
from odoo.addons.smart_core.core.ui_base_contract_asset_event_queue import get_queue_metrics
from odoo.addons.smart_core.core.scene_ready_contract_builder import build_scene_ready_contract_v1
from odoo.addons.smart_core.core.ui_base_contract_asset_repository import bind_scene_assets
from odoo.addons.smart_core.core.scene_delivery_policy import (
    filter_delivery_scenes,
    resolve_delivery_policy_runtime,
)
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
        workspace_collections = core_facts.get("workspace_collections")
        if isinstance(workspace_collections, dict):
            for key in ("task_items", "payment_requests", "risk_actions", "project_actions"):
                rows = workspace_collections.get(key)
                if key not in data and isinstance(rows, list):
                    data[key] = rows
        provider_payload = core_facts.get("role_surface_override_provider")
        if isinstance(provider_payload, dict):
            provider_key = str(provider_payload.get("key") or "").strip()
            if provider_key:
                providers = data.get("role_surface_override_providers")
                if not isinstance(providers, dict):
                    providers = {}
                merged = dict(provider_payload)
                merged.pop("key", None)
                providers[provider_key] = merged
                data["role_surface_override_providers"] = providers


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
        diag_enabled, diagnostic_info = SystemInitDiagnosticsHelper.collect(diagnostics_collector, self.env, params)
        if diag_enabled:
            SystemInitDiagnosticsHelper.log_debug(
                _logger,
                self.env,
                params,
                diagnostic_info,
                self_params=getattr(self, "params", {}),
            )

        # 如果 finalize_contract 内部不读 ORM，可用 env；若会读，推荐 su_env
        cs = ContractService(su_env)

        # -------- 1) 用户/环境 --------
        scene = params.get("scene") or "web"

        user = env.user
        identity_resolver = IdentityResolver()
        user_groups_xmlids = identity_resolver.user_group_xmlids(user)
        user_dict = SystemInitIdentityPayload.build(user, user_groups_xmlids)

        # -------- 2) 导航（净化 + 指纹）--------
        p_nav = SystemInitNavRequestBuilder.build(params, scene)
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
            intents_meta=intents_meta,
            feature_flags=nav_data.get("feature_flags") or {"ai_enabled": True},
            capabilities=normalize_capabilities(_load_capabilities_for_user(env, user)),
            scene_channel=scene_channel,
            channel_selector=channel_selector,
            channel_source_ref=channel_source_ref,
            contract_mode=contract_mode,
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
        components = SystemInitComponentsFactory.create()
        scene_normalizer = components["scene_normalizer"]
        scene_drift_engine = components["scene_drift_engine"]
        auto_degrade_engine = components["auto_degrade_engine"]
        capability_surface_engine = components["capability_surface_engine"]
        contract_assembler = components["contract_assembler"]
        scene_normalizer.append_act_url_deprecations(nav_tree, scene_diagnostics["normalize_warnings"])
        SystemInitPayloadBuilder.attach_preload(data, home_contract, etags, preload_items)

        # 扩展模块可附加场景/能力等（不影响主流程）
        run_extension_hooks(env, "smart_core_extend_system_init", data, env, user)
        _merge_extension_facts(data)
        data["scene_validation_recovery_strategy"] = _load_scene_validation_recovery_strategy(env, params, data)
        data["scene_action_surface_strategy"] = _load_scene_action_surface_strategy(env, params, data)

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
        with_tokens = _parse_with_tokens(params.get("with"))
        include_workspace_home = bool(params.get("with_preload", False)) or "workspace_home" in with_tokens
        if include_workspace_home:
            data["workspace_home"] = build_workspace_home_contract(data)
        else:
            data.pop("workspace_home", None)
        data["page_contracts"] = build_page_contracts(data)
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

        delivery_runtime = resolve_delivery_policy_runtime(env, params)
        delivery_result = filter_delivery_scenes(
            data.get("scenes") if isinstance(data, dict) else [],
            surface=delivery_runtime.get("surface") or "default",
            role_surface=role_surface if isinstance(role_surface, dict) else {},
            contract_mode=contract_mode,
            runtime_env=delivery_runtime.get("runtime_env") or "dev",
            enabled=bool(delivery_runtime.get("enabled")),
        )
        if isinstance(data.get("nav_meta"), dict):
            data["nav_meta"]["delivery_policy"] = delivery_result.get("meta") or {}

        # Scene-first nav contract (v1): sidebar nav source switches from native menu facts
        # to scene orchestration contract. Keep legacy nav for rollback/diagnostics.
        nav_contract_input = dict(data)
        nav_contract_input["scenes"] = delivery_result.get("delivery_scenes") or []
        nav_contract_input["delivery_policy_applied"] = bool(delivery_result.get("meta", {}).get("enabled"))
        role_code = ""
        if isinstance(role_surface, dict):
            role_code = str(role_surface.get("role_code") or "").strip()
        bind_result = bind_scene_assets(
            env,
            scenes=nav_contract_input.get("scenes") if isinstance(nav_contract_input.get("scenes"), list) else [],
            role_code=role_code or None,
            company_id=env.company.id if env.company else None,
        )
        nav_contract_input["scenes"] = bind_result.get("scenes") or nav_contract_input.get("scenes") or []
        if isinstance(data.get("nav_meta"), dict):
            data["nav_meta"]["ui_base_contract_asset_scene_count"] = int(bind_result.get("asset_scene_count") or 0)
            data["nav_meta"]["ui_base_contract_bound_scene_count"] = int(bind_result.get("bound_scene_count") or 0)
            data["nav_meta"]["ui_base_contract_missing_scene_count"] = int(bind_result.get("missing_scene_count") or 0)
        data["scene_ready_contract_v1"] = build_scene_ready_contract_v1(
            scenes=nav_contract_input.get("scenes") if isinstance(nav_contract_input.get("scenes"), list) else [],
            role_surface=role_surface if isinstance(role_surface, dict) else {},
            scene_version=data.get("scene_version"),
            schema_version=data.get("schema_version"),
            scene_channel=scene_channel,
            action_surface_strategy=data.get("scene_action_surface_strategy") if isinstance(data.get("scene_action_surface_strategy"), dict) else {},
            runtime_context={
                "role_code": role_code,
                "company_id": env.company.id if env.company else None,
            },
        )
        scene_nav_contract = build_scene_nav_contract(nav_contract_input)
        if isinstance(scene_nav_contract, dict) and isinstance(scene_nav_contract.get("nav"), list):
            data["nav_legacy"] = data.get("nav") or []
            data["nav_contract"] = scene_nav_contract
            data["nav"] = scene_nav_contract.get("nav") or []
            data["default_route"] = scene_nav_contract.get("default_route") or data.get("default_route") or {"menu_id": None}
            if isinstance(data.get("nav_meta"), dict):
                data["nav_meta"]["nav_source"] = scene_nav_contract.get("source") or "scene_contract_v1"
                data["nav_meta"]["scene_ready_contract_v1"] = True
                contract_meta = scene_nav_contract.get("meta")
                if isinstance(contract_meta, dict):
                    data["nav_meta"]["scene_nav_meta"] = contract_meta

        landing_scene_key = "portal.dashboard"
        if isinstance(role_surface, dict):
            landing_scene_key = str(role_surface.get("landing_scene_key") or "").strip() or landing_scene_key
        data["workspace_home_ref"] = {
            "intent": "ui.contract",
            "scene_key": landing_scene_key,
            "loaded": bool(include_workspace_home),
        }

        data["scene_governance_v1"] = build_scene_governance_payload_v1(
            data=data,
            scene_diagnostics=scene_diagnostics,
            delivery_meta=delivery_result.get("meta") if isinstance(delivery_result, dict) else {},
            nav_contract_meta=scene_nav_contract.get("meta") if isinstance(scene_nav_contract, dict) else {},
            asset_queue_metrics=get_queue_metrics(env),
        )
        data = _strip_ui_base_contract_for_frontend(data)
        SystemInitPayloadBuilder.attach_layered_contract(data)
        if contract_mode == "hud":
            data["scene_diagnostics"] = scene_diagnostics

        # 分部 etag：加入导航
        etags["nav"] = nav_fp

        elapsed_ms = int((time.time() - ts0) * 1000)
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
        )
        if contract_mode == "hud":
            SystemInitPayloadBuilder.attach_hud(
                data,
                trace_id=trace_id,
                elapsed_ms=elapsed_ms,
                contract_version=CONTRACT_VERSION,
                scene_trace_meta=scene_trace_meta,
            )
        if diag_enabled and diagnostic_info is not None and contract_mode == "hud":
            SystemInitPayloadBuilder.attach_diagnostic(data, diagnostic_info)

        return {"status": "success", "data": data, "meta": meta_with_etag, "ok": True}
