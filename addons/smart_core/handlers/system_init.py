# smart_core/handlers/system_init.py
# -*- coding: utf-8 -*-
import json
import logging
import time
from typing import List

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

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
from odoo.addons.smart_core.utils.backend_contract_boundaries import (
    MENU_CONFIG_CONFIG_ONLY_PARAM,
    MENU_CONFIG_NAV_ENABLED_PARAM,
    MENU_CONFIG_POLICY_MODEL,
    NAV_USER_DATA_ACCEPTANCE_ONLY_PARAM,
)
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
try:
    from odoo.addons.smart_core.core.project_context import build_record_context_contract
except ImportError:  # pragma: no cover - compatibility for lightweight boundary tests
    from odoo.addons.smart_core.core.project_context import build_project_context_contract as build_record_context_contract
from odoo.addons.smart_core.core.page_contracts_builder import build_page_contracts
from odoo.addons.smart_core.core.workspace_home_contract_builder import build_workspace_home_contract
from odoo.addons.smart_core.core.runtime_page_contract_builder import mirror_workspace_home_role_context
from odoo.addons.smart_core.core.scene_governance_payload_builder import build_scene_governance_payload_v1
from odoo.addons.smart_core.core.ui_base_contract_asset_event_queue import get_queue_metrics
from odoo.addons.smart_core.core.release_navigation_contract_builder import build_release_navigation_contract
from odoo.addons.smart_core.core.request_params import parse_bool
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
from odoo.addons.smart_core.delivery.product_identity import LEGACY_DEFAULT_BASE_PRODUCT_KEY
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
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
from odoo.addons.smart_core.core.extension_loader import run_extension_hooks

_logger = logging.getLogger(__name__)

# Contract/API version markers for client compatibility
CONTRACT_VERSION = "1.0.0"
API_VERSION = "v1"

_BUSINESS_NAV_GROUP_DISPLAY_ORDER: dict[str, int] = {}

_BUSINESS_MASTER_DATA_MENU_XMLIDS: set[str] = set()

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


def _resolve_industry_extension_modules(env) -> list[str]:
    hook_modules = call_extension_hook_first(
        env,
        "smart_core_industry_extension_module_names",
        env,
    )
    if isinstance(hook_modules, (list, tuple, set)):
        modules = [str(name or "").strip() for name in hook_modules if str(name or "").strip()]
        if modules:
            return modules
    try:
        raw = env["ir.config_parameter"].sudo().get_param("smart_core.industry_extension_modules", "")
    except Exception:
        raw = ""
    modules = [item.strip() for item in str(raw or "").split(",") if item.strip()]
    return modules


def _resolve_user_acceptance_nav_contract(env) -> dict:
    hook_payload = call_extension_hook_first(env, "smart_core_user_data_acceptance_nav_contract", env)
    if isinstance(hook_payload, dict):
        return hook_payload
    return {}


def _string_set(value) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {_text(item) for item in value if _text(item)}
    if isinstance(value, str) and value.strip():
        return {_text(value)}
    return set()


def _int_set(value) -> set[int]:
    values = value if isinstance(value, (list, tuple, set)) else [value]
    out = set()
    for item in values:
        try:
            parsed = int(item or 0)
        except Exception:
            parsed = 0
        if parsed > 0:
            out.add(parsed)
    return out


def _acceptance_surface_matchers(contract: dict | None) -> dict:
    contract = contract if isinstance(contract, dict) else {}
    tokens = set()
    for key in (
        "acceptance_surface_tokens",
        "old_acceptance_group_labels",
        "direct_acceptance_group_labels",
        "joint_acceptance_group_labels",
        "acceptance_root_labels",
    ):
        tokens.update(_string_set(contract.get(key)))
    return {
        "tokens": tokens,
        "menu_ids": _int_set(contract.get("acceptance_surface_menu_ids")),
        "action_ids": _int_set(contract.get("acceptance_surface_action_ids")),
    }


def _resolve_startup_delivery_identity(env, params: dict | None) -> dict:
    raw_params = params if isinstance(params, dict) else {}
    edition_key = str(
        raw_params.get("delivery_edition_key")
        or raw_params.get("edition_key")
        or "standard"
    ).strip() or "standard"
    explicit_product_key = str(
        raw_params.get("delivery_product_key")
        or raw_params.get("product_key")
        or ""
    ).strip()
    explicit_base_product_key = str(
        raw_params.get("delivery_base_product_key")
        or raw_params.get("base_product_key")
        or ""
    ).strip()
    hook_payload = None
    if not explicit_product_key and not explicit_base_product_key:
        hook_result = call_extension_hook_first(env, "smart_core_resolve_startup_delivery_identity", env, raw_params)
        hook_payload = hook_result if isinstance(hook_result, dict) else None
    source = "params" if (explicit_product_key or explicit_base_product_key) else "extension_hook" if hook_payload else "legacy_default"
    base_product_key = (
        explicit_base_product_key
        or str((hook_payload or {}).get("base_product_key") or LEGACY_DEFAULT_BASE_PRODUCT_KEY).strip()
        or LEGACY_DEFAULT_BASE_PRODUCT_KEY
    )
    product_key = explicit_product_key or str((hook_payload or {}).get("product_key") or f"{base_product_key}.{edition_key}").strip()
    if "." in product_key and not explicit_base_product_key:
        base_product_key = product_key.split(".", 1)[0] or base_product_key
    return {
        "product_key": product_key,
        "base_product_key": base_product_key,
        "edition_key": edition_key,
        "source": source,
        "projection_only": True,
        "no_business_fact_authority": True,
    }


def _is_platform_minimum_surface_mode(env, delivery_identity: dict | None = None) -> bool:
    identity = delivery_identity if isinstance(delivery_identity, dict) else {}
    base_product_key = str(identity.get("base_product_key") or "").strip()
    product_key = str(identity.get("product_key") or "").strip()
    if base_product_key == "platform" or product_key.startswith("platform."):
        return True
    return not _is_any_module_installed(env, _resolve_industry_extension_modules(env))


