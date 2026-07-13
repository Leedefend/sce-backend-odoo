# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

_REGISTRY_EXPORTS = (
    "SOURCE_KIND",
    "SOURCE_AUTHORITIES",
    "NO_BUSINESS_FACT_AUTHORITY",
    "LEGACY_INDUSTRY_GOVERNANCE_SOURCE_KIND",
    "LEGACY_USER_SURFACE_MODEL_POLICY_SOURCE_KIND",
    "LEGACY_RECORD_CONTEXT_CLEAR_MODELS",
    "LEGACY_DELETE_ONLY_MODELS",
    "_LEGACY_STANDARD_LIST_PROFILE_REGISTRY",
    "_LEGACY_FIELD_PRESENTATION_REGISTRY",
    "_LEGACY_PROJECT_FORM_GOVERNANCE_MODELS",
    "_LEGACY_PROJECT_FORM_PROFILE_REGISTRY",
    "_LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS",
    "_LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS",
    "_LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY",
    "_LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY",
    "_LEGACY_KANBAN_ROW_ACTION_REGISTRY",
    "_CAPABILITY_GROUP_PROFILE_REGISTRY",
    "_SCENE_SEMANTIC_PROFILE_REGISTRY",
    "CONTRACT_MODES",
    "CONTRACT_SURFACES",
    "_NON_HUD_STRIP_KEYS",
    "_USER_MODE_STRIP_KEYS",
    "_USER_CAPABILITY_KEYS",
    "_USER_SCENE_KEYS",
    "_USER_SCENE_TARGET_KEYS",
    "_USER_SCENE_TILE_KEYS",
    "_USER_SCENE_ACCESS_KEYS",
    "_PROJECT_FORM_PAGE_PRESERVE_FIELDS",
    "_BUSINESS_DETAIL_RELATION_FIELDS",
    "_TECHNICAL_RELATION_FIELD_PREFIXES",
    "_PROJECT_FORM_FIELD_MAX",
    "_PROJECT_FORM_HEADER_ACTION_MAX",
    "_PROJECT_FORM_SMART_ACTION_MAX",
    "_ENTERPRISE_COMPANY_FORM_FIELDS",
    "_ENTERPRISE_COMPANY_FIELD_LABELS",
    "_ENTERPRISE_DEPARTMENT_FORM_FIELDS",
    "_ENTERPRISE_DEPARTMENT_FIELD_LABELS",
    "_ENTERPRISE_USER_FORM_FIELDS",
    "_ENTERPRISE_USER_FIELD_LABELS",
    "_PROJECT_FORM_ACTION_GROUP_LIMIT",
    "_PROJECT_FORM_DEFAULT_ACTION_GROUP_LABELS",
    "_FORM_CORE_FIELD_MAX",
    "_FORM_ACTION_PRIMARY_KEYWORDS",
    "_FORM_ACTION_READONLY_KEYWORDS",
    "_FORM_PRIMARY_DISABLED_REASON",
    "_FORM_DISABLED_REASON_CAPABILITY",
    "_FORM_DISABLED_REASON_LIFECYCLE",
    "_FORM_DISABLED_REASON_GROUP",
    "_FORM_DISABLED_REASON_ROLE",
    "_FORM_SCENE_PROFILE_DEFAULT",
    "_FORM_SCENE_PROFILE_PROJECT",
    "_CAPABILITY_GROUP_DEFAULTS",
    "_CONTRACT_KEY_CANONICAL_MAP",
    "_TIER_REVIEW_LIST_NAV_ACTION_PREFIXES",
    "_BUSINESS_FIELD_LABEL_OVERRIDES",
    "_USER_SURFACE_ACTION_GROUP_LABELS",
    "_USER_SURFACE_NOISE_MARKERS",
    "_USER_SURFACE_FILTER_MAX",
    "_USER_SURFACE_ACTION_MAX",
    "_USER_SURFACE_PRIMARY_FILTER_MAX",
    "_USER_SURFACE_PRIMARY_ACTION_MAX",
    "_RENDER_PROFILE_CREATE",
    "_RENDER_PROFILE_EDIT",
    "_RENDER_PROFILE_READONLY",
    "_RENDER_PROFILES",
)


def _load_sibling_module(module_name: str, file_name: str) -> Any:
    try:
        if __package__:
            return importlib.import_module(f"{__package__}.{module_name}")
    except ImportError:
        pass
    spec = importlib.util.spec_from_file_location(
        module_name,
        Path(__file__).with_name(file_name),
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to load {file_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_registry_module() -> Any:
    return _load_sibling_module("contract_governance_registry", "contract_governance_registry.py")


_registry = _load_registry_module()
globals().update({name: getattr(_registry, name) for name in _REGISTRY_EXPORTS})
# Compatibility marker for source-level authority guards:
# NO_BUSINESS_FACT_AUTHORITY = True is defined in contract_governance_registry.py.


def _load_user_surface_module() -> Any:
    return _load_sibling_module("contract_governance_user_surface", "contract_governance_user_surface.py")


_user_surface = _load_user_surface_module()


def _load_capabilities_module() -> Any:
    return _load_sibling_module("contract_governance_capabilities", "contract_governance_capabilities.py")


_capabilities = _load_capabilities_module()
_capabilities._CAPABILITY_GROUP_DEFAULTS = _CAPABILITY_GROUP_DEFAULTS
_capabilities._CAPABILITY_GROUP_PROFILE_REGISTRY = _CAPABILITY_GROUP_PROFILE_REGISTRY
_has_demo_semantics = _capabilities._has_demo_semantics
_normalized_tags_for_item = _capabilities._normalized_tags_for_item
is_internal_or_smoke = _capabilities.is_internal_or_smoke


def normalize_capabilities(capabilities: list) -> list[dict]:
    return _capabilities.normalize_capabilities(capabilities)


def _load_scenes_module() -> Any:
    return _load_sibling_module("contract_governance_scenes", "contract_governance_scenes.py")


_scenes = _load_scenes_module()
_scenes._SCENE_SEMANTIC_PROFILE_REGISTRY = _SCENE_SEMANTIC_PROFILE_REGISTRY
_normalize_scene_list_profile = _scenes._normalize_scene_list_profile
_derive_scene_meta = _scenes._derive_scene_meta


def normalize_scenes(scenes: list) -> list[dict]:
    return _scenes.normalize_scenes(scenes)


def _load_list_surface_module() -> Any:
    return _load_sibling_module("contract_governance_list_surface", "contract_governance_list_surface.py")


_list_surface = _load_list_surface_module()


def _load_native_bridge_module() -> Any:
    return _load_sibling_module("contract_governance_native_bridge", "contract_governance_native_bridge.py")


_native_bridge = _load_native_bridge_module()
_native_bridge._USER_SURFACE_ACTION_MAX = _USER_SURFACE_ACTION_MAX


def _load_labels_module() -> Any:
    return _load_sibling_module("contract_governance_labels", "contract_governance_labels.py")


_labels = _load_labels_module()
_labels._BUSINESS_FIELD_LABEL_OVERRIDES = _BUSINESS_FIELD_LABEL_OVERRIDES
_labels._LEGACY_FIELD_PRESENTATION_REGISTRY = _LEGACY_FIELD_PRESENTATION_REGISTRY


def _load_access_policy_module() -> Any:
    return _load_sibling_module("contract_governance_access_policy", "contract_governance_access_policy.py")


_access_policy = _load_access_policy_module()


def _load_canonicalization_module() -> Any:
    return _load_sibling_module("contract_governance_canonicalization", "contract_governance_canonicalization.py")


_canonicalization = _load_canonicalization_module()
_canonicalization._CONTRACT_KEY_CANONICAL_MAP = _CONTRACT_KEY_CANONICAL_MAP


def _load_domain_overrides_module() -> Any:
    return _load_sibling_module("contract_governance_domain_overrides", "contract_governance_domain_overrides.py")


_domain_overrides = _load_domain_overrides_module()


def _load_surface_mapping_module() -> Any:
    return _load_sibling_module("contract_governance_surface_mapping", "contract_governance_surface_mapping.py")


_surface_mapping = _load_surface_mapping_module()


def _load_create_profile_module() -> Any:
    return _load_sibling_module("contract_governance_create_profile", "contract_governance_create_profile.py")


_create_profile = _load_create_profile_module()
_create_profile._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE


def _load_field_semantics_module() -> Any:
    return _load_sibling_module("contract_governance_field_semantics", "contract_governance_field_semantics.py")


_field_semantics = _load_field_semantics_module()
_field_semantics._PROJECT_FORM_PAGE_PRESERVE_FIELDS = _PROJECT_FORM_PAGE_PRESERVE_FIELDS
_field_semantics._BUSINESS_DETAIL_RELATION_FIELDS = _BUSINESS_DETAIL_RELATION_FIELDS
_field_semantics._TECHNICAL_RELATION_FIELD_PREFIXES = _TECHNICAL_RELATION_FIELD_PREFIXES
_field_semantics._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_field_semantics._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_field_semantics._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY


def _load_form_layout_module() -> Any:
    return _load_sibling_module("contract_governance_form_layout", "contract_governance_form_layout.py")


_form_layout = _load_form_layout_module()
_form_layout._ENTERPRISE_COMPANY_FIELD_LABELS = _ENTERPRISE_COMPANY_FIELD_LABELS
_form_layout._ENTERPRISE_USER_FIELD_LABELS = _ENTERPRISE_USER_FIELD_LABELS


def _load_form_actions_module() -> Any:
    return _load_sibling_module("contract_governance_form_actions", "contract_governance_form_actions.py")


_form_actions = _load_form_actions_module()
_form_actions._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_actions._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_actions._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY
_form_actions._RENDER_PROFILES = _RENDER_PROFILES
_form_actions._FORM_ACTION_PRIMARY_KEYWORDS = _FORM_ACTION_PRIMARY_KEYWORDS
_form_actions._FORM_ACTION_READONLY_KEYWORDS = _FORM_ACTION_READONLY_KEYWORDS
_form_actions._FORM_PRIMARY_DISABLED_REASON = _FORM_PRIMARY_DISABLED_REASON
_form_actions._FORM_DISABLED_REASON_CAPABILITY = _FORM_DISABLED_REASON_CAPABILITY
_form_actions._FORM_DISABLED_REASON_LIFECYCLE = _FORM_DISABLED_REASON_LIFECYCLE
_form_actions._FORM_DISABLED_REASON_GROUP = _FORM_DISABLED_REASON_GROUP
_form_actions._FORM_DISABLED_REASON_ROLE = _FORM_DISABLED_REASON_ROLE
_form_actions._FORM_SCENE_PROFILE_PROJECT = _FORM_SCENE_PROFILE_PROJECT


def _load_form_render_module() -> Any:
    return _load_sibling_module("contract_governance_form_render", "contract_governance_form_render.py")


_form_render = _load_form_render_module()
_form_render._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_render._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_render._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY
_form_render._RENDER_PROFILES = _RENDER_PROFILES


def _load_form_validation_module() -> Any:
    return _load_sibling_module("contract_governance_form_validation", "contract_governance_form_validation.py")


_form_validation = _load_form_validation_module()
_form_validation._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_validation._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_validation._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY
_form_validation._RENDER_PROFILES = _RENDER_PROFILES


def _load_form_fields_module() -> Any:
    return _load_sibling_module("contract_governance_form_fields", "contract_governance_form_fields.py")


_form_fields = _load_form_fields_module()
_form_fields._BUSINESS_DETAIL_RELATION_FIELDS = _BUSINESS_DETAIL_RELATION_FIELDS
_form_fields._FORM_CORE_FIELD_MAX = _FORM_CORE_FIELD_MAX
_form_fields._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_fields._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_fields._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY


def _load_project_form_module() -> Any:
    return _load_sibling_module("contract_governance_project_form", "contract_governance_project_form.py")


_project_form = _load_project_form_module()


def _load_enterprise_forms_module() -> Any:
    return _load_sibling_module("contract_governance_enterprise_forms", "contract_governance_enterprise_forms.py")


_enterprise_forms = _load_enterprise_forms_module()


def _load_contract_detection_module() -> Any:
    return _load_sibling_module("contract_governance_contract_detection", "contract_governance_contract_detection.py")


_contract_detection = _load_contract_detection_module()


def source_authority_contract() -> dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "legacy_industry_governance_profile": LEGACY_INDUSTRY_GOVERNANCE_SOURCE_KIND,
        "legacy_user_surface_model_policy": LEGACY_USER_SURFACE_MODEL_POLICY_SOURCE_KIND,
        "field_label_projection_only": True,
        "no_partner_classification": True,
    }


def legacy_industry_governance_source_authority_contract() -> dict[str, Any]:
    return {
        "kind": LEGACY_INDUSTRY_GOVERNANCE_SOURCE_KIND,
        "authorities": ["compatibility_governance_rules", "industry_extension_governance_profile"],
        "projection_only": True,
        "no_business_fact_authority": True,
        "legacy_compatibility": True,
    }


def legacy_user_surface_model_policy_source_authority_contract() -> dict[str, Any]:
    return {
        "kind": LEGACY_USER_SURFACE_MODEL_POLICY_SOURCE_KIND,
        "authorities": ["compatibility_ui_model_policy", "extension_governance_policy"],
        "projection_only": True,
        "no_business_fact_authority": True,
        "legacy_compatibility": True,
    }


def _mark_legacy_industry_governance_profile(data: dict, profile_key: str) -> None:
    if not isinstance(data, dict):
        return
    diagnostics = _as_dict(data.get("governance_diagnostics"))
    profiles = diagnostics.get("legacy_industry_profiles")
    if not isinstance(profiles, list):
        profiles = []
    if profile_key and profile_key not in profiles:
        profiles.append(profile_key)
    diagnostics["legacy_industry_profiles"] = profiles
    diagnostics["legacy_industry_source_authority"] = legacy_industry_governance_source_authority_contract()
    data["governance_diagnostics"] = diagnostics


def _mark_legacy_user_surface_model_policy(data: dict, policy_key: str) -> None:
    if not isinstance(data, dict):
        return
    diagnostics = _as_dict(data.get("governance_diagnostics"))
    policies = diagnostics.get("legacy_user_surface_model_policies")
    if not isinstance(policies, list):
        policies = []
    if policy_key and policy_key not in policies:
        policies.append(policy_key)
    diagnostics["legacy_user_surface_model_policies"] = policies
    diagnostics["legacy_user_surface_model_policy_source_authority"] = legacy_user_surface_model_policy_source_authority_contract()
    data["governance_diagnostics"] = diagnostics


def register_legacy_standard_list_profile(profile: dict[str, Any]) -> None:
    _registry.register_legacy_standard_list_profile(profile)


def register_legacy_record_context_clear_model(model_name: str) -> None:
    _registry.register_legacy_record_context_clear_model(model_name)


def register_legacy_delete_only_model(model_name: str) -> None:
    _registry.register_legacy_delete_only_model(model_name)


def register_legacy_project_form_governance_model(model_name: str) -> None:
    _registry.register_legacy_project_form_governance_model(model_name)


def register_legacy_project_form_profile(model_name: str, profile: dict[str, Any]) -> None:
    _registry.register_legacy_project_form_profile(
        model_name,
        profile,
        default_max_fields=_PROJECT_FORM_FIELD_MAX,
    )


def register_legacy_project_task_form_governance_model(model_name: str) -> None:
    _registry.register_legacy_project_task_form_governance_model(model_name)


def register_legacy_project_task_form_profile(model_name: str, profile: dict[str, Any]) -> None:
    _registry.register_legacy_project_task_form_profile(model_name, profile)


def register_legacy_project_kanban_governance_model(model_name: str) -> None:
    _registry.register_legacy_project_kanban_governance_model(model_name)


def register_legacy_project_kanban_profile(model_name: str, profile: dict[str, Any]) -> None:
    _registry.register_legacy_project_kanban_profile(model_name, profile)


def register_legacy_kanban_row_action(model_name: str, action: dict[str, Any]) -> None:
    _registry.register_legacy_kanban_row_action(model_name, action)


def register_legacy_field_presentation(model_name: str, field_name: str, profile: dict[str, Any]) -> None:
    _registry.register_legacy_field_presentation(model_name, field_name, profile)


def register_capability_group_profile(group_key: str, profile: dict[str, Any]) -> None:
    _registry.register_capability_group_profile(group_key, profile)


def register_scene_semantic_profile(profile: dict[str, Any]) -> None:
    _registry.register_scene_semantic_profile(profile)


def _legacy_field_presentation(model_name: str, field_name: str) -> dict[str, Any]:
    return dict(_LEGACY_FIELD_PRESENTATION_REGISTRY.get((_safe_text(model_name), _safe_text(field_name))) or {})


def _legacy_standard_list_profile_signature(data: dict) -> str:
    head = _as_dict(data.get("head"))
    context = _as_dict(data.get("context"))
    views = _as_dict(data.get("views"))
    tree_view = _as_dict(views.get("tree") or views.get("list"))
    raw_parts = [
        head.get("name"),
        data.get("name"),
        data.get("title"),
        data.get("domain"),
        data.get("domain_raw"),
        head.get("domain"),
        head.get("domain_raw"),
        context.get("default_payment_family"),
        context.get("default_source_table"),
        tree_view.get("name"),
        tree_view.get("domain"),
        tree_view.get("domain_raw"),
    ]
    return " ".join(_safe_text(part) for part in raw_parts)


def _legacy_standard_list_profile_matches(data: dict, profile: dict[str, Any]) -> bool:
    model_name = _safe_text(profile.get("model_name"))
    if not model_name or not _is_model_tree_contract(data, model_name):
        return False
    signature_any = profile.get("signature_any") if isinstance(profile.get("signature_any"), list) else []
    if not signature_any:
        return True
    signature = _legacy_standard_list_profile_signature(data)
    return any(token and token in signature for token in signature_any)


def _apply_registered_legacy_standard_list_profiles(data: dict) -> None:
    for profile in list(_LEGACY_STANDARD_LIST_PROFILE_REGISTRY):
        model_name = _safe_text(profile.get("model_name"))
        if not model_name or not _legacy_standard_list_profile_matches(data, profile):
            continue
        profile_key = _safe_text(profile.get("profile_key"))
        if profile_key:
            _mark_legacy_industry_governance_profile(data, profile_key)
        _govern_standard_list_for_user(
            data,
            model_name=model_name,
            columns_order=profile.get("columns_order") if isinstance(profile.get("columns_order"), list) else [],
            column_labels=profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {},
            row_primary=_safe_text(profile.get("row_primary")),
            row_secondary=_safe_text(profile.get("row_secondary")),
            status_field=_safe_text(profile.get("status_field")),
            strict_columns=bool(profile.get("strict_columns")),
        )


def _inject_enterprise_form_governance(data: dict, *, next_action_key: str = "", next_action_label: str = "") -> None:
    governance = _as_dict(data.get("form_governance"))
    governance.update(
        {
            "surface": "enterprise_enablement",
            "hide_workflow": True,
            "hide_search_filters": True,
            "hide_body_actions": True,
            "suppress_contract_header_actions": True,
        }
    )
    if _safe_text(next_action_key) and _safe_text(next_action_label):
        governance["next_action"] = {
            "step_key": _safe_text(next_action_key),
            "label": _safe_text(next_action_label),
        }
    else:
        governance.pop("next_action", None)
    data["form_governance"] = governance

def _governance_primary_model(data: dict) -> str:
    governance = _as_dict(data.get("governance"))
    head = _as_dict(data.get("head"))
    permissions = _as_dict(data.get("permissions"))
    return _safe_text(
        governance.get("primary_model")
        or data.get("governance_primary_model")
        or head.get("model")
        or data.get("model")
        or permissions.get("model")
    )


def is_truthy(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def resolve_contract_mode(params: dict | None) -> str:
    params = params if isinstance(params, dict) else {}
    raw_mode = str(params.get("contract_mode") or "").strip().lower()
    if raw_mode in CONTRACT_MODES:
        return raw_mode
    if is_truthy(params.get("hud")) or is_truthy(params.get("debug_hud")):
        return "hud"
    return "user"


def resolve_contract_surface(params: dict | None, contract_mode: str | None = None) -> str:
    params = params if isinstance(params, dict) else {}
    raw_surface = str(params.get("contract_surface") or params.get("surface") or "").strip().lower()
    if raw_surface in CONTRACT_SURFACES:
        return raw_surface
    mode = str(contract_mode or "").strip().lower()
    if mode == "hud":
        return "hud"
    return "user"


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _strip_user_mode_fields(obj: Any) -> Any:
    return _user_surface.strip_user_mode_fields(obj)


def _pick_fields(raw: dict, allowed_keys: tuple[str, ...] | list[str]) -> dict:
    return _user_surface.pick_fields(raw, allowed_keys)


def _sanitize_capability_for_user(item: dict) -> dict:
    return _user_surface.sanitize_capability_for_user(item)


def _sanitize_scene_for_user(item: dict) -> dict:
    return _user_surface.sanitize_scene_for_user(item)


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _safe_lower(value: Any) -> str:
    return _user_surface.safe_lower(value)


def _is_numeric_token(value: Any) -> bool:
    return _user_surface.is_numeric_token(value)


def _contains_noise_marker(*values: Any) -> bool:
    return _user_surface.contains_noise_marker(*values)


def _is_noisy_filter_row(row: dict) -> bool:
    return _user_surface.is_noisy_filter_row(row)


def _sanitize_user_search_filters(data: dict) -> None:
    _user_surface.sanitize_user_search_filters(data)


def _is_noisy_action_row(row: dict) -> bool:
    return _user_surface.is_noisy_action_row(row)


def _classify_user_surface_action_group(action: dict) -> str:
    return _user_surface.classify_user_surface_action_group(action)


def _build_user_surface_action_groups(rows: list[dict]) -> list[dict]:
    return _user_surface.build_user_surface_action_groups(rows)


def _sanitize_user_action_rows(rows: Any, max_count: int = _USER_SURFACE_ACTION_MAX) -> list[dict]:
    return _user_surface.sanitize_user_action_rows(rows, max_count=max_count)


def _apply_user_surface_noise_reduction(data: dict) -> None:
    _user_surface.apply_user_surface_noise_reduction(data)


def _apply_user_surface_policies(data: dict) -> None:
    _user_surface.apply_user_surface_policies(
        data,
        primary_model=_governance_primary_model(data),
        record_context_clear_models=LEGACY_RECORD_CONTEXT_CLEAR_MODELS,
        delete_only_models=LEGACY_DELETE_ONLY_MODELS,
        mark_model_policy=_mark_legacy_user_surface_model_policy,
        filter_max=_USER_SURFACE_FILTER_MAX,
        action_max=_USER_SURFACE_ACTION_MAX,
        primary_filter_max=_USER_SURFACE_PRIMARY_FILTER_MAX,
        primary_action_max=_USER_SURFACE_PRIMARY_ACTION_MAX,
    )


def _is_project_form_contract(data: dict) -> bool:
    return _contract_detection.is_project_form_contract(
        data,
        primary_model=_governance_primary_model(data),
        project_form_models=_LEGACY_PROJECT_FORM_GOVERNANCE_MODELS,
    )


def _legacy_project_form_profile(data: dict) -> dict[str, Any]:
    profile = _LEGACY_PROJECT_FORM_PROFILE_REGISTRY.get(_governance_primary_model(data)) or {}
    return _project_form.normalize_legacy_project_form_profile(
        profile,
        default_max_fields=_PROJECT_FORM_FIELD_MAX,
    )


def _is_enterprise_company_form_contract(data: dict) -> bool:
    return _contract_detection.is_enterprise_company_form_contract(
        data,
        primary_model=_governance_primary_model(data),
    )


def _is_enterprise_user_form_contract(data: dict) -> bool:
    return _contract_detection.is_enterprise_user_form_contract(
        data,
        primary_model=_governance_primary_model(data),
    )


def _is_project_kanban_contract(data: dict) -> bool:
    return _contract_detection.is_project_kanban_contract(
        data,
        primary_model=_governance_primary_model(data),
        project_kanban_models=_LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS,
        create_profile=_RENDER_PROFILE_CREATE,
        edit_profile=_RENDER_PROFILE_EDIT,
        readonly_profile=_RENDER_PROFILE_READONLY,
    )


def _is_project_task_form_contract(data: dict) -> bool:
    return _contract_detection.is_project_task_form_contract(
        data,
        primary_model=_governance_primary_model(data),
        task_form_models=_LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS,
    )


def _is_model_tree_contract(data: dict, model_name: str) -> bool:
    return _contract_detection.is_model_tree_contract(
        data,
        primary_model=_governance_primary_model(data),
        model_name=model_name,
    )


def _is_form_contract(data: dict) -> bool:
    return _contract_detection.is_form_contract(data)


def _is_technical_field(name: str, descriptor: dict) -> bool:
    return _field_semantics.is_technical_field(name, descriptor)


def _pick_project_form_fields(data: dict) -> list[str]:
    return _project_form.pick_project_form_fields(
        data,
        profile=_legacy_project_form_profile(data),
        iter_field_order=_iter_field_order,
        is_technical_field=_is_technical_field,
        default_max_fields=_PROJECT_FORM_FIELD_MAX,
    )


def _govern_project_kanban_contract_for_user(data: dict) -> None:
    primary_model = _governance_primary_model(data)
    _project_form.govern_project_kanban_contract(
        data,
        primary_model=primary_model,
        registered_profile=_LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY.get(primary_model) or {},
        registered_row_actions=_LEGACY_KANBAN_ROW_ACTION_REGISTRY.get(primary_model, []),
        is_technical_field=_is_technical_field,
        deep_clone_json_like=_deep_clone_json_like,
    )


def _restructure_project_form_layout(data: dict) -> None:
    if not _is_project_form_contract(data):
        return
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return
    # Keep parser-native container hierarchy intact. Downstream user governance will
    # prune fields from this tree, but it should not replace notebook/page/group with
    # synthetic buckets because frontend detail rendering depends on the native shape.
    form["layout"] = layout
    views["form"] = form
    data["views"] = views


def _filter_project_form_layout(data: dict, selected_fields: list[str]) -> None:
    _project_form.filter_project_form_layout(
        data,
        selected_fields,
        profile=_legacy_project_form_profile(data),
    )


def _trim_contract_field_maps(data: dict, selected_fields: list[str]) -> None:
    _project_form.trim_contract_field_maps(data, selected_fields)


def _govern_project_form_search(data: dict) -> None:
    _project_form.govern_project_form_search(data, profile=_legacy_project_form_profile(data))


def _action_priority(action: dict, data: dict | None = None) -> int:
    return _project_form.action_priority(action, profile=_legacy_project_form_profile(data or {}))


def _is_noisy_project_action(action: dict, data: dict | None = None) -> bool:
    return _project_form.is_noisy_project_action(action, profile=_legacy_project_form_profile(data or {}))


def _classify_project_action_group(action: dict) -> str:
    return _project_form.classify_project_action_group(action)


def _build_project_action_groups(rows: list[dict], data: dict | None = None) -> list[dict]:
    return _project_form.build_project_action_groups(
        rows,
        profile=_legacy_project_form_profile(data or {}),
        default_group_labels=_PROJECT_FORM_DEFAULT_ACTION_GROUP_LABELS,
        action_group_limit=_PROJECT_FORM_ACTION_GROUP_LIMIT,
    )


def _emit_scene_action_semantics(data: dict, *, header_rows: list[dict], record_rows: list[dict]) -> None:
    _project_form.emit_scene_action_semantics(data, header_rows=header_rows, record_rows=record_rows)


def _govern_project_form_actions(data: dict) -> None:
    _project_form.govern_project_form_actions(
        data,
        profile=_legacy_project_form_profile(data),
        default_group_labels=_PROJECT_FORM_DEFAULT_ACTION_GROUP_LABELS,
        action_group_limit=_PROJECT_FORM_ACTION_GROUP_LIMIT,
        header_action_max=_PROJECT_FORM_HEADER_ACTION_MAX,
        smart_action_max=_PROJECT_FORM_SMART_ACTION_MAX,
    )


def _build_project_lifecycle_summary(data: dict) -> None:
    _project_form.build_project_lifecycle_summary(data)


def _govern_project_form_contract_for_user(data: dict) -> None:
    selected = _pick_project_form_fields(data)
    profile = _legacy_project_form_profile(data)
    _project_form.govern_project_form_contract(
        data,
        selected_fields=selected,
        profile=profile,
        collect_layout_field_names=_collect_layout_field_names,
        backfill_form_layout_from_visible_fields=_backfill_form_layout_from_visible_fields,
        govern_project_form_search=_govern_project_form_search,
        build_project_lifecycle_summary=_build_project_lifecycle_summary,
        realign_access_policy_with_visible_fields=_realign_access_policy_with_visible_fields,
        default_max_fields=_PROJECT_FORM_FIELD_MAX,
        default_group_labels=_PROJECT_FORM_DEFAULT_ACTION_GROUP_LABELS,
        action_group_limit=_PROJECT_FORM_ACTION_GROUP_LIMIT,
        header_action_max=_PROJECT_FORM_HEADER_ACTION_MAX,
        smart_action_max=_PROJECT_FORM_SMART_ACTION_MAX,
    )


def _govern_project_task_form_for_user(data: dict) -> None:
    if not _is_project_task_form_contract(data):
        return
    primary_model = _governance_primary_model(data)
    profile = _LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY.get(primary_model) or {}
    _project_form.govern_project_task_form(
        data,
        profile=profile,
        make_labeled_field_node=_make_labeled_field_node,
    )


def _govern_standard_list_for_user(
    data: dict,
    *,
    model_name: str,
    columns_order: list[str],
    column_labels: dict[str, str],
    row_primary: str,
    row_secondary: str,
    status_field: str,
    strict_columns: bool = False,
) -> None:
    _list_surface.govern_standard_list_for_user(
        data,
        model_name=model_name,
        columns_order=columns_order,
        column_labels=column_labels,
        row_primary=row_primary,
        row_secondary=row_secondary,
        status_field=status_field,
        strict_columns=strict_columns,
        is_model_tree_contract=_is_model_tree_contract,
        legacy_field_presentation=_legacy_field_presentation,
        deep_clone_json_like=_deep_clone_json_like,
        apply_standard_search_toolbar_labels=_apply_standard_search_toolbar_labels,
    )


def _apply_standard_search_toolbar_labels(data: dict) -> None:
    _list_surface.apply_standard_search_toolbar_labels(data)


def _govern_tier_review_list_for_user(data: dict) -> None:
    _list_surface.govern_tier_review_list_for_user(
        data,
        is_model_tree_contract=_is_model_tree_contract,
        mark_legacy_industry_governance_profile=_mark_legacy_industry_governance_profile,
        nav_action_prefixes=_TIER_REVIEW_LIST_NAV_ACTION_PREFIXES,
    )


def _realign_access_policy_with_visible_fields(data: dict) -> None:
    _access_policy.realign_access_policy_with_visible_fields(data)


def _normalize_native_view_contract_surface(data: dict) -> None:
    _native_bridge.normalize_native_view_contract_surface(data)


def _normalize_scene_semantic_surface(data: dict) -> None:
    _native_bridge.normalize_scene_semantic_surface(data)


def _search_surface_from_contract(data: dict) -> dict:
    return _native_bridge.search_surface_from_contract(data)


def _scene_actions_from_contract(data: dict) -> dict:
    return _native_bridge.scene_actions_from_contract(data)


def _ensure_scene_contract_v1_envelope(data: dict) -> None:
    _native_bridge.ensure_scene_contract_v1_envelope(data)


def _business_field_label(field_name: str, current_label: Any = "", model_name: str = "") -> str:
    return _labels.business_field_label(field_name, current_label, model_name)


def _normalize_business_field_labels(data: dict) -> None:
    _labels.normalize_business_field_labels(data)


def _native_node_label(node: dict) -> str:
    return _labels.native_node_label(node)


def _preserve_native_layout_labels(data: dict) -> None:
    _labels.preserve_native_layout_labels(data)


def _emit_relation_entry_semantics(data: dict) -> None:
    _labels.emit_relation_entry_semantics(data)


def _to_bool(value: Any, fallback: bool = False) -> bool:
    return _form_render.to_bool(value, fallback=fallback)


def _resolve_render_profile(data: dict) -> str:
    return _form_render.resolve_render_profile(data)


def _apply_form_view_capabilities(data: dict) -> None:
    _form_render.apply_form_view_capabilities(data)


def _iter_field_order(data: dict) -> list[str]:
    return _form_fields.iter_field_order(data)


def _derive_form_core_fields(data: dict) -> list[str]:
    return _form_fields.derive_form_core_fields(
        data,
        is_project_form=_is_project_form_contract(data),
        project_form_profile=_legacy_project_form_profile(data),
        is_technical_field=_is_technical_field,
        to_bool=lambda value: _to_bool(value, fallback=False),
    )


def _apply_form_field_groups(data: dict) -> None:
    _form_fields.apply_form_field_groups(
        data,
        is_form_contract=_is_form_contract,
        is_project_form=_is_project_form_contract(data),
        project_form_profile=_legacy_project_form_profile(data),
        is_enterprise_company_form=_is_enterprise_company_form_contract(data),
        is_enterprise_user_form=_is_enterprise_user_form_contract(data),
        is_technical_field=_is_technical_field,
        to_bool=lambda value: _to_bool(value, fallback=False),
    )


def _collect_layout_field_names(nodes: Any) -> list[str]:
    return _form_layout.collect_layout_field_names(nodes)


def _find_layout_sheet_node(nodes: Any) -> dict | None:
    return _form_layout.find_layout_sheet_node(nodes)


def _backfill_form_layout_from_visible_fields(data: dict) -> None:
    _form_layout.backfill_form_layout_from_visible_fields(
        data,
        is_form_contract=_is_form_contract,
        is_technical_field=_is_technical_field,
    )


def _make_labeled_field_node(
    name: str,
    fields_map: dict[str, Any],
    preferred_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _form_layout.make_labeled_field_node(name, fields_map, preferred_labels)


def _infer_action_semantic(action: dict) -> str:
    return _form_actions.infer_action_semantic(action)


def _infer_visible_profiles(action: dict) -> list[str]:
    return _form_actions.infer_visible_profiles(action)


def _annotate_form_actions(data: dict) -> None:
    _form_actions.annotate_form_actions(data, is_form_contract=_is_form_contract)


def _apply_form_render_semantics(data: dict, contract_mode: str) -> None:
    if not _is_form_contract(data):
        return
    _apply_form_view_capabilities(data)
    data["render_profile"] = _resolve_render_profile(data)
    rights = _as_dict(_as_dict(_as_dict(data.get("permissions")).get("effective")).get("rights"))
    if not _to_bool(rights.get("write"), fallback=False) and not _to_bool(rights.get("create"), fallback=False):
        data["render_profile"] = _RENDER_PROFILE_READONLY
    data["hide_filters_on_create"] = True
    _apply_form_field_groups(data)
    _annotate_form_actions(data)
    _apply_form_policy_contract(data, contract_mode)


def _resolve_contract_required_fields(data: dict, fields_map: dict[str, Any]) -> list[str]:
    return _form_fields.resolve_contract_required_fields(
        data,
        fields_map,
        is_project_form=_is_project_form_contract(data),
        to_bool=lambda value: _to_bool(value, fallback=False),
    )


def _build_form_field_policies(data: dict) -> dict[str, dict[str, Any]]:
    fields_map = _as_dict(data.get("fields"))
    return _form_fields.build_form_field_policies(
        data,
        contract_required_fields=_resolve_contract_required_fields(data, fields_map),
        is_project_form=_is_project_form_contract(data),
        project_form_profile=_legacy_project_form_profile(data),
        to_bool=lambda value: _to_bool(value, fallback=False),
    )


def _default_action_policy(semantic: str, visible_profiles: list[str], required_fields: list[str]) -> dict[str, Any]:
    return _form_actions.default_action_policy(semantic, visible_profiles, required_fields)


def _resolve_form_scene_profile(data: dict) -> str:
    return _FORM_SCENE_PROFILE_PROJECT if _is_project_form_contract(data) else _FORM_SCENE_PROFILE_DEFAULT


def _resolve_action_policy_template_keys(
    *,
    scene_profile: str,
    semantic: str,
    required_capabilities: list[str],
    required_groups: list[str],
    required_roles: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
) -> list[str]:
    return _form_actions.resolve_action_policy_template_keys(
        scene_profile=scene_profile,
        semantic=semantic,
        required_capabilities=required_capabilities,
        required_groups=required_groups,
        required_roles=required_roles,
        lifecycle_field=lifecycle_field,
        lifecycle_blocked_states=lifecycle_blocked_states,
    )


def _apply_action_policy_templates(
    policy: dict[str, Any],
    template_keys: list[str],
    *,
    required_fields: list[str],
    required_capabilities: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
    required_groups: list[str],
    required_roles: list[str],
    fields_map: dict[str, Any],
) -> None:
    _form_actions.apply_action_policy_templates(
        policy,
        template_keys,
        required_fields=required_fields,
        required_capabilities=required_capabilities,
        lifecycle_field=lifecycle_field,
        lifecycle_blocked_states=lifecycle_blocked_states,
        required_groups=required_groups,
        required_roles=required_roles,
        fields_map=fields_map,
    )


def _merge_policy_constraints(
    policy: dict[str, Any],
    *,
    required_capabilities: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
    required_groups: list[str],
    required_roles: list[str],
) -> None:
    _form_actions.merge_policy_constraints(
        policy,
        required_capabilities=required_capabilities,
        lifecycle_field=lifecycle_field,
        lifecycle_blocked_states=lifecycle_blocked_states,
        required_groups=required_groups,
        required_roles=required_roles,
    )


def _append_primary_action_conditions(policy: dict[str, Any], fields_map: dict[str, Any]) -> None:
    _form_actions.append_primary_action_conditions(policy, fields_map)


def _build_form_action_policies(data: dict) -> dict[str, dict[str, Any]]:
    required_fields = _resolve_contract_required_fields(data, _as_dict(data.get("fields")))
    scene_profile = _resolve_form_scene_profile(data)
    return _form_actions.build_form_action_policies(
        data,
        required_fields=required_fields,
        scene_profile=scene_profile,
    )


def _govern_enterprise_company_form_for_user(data: dict) -> None:
    if not _is_enterprise_company_form_contract(data):
        return
    _enterprise_forms.govern_enterprise_company_form(
        data,
        form_fields=_ENTERPRISE_COMPANY_FORM_FIELDS,
        field_labels=_ENTERPRISE_COMPANY_FIELD_LABELS,
        make_labeled_field_node=_make_labeled_field_node,
        resolve_render_profile=_resolve_render_profile,
        render_profile_create=_RENDER_PROFILE_CREATE,
        inject_enterprise_form_governance=_inject_enterprise_form_governance,
    )


def _govern_enterprise_department_form_for_user(data: dict) -> None:
    if _governance_primary_model(data) != "hr.department":
        return
    if not _is_form_contract(data):
        return
    _enterprise_forms.govern_enterprise_department_form(
        data,
        form_fields=_ENTERPRISE_DEPARTMENT_FORM_FIELDS,
        field_labels=_ENTERPRISE_DEPARTMENT_FIELD_LABELS,
        make_labeled_field_node=_make_labeled_field_node,
        resolve_render_profile=_resolve_render_profile,
        render_profile_create=_RENDER_PROFILE_CREATE,
        inject_enterprise_form_governance=_inject_enterprise_form_governance,
    )


def _govern_enterprise_user_form_for_user(data: dict) -> None:
    if not _is_enterprise_user_form_contract(data):
        return
    _enterprise_forms.govern_enterprise_user_form(
        data,
        form_fields=_ENTERPRISE_USER_FORM_FIELDS,
        make_labeled_field_node=_make_labeled_field_node,
        resolve_contract_required_fields=_resolve_contract_required_fields,
        to_bool=_to_bool,
        render_profile_create=_RENDER_PROFILE_CREATE,
        render_profile_edit=_RENDER_PROFILE_EDIT,
        render_profile_readonly=_RENDER_PROFILE_READONLY,
        inject_enterprise_form_governance=_inject_enterprise_form_governance,
    )


def _build_form_validation_rules(data: dict, contract_mode: str) -> list[dict[str, Any]]:
    fields_map = _as_dict(data.get("fields"))
    required_fields = _resolve_contract_required_fields(data, fields_map)
    return _form_validation.build_form_validation_rules(
        data,
        contract_mode,
        required_fields=required_fields,
        to_bool=lambda value: _to_bool(value, fallback=False),
    )


def _normalize_profile_list(raw: Any, fallback: list[str] | None = None) -> list[str]:
    return _form_validation.normalize_profile_list(raw, fallback)


def _apply_business_form_policy(data: dict) -> None:
    _form_validation.apply_business_form_policy(
        data,
        to_bool=lambda value: _to_bool(value, fallback=False),
    )


def _apply_form_policy_contract(data: dict, contract_mode: str) -> None:
    data["field_policies"] = _build_form_field_policies(data)
    data["action_policies"] = _build_form_action_policies(data)
    data["validation_rules"] = _build_form_validation_rules(data, contract_mode)
    _apply_business_form_policy(data)


def _classify_field_semantic_type(name: str, descriptor: dict) -> str:
    return _field_semantics.classify_field_semantic_type(name, descriptor)


def _annotate_field_semantics(data: dict) -> None:
    _field_semantics.annotate_field_semantics(data)


def _is_create_render_profile(data: dict) -> bool:
    return _create_profile.is_create_render_profile(data)


def _mark_record_dependent_native_buttons_hidden_on_create(data: dict) -> None:
    _create_profile.mark_record_dependent_native_buttons_hidden_on_create(
        data,
        is_form_contract=_is_form_contract,
    )


def _is_create_profile_noise_field(name: str, descriptor: dict) -> bool:
    return _create_profile.is_create_profile_noise_field(name, descriptor)


def _hide_create_profile_noise_fields(data: dict) -> None:
    _create_profile.hide_create_profile_noise_fields(
        data,
        is_form_contract=_is_form_contract,
        is_enterprise_user_form_contract=_is_enterprise_user_form_contract,
    )


def _hide_create_profile_state_ribbons(data: dict) -> None:
    _create_profile.hide_create_profile_state_ribbons(
        data,
        is_form_contract=_is_form_contract,
    )


def _canonicalize_contract_keys(
    obj: Any,
    *,
    path: str = "$",
    conflicts: list[dict[str, Any]] | None = None,
) -> Any:
    return _canonicalization.canonicalize_contract_keys(obj, path=path, conflicts=conflicts)


def register_contract_domain_override(
    name: str,
    handler: Any,
    *,
    priority: int = 100,
) -> None:
    _domain_overrides.register_contract_domain_override(name, handler, priority=priority)


def _append_governance_diagnostic(data: dict, key: str, value: Any) -> None:
    _domain_overrides.append_governance_diagnostic(data, key, value)


def _apply_domain_overrides(data: dict, contract_mode: str) -> list[dict[str, Any]]:
    return _domain_overrides.apply_domain_overrides(data, contract_mode)


def apply_project_form_domain_override(data: dict, contract_mode: str) -> None:
    if contract_mode in {"user", "hud"} and _is_project_form_contract(data):
        _restructure_project_form_layout(data)
    if contract_mode == "user" and _is_project_form_contract(data):
        _govern_project_form_contract_for_user(data)
    if contract_mode == "user" and _is_project_task_form_contract(data):
        _govern_project_task_form_for_user(data)
    if contract_mode == "user":
        _apply_registered_legacy_standard_list_profiles(data)
        _govern_tier_review_list_for_user(data)
    if contract_mode == "user" and _is_enterprise_company_form_contract(data):
        _govern_enterprise_company_form_for_user(data)
    if contract_mode == "user":
        _govern_enterprise_department_form_for_user(data)
    if contract_mode == "user" and _is_enterprise_user_form_contract(data):
        _govern_enterprise_user_form_for_user(data)
    if contract_mode == "user" and _is_project_kanban_contract(data):
        _govern_project_kanban_contract_for_user(data)


def _apply_sanitize_governance(data: dict, contract_mode: str) -> None:
    if isinstance(data.get("capabilities"), list):
        capabilities = normalize_capabilities(data.get("capabilities") or [])
        if contract_mode == "user":
            capabilities = [item for item in capabilities if not is_internal_or_smoke(item)]
            capabilities = [item for item in capabilities if not _has_demo_semantics(item)]
            capabilities = [_sanitize_capability_for_user(item) for item in capabilities]
        data["capabilities"] = capabilities

    if isinstance(data.get("scenes"), list):
        scenes = normalize_scenes(data.get("scenes") or [])
        if contract_mode == "user":
            scenes = [item for item in scenes if not is_internal_or_smoke(item)]
            scenes = [item for item in scenes if not _has_demo_semantics(item)]
            scenes = [_sanitize_scene_for_user(item) for item in scenes]
            scenes = [item for item in scenes if not _has_demo_semantics(item)]
        data["scenes"] = scenes

    if contract_mode != "hud":
        for key in _NON_HUD_STRIP_KEYS:
            data.pop(key, None)
    if contract_mode == "user":
        _apply_user_surface_noise_reduction(data)
        _apply_user_surface_policies(data)


def _apply_semantic_governance(data: dict, contract_mode: str) -> None:
    if _is_form_contract(data):
        _apply_form_render_semantics(data, contract_mode)


def _deep_clone_json_like(obj: Any) -> Any:
    return _surface_mapping.deep_clone_json_like(obj)


def _collect_layout_snapshot(layout: Any) -> dict[str, Any]:
    return _surface_mapping.collect_layout_snapshot(layout)


def _collect_action_snapshot(rows: Any) -> list[str]:
    return _surface_mapping.collect_action_snapshot(rows)


def _collect_surface_snapshot(data: dict) -> dict[str, Any]:
    return _surface_mapping.collect_surface_snapshot(data)


def _build_surface_mapping(native_snapshot: dict[str, Any], governed_snapshot: dict[str, Any]) -> dict[str, Any]:
    return _surface_mapping.build_surface_mapping(native_snapshot, governed_snapshot)


def apply_contract_governance(
    data: dict | Any,
    contract_mode: str,
    *,
    contract_surface: str = "user",
    source_mode: str = "",
    inject_contract_mode: bool = True,
) -> dict | Any:
    if not isinstance(data, dict):
        return data

    pipeline = ["canonicalize", "sanitize", "semantic", "domain_overrides", "inject_mode"]
    key_conflicts: list[dict[str, Any]] = []
    data = _canonicalize_contract_keys(data, conflicts=key_conflicts)

    normalized_surface = str(contract_surface or "").strip().lower()
    if normalized_surface not in CONTRACT_SURFACES:
        normalized_surface = "hud" if contract_mode == "hud" else "user"

    native_snapshot = _collect_surface_snapshot(_deep_clone_json_like(data))

    nested_payload = data.get("data")
    if isinstance(nested_payload, dict):
        data["data"] = apply_contract_governance(
            nested_payload,
            contract_mode,
            contract_surface=normalized_surface,
            source_mode=source_mode,
            inject_contract_mode=False,
        )

    _normalize_native_view_contract_surface(data)
    _normalize_scene_semantic_surface(data)

    effective_mode = contract_mode
    if normalized_surface == "native":
        # Native surface keeps parser-origin structure and skips user/hud policy transforms.
        effective_mode = "hud"

    if normalized_surface != "native":
        _apply_sanitize_governance(data, effective_mode)
        _apply_semantic_governance(data, effective_mode)
        override_failures = _apply_domain_overrides(data, effective_mode)
        _preserve_native_layout_labels(data)
        _emit_relation_entry_semantics(data)
        _normalize_business_field_labels(data)
        _ensure_scene_contract_v1_envelope(data)
    else:
        override_failures = []
    _annotate_field_semantics(data)
    _hide_create_profile_noise_fields(data)
    _hide_create_profile_state_ribbons(data)
    _mark_record_dependent_native_buttons_hidden_on_create(data)
    if _is_form_contract(data):
        _apply_form_policy_contract(data, effective_mode)

    governed_snapshot = _collect_surface_snapshot(data)
    surface_mapping = _build_surface_mapping(native_snapshot, governed_snapshot)

    if inject_contract_mode:
        data["contract_mode"] = contract_mode
    data["contract_surface"] = normalized_surface
    data["render_mode"] = "native" if normalized_surface == "native" else "governed"
    data["source_mode"] = _safe_text(
        source_mode,
        "native_parser" if normalized_surface == "native" else "governance_pipeline",
    )
    data["governed_from_native"] = normalized_surface != "native"
    data["surface_mapping"] = surface_mapping
    if contract_mode == "hud":
        if key_conflicts:
            _append_governance_diagnostic(data, "contract_key_conflicts", key_conflicts)
        if override_failures:
            _append_governance_diagnostic(data, "domain_override_failures", override_failures)
        _append_governance_diagnostic(data, "governance_pipeline", pipeline)
    return data