def _build_platform_minimum_nav_contract() -> dict:
    workspace_leaf = {
        "key": "scene:workspace.home",
        "label": "角色首页",
        "title": "角色首页",
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


def _text(value) -> str:
    return str(value or "").strip()


def _release_gate_page_contract_from_snapshot(snapshot: dict) -> dict:
    meta_json = snapshot.get("meta_json") if isinstance(snapshot.get("meta_json"), dict) else {}
    release_draft = meta_json.get("release_draft") if isinstance(meta_json.get("release_draft"), dict) else {}
    pages = release_draft.get("pages") if isinstance(release_draft.get("pages"), list) else []
    allowed = {
        "page_keys": set(),
        "menu_keys": set(),
        "menu_xmlids": set(),
        "routes": set(),
        "models": set(),
        "menu_ids": set(),
        "action_ids": set(),
    }
    effective_count = 0
    for page in pages:
        if not isinstance(page, dict):
            continue
        enabled = bool(page.get("enabled", True))
        release_state = _text(page.get("release_state")) or ("released" if enabled else "hidden")
        if not enabled or release_state not in {"released", "preview"}:
            continue
        effective_count += 1
        for bucket, key in (
            ("page_keys", "page_key"),
            ("menu_keys", "menu_key"),
            ("menu_xmlids", "menu_xmlid"),
            ("routes", "route"),
            ("models", "res_model"),
        ):
            value = _text(page.get(key))
            if value:
                allowed[bucket].add(value)
        menu_id = int(page.get("menu_id") or 0)
        action_id = int(page.get("action_id") or 0)
        if menu_id:
            allowed["menu_ids"].add(f"system.menu_{menu_id}")
        if action_id:
            allowed["action_ids"].add(f"/a/{action_id}")
    return {
        "snapshot_id": int(snapshot.get("id") or 0),
        "version": _text(snapshot.get("version")),
        "product_key": _text(snapshot.get("product_key")),
        "page_count": effective_count,
        "total_page_count": len(pages),
        "fingerprint": _text(release_draft.get("fingerprint")),
        "allowed": allowed,
    }


def _count_nav_nodes(nodes) -> int:
    total = 0
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        total += 1
        total += _count_nav_nodes(node.get("children"))
    return total


def _load_platform_release_gate(env, *, product_key: str) -> dict:
    requested_product_key = _text(product_key)
    if not requested_product_key:
        return {}
    try:
        platform_db = _text(env["ir.config_parameter"].sudo().get_param("smart_core.platform_release_db", ""))
    except Exception:
        platform_db = ""
    platform_db = platform_db or "sc_platform_core"
    current_db = _text(getattr(getattr(env, "cr", None), "dbname", ""))

    def _read_from(read_env) -> dict:
        try:
            model = read_env["sc.edition.release.snapshot"].sudo()
        except Exception:
            return {}
        snapshot = model.search(
            [
                ("product_key", "=", requested_product_key),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        return snapshot.to_runtime_dict() if snapshot else {}

    if platform_db == current_db:
        snapshot = _read_from(env)
    else:
        snapshot = {}
        try:
            registry = Registry(platform_db)
            with registry.cursor() as cr:
                read_env = api.Environment(cr, SUPERUSER_ID, dict(env.context or {}))
                snapshot = _read_from(read_env)
        except Exception as exc:
            return {
                "applied": False,
                "product_key": requested_product_key,
                "platform_db": platform_db,
                "reason": "PLATFORM_RELEASE_DB_UNAVAILABLE",
                "error": _text(exc),
            }
    if not snapshot:
        return {
            "applied": False,
            "product_key": requested_product_key,
            "platform_db": platform_db,
            "reason": "ACTIVE_RELEASE_SNAPSHOT_NOT_FOUND",
        }
    contract = _release_gate_page_contract_from_snapshot(snapshot)
    if int(contract.get("page_count") or 0) <= 0:
        return {
            "applied": False,
            "product_key": requested_product_key,
            "platform_db": platform_db,
            "reason": "ACTIVE_RELEASE_HAS_NO_PAGES",
            "snapshot_id": contract.get("snapshot_id"),
            "version": contract.get("version"),
        }
    contract["applied"] = True
    contract["platform_db"] = platform_db
    contract["reason"] = "OK"
    return contract


def _node_release_gate_keys(node: dict) -> set[str]:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    entry_target = meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {}
    compatibility_refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
    values = {
        _text(node.get("key")),
        _text(node.get("route")),
        _text(node.get("scene_key")),
        _text(node.get("menu_xmlid")),
        _text(node.get("model")),
        _text(meta.get("route")),
        _text(meta.get("scene_key")),
        _text(meta.get("menu_key")),
        _text(meta.get("menu_xmlid")),
        _text(meta.get("model")),
        _text(entry_target.get("route")),
        _text(entry_target.get("scene_key")),
        _text(compatibility_refs.get("model")),
    }
    menu_id = node.get("menu_id") or meta.get("menu_id") or compatibility_refs.get("menu_id")
    action_id = meta.get("action_id") or compatibility_refs.get("action_id")
    if menu_id:
        values.add(f"system.menu_{menu_id}")
    if action_id:
        values.add(f"/a/{action_id}")
    for option in meta.get("business_category_options") or []:
        if not isinstance(option, dict):
            continue
        option_menu_xmlid = _text(option.get("menu_xmlid"))
        if option_menu_xmlid:
            values.add(option_menu_xmlid)
        option_menu_id = option.get("menu_id")
        if option_menu_id:
            values.add(f"system.menu_{option_menu_id}")
    return {item for item in values if item}


def _node_is_user_acceptance_surface(node: dict, *, acceptance_matchers: dict | None = None) -> bool:
    matchers = acceptance_matchers if isinstance(acceptance_matchers, dict) else {}
    surface_tokens = matchers.get("tokens") if isinstance(matchers.get("tokens"), set) else set()
    surface_menu_ids = matchers.get("menu_ids") if isinstance(matchers.get("menu_ids"), set) else set()
    surface_action_ids = matchers.get("action_ids") if isinstance(matchers.get("action_ids"), set) else set()
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    entry_target = meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {}
    compatibility_refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
    menu_id = node.get("menu_id") or meta.get("menu_id") or compatibility_refs.get("menu_id")
    action_id = meta.get("action_id") or compatibility_refs.get("action_id")
    try:
        normalized_menu_id = int(menu_id or 0)
    except Exception:
        normalized_menu_id = 0
    try:
        normalized_action_id = int(action_id or 0)
    except Exception:
        normalized_action_id = 0
    if normalized_menu_id in surface_menu_ids or normalized_action_id in surface_action_ids:
        return True
    text = "/".join(
        _text(value)
        for value in (
            node.get("key"),
            node.get("name"),
            node.get("label"),
            node.get("title"),
            node.get("path"),
            node.get("complete_name"),
            node.get("menu_xmlid"),
            node.get("model"),
            meta.get("menu_xmlid"),
            meta.get("model"),
            compatibility_refs.get("model"),
        )
        if _text(value)
    )
    if surface_tokens and any(token in text for token in surface_tokens):
        return True
    return False


def _runtime_business_config_productization_sources(env) -> set[str]:
    payload = call_extension_hook_first(env, "smart_core_runtime_business_config_productization_sources", env)
    if not isinstance(payload, (list, tuple, set)):
        return set()
    return {_text(item) for item in payload if _text(item)}


def _runtime_business_config_protected_menu_refs(env) -> dict:
    refs = {"menu_ids": set(), "menu_xmlids": set()}
    if env is None:
        return refs
    try:
        from odoo.addons.smart_core.model.ui_menu_config_policy import _lowcode_system_config_menu_xmlids

        xmlids = {_text(xmlid) for xmlid in _lowcode_system_config_menu_xmlids(env) if _text(xmlid)}
    except Exception:
        xmlids = set()
    refs["menu_xmlids"] = xmlids
    if not xmlids:
        return refs
    try:
        ModelData = env["ir.model.data"].sudo()
        modules = {xmlid.split(".", 1)[0] for xmlid in xmlids if "." in xmlid}
        names = {xmlid.split(".", 1)[1] for xmlid in xmlids if "." in xmlid}
        rows = ModelData.search([
            ("model", "=", "ir.ui.menu"),
            ("module", "in", list(modules)),
            ("name", "in", list(names)),
        ])
    except Exception:
        rows = []
    for row in rows or []:
        xmlid = "%s.%s" % (_text(getattr(row, "module", "")), _text(getattr(row, "name", "")))
        try:
            menu_id = int(getattr(row, "res_id", 0) or 0)
        except Exception:
            menu_id = 0
        if xmlid in xmlids and menu_id:
            refs["menu_ids"].add(menu_id)
    return refs


def _node_is_protected_runtime_business_config_menu(node: dict, protected_refs: dict | None = None) -> bool:
    if not isinstance(protected_refs, dict):
        return False
    protected_menu_ids = protected_refs.get("menu_ids") if isinstance(protected_refs.get("menu_ids"), set) else set()
    protected_xmlids = protected_refs.get("menu_xmlids") if isinstance(protected_refs.get("menu_xmlids"), set) else set()
    if not protected_menu_ids and not protected_xmlids:
        return False
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    entry_target = meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {}
    compatibility_refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
    menu_id = node.get("menu_id") or meta.get("menu_id") or compatibility_refs.get("menu_id")
    try:
        normalized_menu_id = int(menu_id or 0)
    except Exception:
        normalized_menu_id = 0
    if normalized_menu_id and normalized_menu_id in protected_menu_ids:
        return True
    xmlid = _text(node.get("menu_xmlid") or meta.get("menu_xmlid") or compatibility_refs.get("menu_xmlid"))
    return bool(xmlid and xmlid in protected_xmlids)


def _node_is_runtime_business_config_entry(
    node: dict,
    *,
    env=None,
    productization_sources: set[str] | None = None,
    protected_menu_refs: dict | None = None,
    acceptance_matchers: dict | None = None,
) -> bool:
    """Keep already-authorized runtime configuration entries available."""
    if _node_is_user_acceptance_surface(node, acceptance_matchers=acceptance_matchers):
        return False
    if _node_is_protected_runtime_business_config_menu(node, protected_refs=protected_menu_refs):
        return True
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    productization_source = _text(meta.get("productization_source"))
    sources = productization_sources if isinstance(productization_sources, set) else _runtime_business_config_productization_sources(env)
    if productization_source and productization_source in sources:
        return True
    if _text(node.get("delivery_bucket")) == "delivery_business_config":
        return True
    if _text(meta.get("delivery_bucket")) == "delivery_business_config":
        return True
    model = _text(node.get("model") or meta.get("model"))
    if model in {MENU_CONFIG_POLICY_MODEL}:
        return True
    return False


def _filter_nav_by_release_gate(nav: list[dict], gate: dict, *, env=None) -> tuple[list[dict], dict]:
    if not isinstance(nav, list) or not gate.get("applied"):
        return nav if isinstance(nav, list) else [], {"applied": False}
    allowed = gate.get("allowed") if isinstance(gate.get("allowed"), dict) else {}
    allowed_values = set()
    for bucket in ("page_keys", "menu_keys", "menu_xmlids", "routes", "menu_ids", "action_ids"):
        values = allowed.get(bucket)
        if isinstance(values, set):
            allowed_values.update(values)
        elif isinstance(values, list):
            allowed_values.update(_text(item) for item in values if _text(item))
    kept_leaf_count = 0
    removed_leaf_count = 0
    runtime_business_config_count = 0
    runtime_business_config_sources = _runtime_business_config_productization_sources(env)
    protected_menu_refs = _runtime_business_config_protected_menu_refs(env)
    acceptance_matchers = _acceptance_surface_matchers(_resolve_user_acceptance_nav_contract(env))

    def _filter_node(node: dict):
        nonlocal kept_leaf_count, removed_leaf_count, runtime_business_config_count
        if not isinstance(node, dict):
            return None
        if _node_is_user_acceptance_surface(node, acceptance_matchers=acceptance_matchers):
            removed_leaf_count += 1
            return None
        children = node.get("children") if isinstance(node.get("children"), list) else []
        next_node = dict(node)
        if children:
            next_children = []
            for child in children:
                filtered = _filter_node(child)
                if filtered:
                    next_children.append(filtered)
            if not next_children:
                return None
            next_node["children"] = next_children
            return next_node

        if _node_is_runtime_business_config_entry(
            node,
            env=env,
            productization_sources=runtime_business_config_sources,
            protected_menu_refs=protected_menu_refs,
            acceptance_matchers=acceptance_matchers,
        ):
            kept_leaf_count += 1
            runtime_business_config_count += 1
            return next_node
        if _node_release_gate_keys(node) & allowed_values:
            kept_leaf_count += 1
            return next_node
        removed_leaf_count += 1
        return None

    filtered = [_filter_node(node) for node in nav]
    filtered = [node for node in filtered if node]
    return filtered, {
        "applied": True,
        "product_key": _text(gate.get("product_key")),
        "platform_db": _text(gate.get("platform_db")),
        "snapshot_id": int(gate.get("snapshot_id") or 0),
        "snapshot_version": _text(gate.get("version")),
        "fingerprint": _text(gate.get("fingerprint")),
        "allowed_page_count": int(gate.get("page_count") or 0),
        "kept_leaf_count": kept_leaf_count,
        "removed_leaf_count": removed_leaf_count,
        "runtime_business_config_passthrough_count": runtime_business_config_count,
    }


def _apply_user_menu_config_to_delivery_nav(env, nav: list[dict]) -> tuple[list[dict], dict]:
    if not isinstance(nav, list):
        return [], {"applied": False, "applied_count": 0, "hidden_count": 0, "renamed_count": 0, "reordered_count": 0}
    try:
        raw = env["ir.config_parameter"].sudo().get_param(MENU_CONFIG_NAV_ENABLED_PARAM, "")
    except Exception:
        raw = ""
    normalized = str(raw or "").strip().lower()
    if normalized in {"0", "false", "no", "off"}:
        return nav, {
            "applied": False,
            "reason": "disabled",
            MENU_CONFIG_NAV_ENABLED_PARAM: normalized,
            "applied_count": 0,
            "hidden_count": 0,
            "renamed_count": 0,
            "reordered_count": 0,
            "moved_count": 0,
        }

    def config_only_enabled() -> bool:
        try:
            raw = env["ir.config_parameter"].sudo().get_param(
                MENU_CONFIG_CONFIG_ONLY_PARAM,
                "1",
            )
        except Exception:
            raw = "1"
        return str(raw or "").strip().lower() not in {"0", "false", "no", "off"}

    try:
        policy_model = env[MENU_CONFIG_POLICY_MODEL]
    except Exception:
        config_only = config_only_enabled()
        meta = {
            "applied": False,
            "reason": "policy_model_unavailable",
            "runtime_source": MENU_CONFIG_POLICY_MODEL,
            "config_only": config_only,
            "applied_count": 0,
            "hidden_count": 0,
            "renamed_count": 0,
            "reordered_count": 0,
            "moved_count": 0,
        }
        if config_only:
            meta["unconfigured_hidden_count"] = _count_nav_nodes(nav)
            return [], meta
        return nav, meta
    overlaid, stats = policy_model.apply_runtime_overlay({"tree": nav, "flat": []}, user=env.user)
    next_nav = overlaid.get("tree") if isinstance(overlaid, dict) and isinstance(overlaid.get("tree"), list) else nav
    if not isinstance(stats, dict):
        stats = {}
    stats.setdefault("applied", True)
    return next_nav, stats


def _nav_node_label(node: dict) -> str:
    if not isinstance(node, dict):
        return ""
    return _text(node.get("label") or node.get("name") or node.get("title"))


def _nav_root_children(nav: list[dict]) -> list[dict]:
    if not isinstance(nav, list) or not nav:
        return []
    if len(nav) == 1 and isinstance(nav[0], dict):
        children = nav[0].get("children")
        if isinstance(children, list):
            return [child for child in children if isinstance(child, dict)]
    return [node for node in nav if isinstance(node, dict)]


def _release_product_center_signature(nav: list[dict]) -> list[str]:
    return [_nav_node_label(node) for node in _nav_root_children(nav) if _nav_node_label(node)]


def _apply_constrained_user_menu_config_to_released_nav(env, nav: list[dict]) -> tuple[list[dict], dict]:
    overlaid_nav, overlay_meta = _apply_user_menu_config_to_delivery_nav(env, nav)
    if not isinstance(overlay_meta, dict):
        overlay_meta = {}
    overlay_meta.setdefault("release_product_nav_constrained", True)

    before_signature = _release_product_center_signature(nav)
    after_signature = _release_product_center_signature(overlaid_nav)
    if before_signature != after_signature:
        blocked_meta = dict(overlay_meta)
        blocked_meta.update({
            "applied": False,
            "blocked": True,
            "reason": "blocked_product_center_signature_change",
            "release_product_nav_constrained": True,
            "before_center_signature": before_signature,
            "after_center_signature": after_signature,
        })
        return nav, blocked_meta

    overlay_meta["release_product_center_signature_preserved"] = True
    return overlaid_nav, overlay_meta


def _user_data_acceptance_nav_only_enabled(env) -> bool:
    try:
        raw = env["ir.config_parameter"].sudo().get_param(NAV_USER_DATA_ACCEPTANCE_ONLY_PARAM, "")
    except Exception:
        raw = ""
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def _filter_nav_for_user_data_acceptance_only(env, nav: list[dict], *, force: bool = False) -> tuple[list[dict], dict]:
    if not isinstance(nav, list) or (not force and not _user_data_acceptance_nav_only_enabled(env)):
        return nav if isinstance(nav, list) else [], {"applied": False}

    acceptance_contract = _resolve_user_acceptance_nav_contract(env)
    formal_group_labels = _string_set(acceptance_contract.get("formal_group_labels"))
    allowed_formal_labels = _string_set(acceptance_contract.get("formal_group_child_labels"))
    old_acceptance_group_labels = _string_set(acceptance_contract.get("old_acceptance_group_labels"))
    direct_acceptance_group_labels = _string_set(acceptance_contract.get("direct_acceptance_group_labels"))
    joint_acceptance_group_labels = _string_set(acceptance_contract.get("joint_acceptance_group_labels"))
    direct_acceptance_child_tokens = _string_set(acceptance_contract.get("direct_acceptance_child_tokens"))
    joint_acceptance_child_tokens = _string_set(acceptance_contract.get("joint_acceptance_child_tokens"))
    acceptance_root_labels = _string_set(acceptance_contract.get("acceptance_root_labels"))
    direct_acceptance_group_label = _text(acceptance_contract.get("direct_acceptance_group_label")) or "数据核对"
    joint_acceptance_group_label = _text(acceptance_contract.get("joint_acceptance_group_label")) or "数据核对"
    acceptance_root_group_label = _text(acceptance_contract.get("acceptance_root_group_label")) or "数据验收"
    formal_group = None
    old_acceptance_children = []
    direct_acceptance_children = []
    joint_acceptance_children = []
    acceptance_source_labels = {"old": [], "direct": [], "joint": []}
    required_old_acceptance_menu_xmlids = list(acceptance_contract.get("old_acceptance_menu_xmlids") or [])
    required_joint_acceptance_menu_xmlids = list(acceptance_contract.get("joint_acceptance_menu_xmlids") or [])
    required_contract_product_menu_xmlids = list(acceptance_contract.get("contract_product_menu_xmlids") or [])
    required_settlement_product_menu_xmlids = list(acceptance_contract.get("settlement_product_menu_xmlids") or [])
    contract_product_children = []
    settlement_product_children = []

    def has_nav_target(node: dict) -> bool:
        if not isinstance(node, dict):
            return False
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        return bool(
            node.get("route")
            or node.get("scene_key")
            or node.get("action_id")
            or node.get("model")
            or meta.get("route")
            or meta.get("scene_key")
            or meta.get("action_id")
            or meta.get("model")
        )

    def flatten_target_children(nodes: list[dict]) -> list[dict]:
        out = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                out.extend(flatten_target_children(children))
                continue
            if has_nav_target(node):
                out.append(node)
        return out

    def mark_acceptance_projection(nodes: list[dict], *, source_bucket: str) -> list[dict]:
        projected = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            next_node = dict(node)
            meta = dict(next_node.get("meta") if isinstance(next_node.get("meta"), dict) else {})
            meta["source"] = "user_data_acceptance_source_menu_projection"
            meta["acceptance_projection"] = True
            meta["acceptance_source_bucket"] = source_bucket
            next_node["meta"] = meta
            projected.append(next_node)
        return projected

    def menu_leaf_from_xmlid(xmlid: str) -> dict | None:
        try:
            menu = env.ref(xmlid, raise_if_not_found=False)
        except Exception:
            menu = None
        if not menu:
            return None
        try:
            action = menu.action
        except Exception:
            action = None
        action_id = int(getattr(action, "id", 0) or 0) if action else 0
        if action_id <= 0:
            return None
        model = _text(getattr(action, "res_model", ""))
        view_mode = _text(getattr(action, "view_mode", ""))
        view_modes = [_text(item) for item in view_mode.split(",") if _text(item)]
        menu_id = int(getattr(menu, "id", 0) or 0)
        label = _text(getattr(menu, "name", "")) or xmlid.rsplit(".", 1)[-1]
        route = f"/a/{action_id}?menu_id={menu_id}"
        sequence = int(getattr(menu, "sequence", 0) or 0)
        return {
            "key": f"runtime.acceptance.{xmlid}",
            "label": label,
            "title": label,
            "name": label,
            "menu_id": menu_id,
            "children": [],
            "route": route,
            "sequence": sequence,
            "meta": {
                "action_type": "delivery.engine",
                "menu_key": xmlid,
                "menu_xmlid": xmlid,
                "menu_id": menu_id,
                "action_id": action_id,
                "model": model,
                "view_modes": view_modes,
                "route": route,
                "delivery_bucket": "delivery_business_config",
                "source": "user_data_acceptance_only_runtime_completion",
                "source_authority": {
                    "kind": "user_data_acceptance_only_runtime_completion",
                    "authorities": ["ir.ui.menu", "ir.actions", MENU_CONFIG_POLICY_MODEL],
                    "projection_only": True,
                    "no_business_fact_authority": True,
                    "rebuildable": True,
                },
            },
        }

    def ensure_required_acceptance_children(xmlids: list[str], target_children: list[dict], source_bucket: str) -> int:
        existing_menu_ids = {
            int(node.get("menu_id") or 0)
            for node in target_children
            if isinstance(node, dict) and int(node.get("menu_id") or 0) > 0
        }
        added = 0
        for xmlid in xmlids:
            leaf = menu_leaf_from_xmlid(xmlid)
            menu_id = int((leaf or {}).get("menu_id") or 0)
            if not leaf or not menu_id or menu_id in existing_menu_ids:
                continue
            target_children.extend(mark_acceptance_projection([leaf], source_bucket=source_bucket))
            existing_menu_ids.add(menu_id)
            added += 1
        return added

    def ensure_required_old_acceptance_children() -> int:
        return ensure_required_acceptance_children(
            required_old_acceptance_menu_xmlids,
            old_acceptance_children,
            "old",
        )

    def ensure_required_joint_acceptance_children() -> int:
        return ensure_required_acceptance_children(
            required_joint_acceptance_menu_xmlids,
            joint_acceptance_children,
            "joint",
        )

    def ensure_required_product_children(xmlids: list[str], target_children: list[dict], key_prefix: str, source: str) -> int:
        existing_menu_ids = {
            int(node.get("menu_id") or 0)
            for node in target_children
            if isinstance(node, dict) and int(node.get("menu_id") or 0) > 0
        }
        added = 0
        for xmlid in xmlids:
            leaf = menu_leaf_from_xmlid(xmlid)
            menu_id = int((leaf or {}).get("menu_id") or 0)
            if not leaf or not menu_id or menu_id in existing_menu_ids:
                continue
            leaf = dict(leaf)
            leaf["key"] = f"{key_prefix}.{xmlid}"
            meta = dict(leaf.get("meta") or {})
            meta["source"] = source
            meta["delivery_bucket"] = "released_product_policy"
            leaf["meta"] = meta
            target_children.append(leaf)
            existing_menu_ids.add(menu_id)
            added += 1
        return added

    def ensure_required_contract_product_children() -> int:
        return ensure_required_product_children(
            required_contract_product_menu_xmlids,
            contract_product_children,
            "runtime.contract_product",
            "user_data_acceptance_only_contract_product_completion",
        )

    def ensure_required_settlement_product_children() -> int:
        return ensure_required_product_children(
            required_settlement_product_menu_xmlids,
            settlement_product_children,
            "runtime.settlement_product",
            "user_data_acceptance_only_settlement_product_completion",
        )

    def scan_groups(groups: list[dict]) -> None:
        nonlocal formal_group
        for group in groups or []:
            if not isinstance(group, dict):
                continue
            label = _text(group.get("label") or group.get("title") or group.get("name"))
            children = group.get("children") if isinstance(group.get("children"), list) else []
            if label in formal_group_labels:
                kept_children = [
                    child
                    for child in children
                    if isinstance(child, dict)
                    and _text(child.get("label") or child.get("title") or child.get("name")) in allowed_formal_labels
                ]
                if kept_children:
                    next_group = dict(group)
                    next_group["children"] = kept_children
                    formal_group = next_group
                continue
            if label in old_acceptance_group_labels:
                acceptance_source_labels["old"].append(label)
                old_acceptance_children.extend(
                    mark_acceptance_projection(flatten_target_children(children), source_bucket="old")
                )
                continue
            if label in acceptance_root_labels:
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    child_label = _text(child.get("label") or child.get("title") or child.get("name"))
                    child_children = child.get("children") if isinstance(child.get("children"), list) else []
                    if child_label in joint_acceptance_group_labels or any(token in child_label for token in joint_acceptance_child_tokens):
                        acceptance_source_labels["joint"].append(child_label or label)
                        joint_acceptance_children.extend(
                            mark_acceptance_projection(flatten_target_children(child_children), source_bucket="joint")
                        )
                    elif child_label in direct_acceptance_group_labels or any(token in child_label for token in direct_acceptance_child_tokens):
                        acceptance_source_labels["direct"].append(child_label or label)
                        direct_acceptance_children.extend(
                            mark_acceptance_projection(flatten_target_children(child_children), source_bucket="direct")
                        )
                    else:
                        acceptance_source_labels["direct"].append(child_label or label)
                        direct_acceptance_children.extend(
                            mark_acceptance_projection(flatten_target_children([child]), source_bucket="direct")
                        )
                continue
            if label in direct_acceptance_group_labels:
                acceptance_source_labels["direct"].append(label)
                direct_acceptance_children.extend(
                    mark_acceptance_projection(flatten_target_children(children), source_bucket="direct")
                )
                continue
            if label in joint_acceptance_group_labels:
                acceptance_source_labels["joint"].append(label)
                joint_acceptance_children.extend(
                    mark_acceptance_projection(flatten_target_children(children), source_bucket="joint")
                )
                continue

    root_nodes = []
    for node in nav:
        if not isinstance(node, dict):
            continue
        children = node.get("children") if isinstance(node.get("children"), list) else []
        if children:
            scan_groups(children)
            root_nodes.append(dict(node))
        else:
            scan_groups([node])

    old_acceptance_completion_count = ensure_required_old_acceptance_children()
    joint_acceptance_completion_count = ensure_required_joint_acceptance_children()
    contract_product_completion_count = ensure_required_contract_product_children()
    settlement_product_completion_count = ensure_required_settlement_product_children()

    def acceptance_project_group(*, key: str, label: str, children: list[dict], source_bucket: str) -> dict:
        return {
            "key": key,
            "label": label,
            "title": label,
            "children": children,
            "meta": {
                "group_key": key.replace("group:", "", 1),
                "source": "user_data_acceptance_source_menu_projection",
                "acceptance_projection": True,
                "acceptance_source_bucket": source_bucket,
                "source_labels": acceptance_source_labels[source_bucket],
            },
        }

    next_children = []
    next_children.extend(old_acceptance_children)
    if direct_acceptance_children:
        next_children.append(
            acceptance_project_group(
                key="group:direct_project_data_acceptance",
                label=direct_acceptance_group_label,
                children=direct_acceptance_children,
                source_bucket="direct",
            )
        )
    if joint_acceptance_children:
        next_children.append(
            acceptance_project_group(
                key="group:joint_project_data_acceptance",
                label=joint_acceptance_group_label,
                children=joint_acceptance_children,
                source_bucket="joint",
            )
        )

    if not next_children:
        return [], {
            "applied": True,
            "formal_entry_count": 0,
            "acceptance_group_count": 0,
            "reason": "no_matching_entries",
        }

    return next_children, {
        "applied": True,
        "formal_entry_count": len(formal_group.get("children") or []) if formal_group else 0,
        "old_acceptance_entry_count": len(old_acceptance_children),
        "old_acceptance_completion_count": old_acceptance_completion_count,
        "direct_acceptance_entry_count": len(direct_acceptance_children),
        "joint_acceptance_entry_count": len(joint_acceptance_children),
        "joint_acceptance_completion_count": joint_acceptance_completion_count,
        "contract_product_entry_count": len(contract_product_children),
        "contract_product_completion_count": contract_product_completion_count,
        "settlement_product_entry_count": len(settlement_product_children),
        "settlement_product_completion_count": settlement_product_completion_count,
        "acceptance_source_labels": acceptance_source_labels,
    }


def _append_user_data_acceptance_nav_group(nav: list[dict], acceptance_children: list[dict]) -> list[dict]:
    if not isinstance(nav, list) or not acceptance_children:
        return nav if isinstance(nav, list) else []

    acceptance_group = {
        "key": "group:user_data_acceptance",
        "label": acceptance_root_group_label,
        "title": acceptance_root_group_label,
        "children": acceptance_children,
        "sequence": 910,
        "meta": {
            "group_key": "user_data_acceptance",
            "source": "user_data_acceptance_runtime_projection",
            "projection_only": True,
        },
    }

    next_nav = []
    inserted = False
    for node in nav:
        if not isinstance(node, dict):
            continue
        node = dict(node)
        children = node.get("children") if isinstance(node.get("children"), list) else []
        if not inserted and children:
            existing_keys = {
                str(child.get("key") or "").strip()
                for child in children
                if isinstance(child, dict)
            }
            existing_labels = {
                str(child.get("label") or child.get("title") or child.get("name") or "").strip()
                for child in children
                if isinstance(child, dict)
            }
            if acceptance_group["key"] not in existing_keys and acceptance_group["label"] not in existing_labels:
                node["children"] = children + [acceptance_group]
            inserted = True
        next_nav.append(node)

    if not inserted:
        next_nav.append(acceptance_group)
    return next_nav


def _remove_nav_groups_by_label(nav: list[dict], labels: set[str]) -> list[dict]:
    if not isinstance(nav, list) or not labels:
        return nav if isinstance(nav, list) else []
    out = []
    for node in nav:
        if not isinstance(node, dict):
            continue
        node_label = _text(node.get("label") or node.get("title") or node.get("name"))
        if node_label in labels:
            continue
        next_node = dict(node)
        children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
        if children:
            next_node["children"] = _remove_nav_groups_by_label(children, labels)
        out.append(next_node)
    return out


def _unwrap_internal_nav_groups(nav: list[dict], labels: set[str]) -> list[dict]:
    if not isinstance(nav, list) or not labels:
        return nav if isinstance(nav, list) else []

    def unwrap(nodes: list[dict]) -> list[dict]:
        out = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            next_node = dict(node)
            children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
            if children:
                next_node["children"] = unwrap(children)
            node_label = _text(next_node.get("label") or next_node.get("title") or next_node.get("name"))
            if node_label in labels:
                out.extend(next_node.get("children") if isinstance(next_node.get("children"), list) else [])
                continue
            out.append(next_node)
        return out

    return unwrap(nav)


def _resolve_business_nav_group_display_order(env) -> dict:
    order = dict(_BUSINESS_NAV_GROUP_DISPLAY_ORDER)
    hook_payload = call_extension_hook_first(env, "smart_core_business_nav_group_display_order", env)
    if isinstance(hook_payload, dict):
        for label, sequence in hook_payload.items():
            label = _text(label)
            if not label:
                continue
            try:
                order[label] = int(sequence)
            except Exception:
                continue
    return order


def _sort_business_nav_groups(nav: list[dict], display_order: dict | None = None) -> list[dict]:
    if not isinstance(nav, list):
        return []
    order = display_order if isinstance(display_order, dict) else _BUSINESS_NAV_GROUP_DISPLAY_ORDER

    def sequence_value(node: dict) -> int:
        try:
            return int(node.get("sequence") or 0)
        except Exception:
            return 0

    def sort_key(node: dict) -> tuple[int, int, str]:
        label = _text(node.get("label") or node.get("title") or node.get("name"))
        return (
            order.get(label, 900),
            sequence_value(node),
            label,
        )

    sorted_nodes = []
    for node in nav:
        if not isinstance(node, dict):
            continue
        next_node = dict(node)
        label = _text(next_node.get("label") or next_node.get("title") or next_node.get("name"))
        group_sequence = order.get(label)
        if group_sequence is not None:
            next_node["sequence"] = group_sequence
            meta = next_node.get("meta")
            if not isinstance(meta, dict):
                meta = {}
                next_node["meta"] = meta
            meta["sequence"] = group_sequence
        children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
        if children:
            next_node["children"] = _sort_business_nav_groups(children, order)
        sorted_nodes.append(next_node)
    return sorted(sorted_nodes, key=sort_key)


def _dedupe_nav_siblings_by_identity(nav: list[dict]) -> list[dict]:
    if not isinstance(nav, list):
        return []

    def node_menu_xmlid(node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        return _text(node.get("menu_xmlid") or meta.get("menu_xmlid") or meta.get("menu_key"))

    def node_identity(node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        target = node.get("target") if isinstance(node.get("target"), dict) else {}
        children = node.get("children") if isinstance(node.get("children"), list) else []
        label = _text(node.get("label") or node.get("title") or node.get("name"))
        model = _text(node.get("model") or meta.get("model"))
        category_code = _text(meta.get("default_business_category_code"))
        integration_target = _text(meta.get("integration_target"))
        entry_intent = _text(meta.get("entry_intent"))
        if (
            not children
            and label
            and model
            and (category_code or integration_target or entry_intent)
        ):
            return "semantic:%s:%s:%s:%s:%s" % (
                label,
                model,
                category_code,
                integration_target,
                entry_intent,
            )
        return _text(
            node.get("menu_id")
            or meta.get("menu_id")
            or target.get("menu_id")
            or node_menu_xmlid(node)
            or node.get("key")
        )

    def merge_node(base: dict, incoming: dict) -> dict:
        merged = dict(base)
        for key, value in incoming.items():
            if key in {"children", "meta"}:
                continue
            if merged.get(key) in (None, "", [], {}):
                merged[key] = value
        base_meta = merged.get("meta") if isinstance(merged.get("meta"), dict) else {}
        incoming_meta = incoming.get("meta") if isinstance(incoming.get("meta"), dict) else {}
        if incoming_meta:
            next_meta = dict(incoming_meta)
            next_meta.update(base_meta)
            merged["meta"] = next_meta
        children = []
        if isinstance(base.get("children"), list):
            children.extend(base.get("children") or [])
        if isinstance(incoming.get("children"), list):
            children.extend(incoming.get("children") or [])
        if children:
            merged["children"] = dedupe(children)
        return merged

    def dedupe(nodes: list[dict]) -> list[dict]:
        out = []
        by_identity = {}
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            next_node = dict(node)
            children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
            if children:
                next_node["children"] = dedupe(children)
            identity = node_identity(next_node)
            if identity and identity in by_identity:
                index = by_identity[identity]
                out[index] = merge_node(out[index], next_node)
                continue
            if identity:
                by_identity[identity] = len(out)
            out.append(next_node)
        return out

    return dedupe(nav)


def _rehome_business_master_data_nav_groups(nav: list[dict], display_order: dict | None = None) -> list[dict]:
    if not isinstance(nav, list):
        return []
    order = display_order if isinstance(display_order, dict) else _BUSINESS_NAV_GROUP_DISPLAY_ORDER

    extracted: list[dict] = []
    seen = set()

    def node_menu_xmlid(node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        return _text(node.get("menu_xmlid") or meta.get("menu_xmlid") or meta.get("menu_key"))

    def node_identity(node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        return _text(node.get("menu_id") or meta.get("menu_id") or node_menu_xmlid(node) or node.get("key"))

    def remove_master_leaves(nodes: list[dict]) -> list[dict]:
        out = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            next_node = dict(node)
            children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
            if children:
                next_node["children"] = remove_master_leaves(children)
                out.append(next_node)
                continue
            if node_menu_xmlid(next_node) in _BUSINESS_MASTER_DATA_MENU_XMLIDS:
                identity = node_identity(next_node)
                if identity and identity not in seen:
                    seen.add(identity)
                    extracted.append(next_node)
                continue
            out.append(next_node)
        return out

    next_nav = remove_master_leaves(nav)
    if not extracted:
        return next_nav

    extracted.sort(key=lambda node: (int(node.get("sequence") or 0), int(node.get("menu_id") or 0)))
    master_group = {
        "key": "group:catalog.基础资料",
        "label": "基础资料",
        "title": "基础资料",
        "children": extracted,
        "sequence": order["基础资料"],
        "meta": {
            "group_key": "catalog.基础资料",
            "source": "business_master_data_runtime_rehome",
            "sequence": order["基础资料"],
        },
    }

    for root in next_nav:
        if not isinstance(root, dict):
            continue
        children = root.get("children") if isinstance(root.get("children"), list) else []
        if not children:
            continue
        merged = False
        next_children = []
        for child in children:
            if not isinstance(child, dict):
                continue
            label = _text(child.get("label") or child.get("title") or child.get("name"))
            if label == "基础资料":
                child = dict(child)
                existing = child.get("children") if isinstance(child.get("children"), list) else []
                child["children"] = extracted + existing
                child["sequence"] = order["基础资料"]
                merged = True
            next_children.append(child)
        if not merged:
            next_children.append(master_group)
        root["children"] = next_children
        return next_nav

    next_nav.append(master_group)
    return next_nav


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
    SOURCE_KIND = "odoo_native_startup_surface_projection"
    SOURCE_AUTHORITIES = (
        "res.users",
        "res.groups",
        "ir.ui.menu",
        "ir.actions",
        "sc.scene",
        "sc.capability",
        "ui_base_contract_asset",
        "ir.module.module",
    )

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

        SystemInitPayloadBuilder.attach_platform_company_access_facts(data, env, user)
        prepare_runtime_context_ts = _mark_substage(
            "prepare_runtime_context",
            "attach_platform_company_access_facts",
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
        extension_context = dict(env.context or {})
        if isinstance(self.context, dict):
            extension_context.update(self.context)
        extension_env = api.Environment(env.cr, env.uid, extension_context)
        run_extension_hooks(extension_env, "smart_core_extend_system_init", data, extension_env, user)
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
        include_workspace_home = parse_bool(params.get("with_preload"), False) or "workspace_home" in with_tokens
        if include_workspace_home:
            data["workspace_home"] = build_workspace_home_contract(data)
        else:
            data.pop("workspace_home", None)
        data["page_contracts"] = build_page_contracts(data)
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

        delivery_identity = _resolve_startup_delivery_identity(env, params)
        platform_minimum_surface_mode = _is_platform_minimum_surface_mode(env, delivery_identity=delivery_identity)
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
        delivery_engine = DeliveryEngine(env)
        delivery_edition_key = str(delivery_identity.get("edition_key") or "standard").strip() or "standard"
        requested_product_key = str(delivery_identity.get("product_key") or "").strip()
        requested_base_product_key = str(delivery_identity.get("base_product_key") or "").strip()
        delivery_payload = delivery_engine.build(
            data=data if isinstance(data, dict) else {},
            product_key=requested_product_key,
            edition_key=delivery_edition_key,
            base_product_key=requested_base_product_key,
            native_nav=nav_tree,
        )
        release_snapshot_service = EditionReleaseSnapshotService(env)
        release_audit_service = ReleaseAuditTrailService(env)
        data["delivery_engine_v1"] = delivery_payload
        delivery_release_navigation = build_release_navigation_contract({"delivery_engine_v1": delivery_payload})
        edition_diagnostics = (
            delivery_payload.get("product_policy", {}).get("edition_diagnostics")
            if isinstance(delivery_payload.get("product_policy"), dict)
            else {}
        )
        effective_base_product_key = str(delivery_payload.get("base_product_key") or requested_base_product_key).strip() or requested_base_product_key
        effective_edition_key = str(delivery_payload.get("edition_key") or "standard").strip() or "standard"
        effective_product_key = str(delivery_payload.get("product_key") or f"{effective_base_product_key}.{effective_edition_key}").strip()
        release_gate = _load_platform_release_gate(env, product_key=effective_product_key)
        if release_gate.get("applied"):
            gated_nav, gate_meta = _filter_nav_by_release_gate(
                delivery_payload.get("nav") if isinstance(delivery_payload.get("nav"), list) else [],
                release_gate,
                env=env,
            )
            gated_nav, user_menu_config_meta = _apply_constrained_user_menu_config_to_released_nav(env, gated_nav)
            gated_nav, post_overlay_gate_meta = _filter_nav_by_release_gate(gated_nav, release_gate, env=env)
            delivery_payload["nav"] = gated_nav
            meta = delivery_payload.get("meta")
            if not isinstance(meta, dict):
                meta = {}
                delivery_payload["meta"] = meta
            meta["platform_release_gate"] = gate_meta
            meta["platform_release_gate_after_user_menu_config"] = post_overlay_gate_meta
            meta["user_menu_config"] = user_menu_config_meta
        else:
            delivery_nav, user_menu_config_meta = _apply_user_menu_config_to_delivery_nav(
                env,
                delivery_payload.get("nav") if isinstance(delivery_payload.get("nav"), list) else [],
            )
            delivery_payload["nav"] = delivery_nav
            meta = delivery_payload.get("meta")
            if not isinstance(meta, dict):
                meta = {}
                delivery_payload["meta"] = meta
            meta["platform_release_gate"] = {
                "applied": False,
                "product_key": effective_product_key,
                "platform_db": _text(release_gate.get("platform_db")),
                "reason": _text(release_gate.get("reason")) or "NOT_APPLIED",
            }
            meta["user_menu_config"] = user_menu_config_meta
        released_snapshot_lineage = release_snapshot_service.resolve_active_snapshot_lineage(product_key=effective_product_key)
        release_audit_trail_summary = release_audit_service.build_runtime_summary(product_key=effective_product_key)
        runtime_diagnostics = dict(edition_diagnostics) if isinstance(edition_diagnostics, dict) else {}
        runtime_diagnostics["platform_release_gate"] = (
            delivery_payload.get("meta", {}).get("platform_release_gate")
            if isinstance(delivery_payload.get("meta"), dict)
            else {}
        )
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
                "base_product_key": requested_base_product_key,
                "edition_key": delivery_edition_key,
                "identity_source": str(delivery_identity.get("source") or ""),
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
                "builder_source": str(delivery_release_navigation.get("source") or ""),
                "builder_contract_version": str(delivery_release_navigation.get("contract_version") or ""),
                "builder_source_authority": delivery_release_navigation.get("source_authority")
                if isinstance(delivery_release_navigation.get("source_authority"), dict)
                else {},
            },
        }
        delivery_nav = delivery_payload.get("nav") if isinstance(delivery_payload.get("nav"), list) else []
        if delivery_nav and not platform_minimum_surface_mode:
            delivery_nav, user_data_acceptance_meta = _filter_nav_for_user_data_acceptance_only(env, delivery_nav)
            if not user_data_acceptance_meta.get("applied"):
                user_data_acceptance_meta = {
                    "applied": False,
                    "projected": False,
                    "reason": "delivery_engine_product_navigation_authority",
                }
            else:
                source_menu_group_labels_to_hide = _string_set(
                    _resolve_user_acceptance_nav_contract(env).get("source_menu_group_labels_to_hide")
                )
                delivery_nav = _remove_nav_groups_by_label(delivery_nav, source_menu_group_labels_to_hide)
                user_data_acceptance_meta["source_user_check_menu_hidden"] = bool(source_menu_group_labels_to_hide)
            formal_product_menu_meta = {
                "applied": False,
                "reason": "delivery_engine_released_by_product_policy",
            }
            delivery_meta = delivery_payload.get("meta") if isinstance(delivery_payload.get("meta"), dict) else {}
            delivery_user_menu_config_meta = (
                delivery_meta.get("user_menu_config")
                if isinstance(delivery_meta.get("user_menu_config"), dict)
                else {
                    "applied": False,
                    "reason": "not_reported_by_delivery_pre_filter",
                }
            )
            delivery_payload["nav"] = delivery_nav
            if isinstance(data.get("delivery_engine_v1"), dict):
                data["delivery_engine_v1"]["nav"] = delivery_nav
            if isinstance(data.get("release_navigation_v1"), dict):
                data["release_navigation_v1"]["nav"] = delivery_nav
                release_meta = data["release_navigation_v1"].get("meta")
                if not isinstance(release_meta, dict):
                    release_meta = {}
                    data["release_navigation_v1"]["meta"] = release_meta
                release_meta["user_data_acceptance_only"] = user_data_acceptance_meta
                release_meta["formal_product_menu_policy"] = formal_product_menu_meta
                release_meta["user_menu_config"] = delivery_user_menu_config_meta
                release_meta["system_init_nav_boundary"] = {
                    "authority": "delivery_engine_v1",
                    "semantic_post_processing": False,
                    "allowed_runtime_filters": [
                        "platform_release_gate",
                        "explicit_user_data_acceptance_only",
                        "explicit_user_menu_config_overlay",
                    ],
                }
            data["nav_role_surface"] = data.get("nav") if isinstance(data.get("nav"), list) else []
            data["nav"] = delivery_nav
            nav_meta = data.get("nav_meta") if isinstance(data.get("nav_meta"), dict) else {}
            nav_meta["nav_source"] = "delivery_engine_v1"
            nav_meta["primary_nav_promoted_from"] = "release_navigation_v1"
            nav_meta["role_surface_nav_preserved"] = True
            nav_meta["platform_release_gate"] = (
                delivery_payload.get("meta", {}).get("platform_release_gate")
                if isinstance(delivery_payload.get("meta"), dict)
                else {}
            )
            nav_meta["user_data_acceptance_only"] = user_data_acceptance_meta
            nav_meta["formal_product_menu_policy"] = formal_product_menu_meta
            nav_meta["user_menu_config"] = delivery_user_menu_config_meta
            nav_meta["system_init_nav_boundary"] = {
                "authority": "delivery_engine_v1",
                "semantic_post_processing": False,
            }
            data["nav_meta"] = nav_meta

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
        snapshot_ext = (
            data.get("ext_facts")
            if isinstance(data.get("ext_facts"), dict)
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
        if contract_mode == "hud" and isinstance(scene_diagnostics, dict):
            data["scene_diagnostics"] = scene_diagnostics
        # Carry the already-authorized delivery projection into the startup
        # contract at the final handler boundary.  This prevents an earlier
        # minimal-surface/default pass from replacing a non-empty projection
        # with an empty release payload.
        _delivery_final = data.get("delivery_engine_v1") if isinstance(data.get("delivery_engine_v1"), dict) else {}
        _release_final = data.get("release_navigation_v1") if isinstance(data.get("release_navigation_v1"), dict) else {}
        if isinstance(_delivery_final.get("nav"), list) and _delivery_final.get("nav"):
            _release_final = dict(_release_final)
            _release_final["nav"] = _delivery_final["nav"]
            data["release_navigation_v1"] = _release_final
        data = SystemInitPayloadBuilder.build_startup_surface(
            data,
            params=params,
            build_mode=build_mode,
            inspect_payload=startup_inspect,
        )
        SystemInitPayloadBuilder.attach_layered_contract(data)
        try:
            data = apply_dictionary_startup_data(env, data)
        except Exception:
            pass
        data = _normalize_access_suggested_action(data)
        data["project_context"] = build_record_context_contract(env, params)
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
        meta_with_etag = dict(meta_with_etag or {})
        meta_with_etag.setdefault("source_kind", self.SOURCE_KIND)
        meta_with_etag.setdefault("source_authorities", list(self.SOURCE_AUTHORITIES))
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
            if isinstance(scene_diagnostics, dict):
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
