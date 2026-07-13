# -*- coding: utf-8 -*-
from __future__ import annotations

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


def _load_registry_module() -> Any:
    try:
        from . import contract_governance_registry as registry

        return registry
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_registry",
            Path(__file__).with_name("contract_governance_registry.py"),
        )
        if spec is None or spec.loader is None:
            raise
        registry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(registry)
        return registry


_registry = _load_registry_module()
globals().update({name: getattr(_registry, name) for name in _REGISTRY_EXPORTS})
# Compatibility marker for source-level authority guards:
# NO_BUSINESS_FACT_AUTHORITY = True is defined in contract_governance_registry.py.


def _load_user_surface_module() -> Any:
    try:
        from . import contract_governance_user_surface as user_surface

        return user_surface
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_user_surface",
            Path(__file__).with_name("contract_governance_user_surface.py"),
        )
        if spec is None or spec.loader is None:
            raise
        user_surface = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_surface)
        return user_surface


_user_surface = _load_user_surface_module()


def _load_capabilities_module() -> Any:
    try:
        from . import contract_governance_capabilities as capabilities

        return capabilities
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_capabilities",
            Path(__file__).with_name("contract_governance_capabilities.py"),
        )
        if spec is None or spec.loader is None:
            raise
        capabilities = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(capabilities)
        return capabilities


_capabilities = _load_capabilities_module()
_capabilities._CAPABILITY_GROUP_DEFAULTS = _CAPABILITY_GROUP_DEFAULTS
_capabilities._CAPABILITY_GROUP_PROFILE_REGISTRY = _CAPABILITY_GROUP_PROFILE_REGISTRY
_has_demo_semantics = _capabilities._has_demo_semantics
_normalized_tags_for_item = _capabilities._normalized_tags_for_item
is_internal_or_smoke = _capabilities.is_internal_or_smoke


def normalize_capabilities(capabilities: list) -> list[dict]:
    return _capabilities.normalize_capabilities(capabilities)


def _load_scenes_module() -> Any:
    try:
        from . import contract_governance_scenes as scenes

        return scenes
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_scenes",
            Path(__file__).with_name("contract_governance_scenes.py"),
        )
        if spec is None or spec.loader is None:
            raise
        scenes = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scenes)
        return scenes


_scenes = _load_scenes_module()
_scenes._SCENE_SEMANTIC_PROFILE_REGISTRY = _SCENE_SEMANTIC_PROFILE_REGISTRY
_normalize_scene_list_profile = _scenes._normalize_scene_list_profile
_derive_scene_meta = _scenes._derive_scene_meta


def normalize_scenes(scenes: list) -> list[dict]:
    return _scenes.normalize_scenes(scenes)


def _load_list_surface_module() -> Any:
    try:
        from . import contract_governance_list_surface as list_surface

        return list_surface
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_list_surface",
            Path(__file__).with_name("contract_governance_list_surface.py"),
        )
        if spec is None or spec.loader is None:
            raise
        list_surface = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(list_surface)
        return list_surface


_list_surface = _load_list_surface_module()


def _load_native_bridge_module() -> Any:
    try:
        from . import contract_governance_native_bridge as native_bridge

        return native_bridge
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_native_bridge",
            Path(__file__).with_name("contract_governance_native_bridge.py"),
        )
        if spec is None or spec.loader is None:
            raise
        native_bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native_bridge)
        return native_bridge


_native_bridge = _load_native_bridge_module()
_native_bridge._USER_SURFACE_ACTION_MAX = _USER_SURFACE_ACTION_MAX


def _load_labels_module() -> Any:
    try:
        from . import contract_governance_labels as labels

        return labels
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_labels",
            Path(__file__).with_name("contract_governance_labels.py"),
        )
        if spec is None or spec.loader is None:
            raise
        labels = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(labels)
        return labels


_labels = _load_labels_module()
_labels._BUSINESS_FIELD_LABEL_OVERRIDES = _BUSINESS_FIELD_LABEL_OVERRIDES
_labels._LEGACY_FIELD_PRESENTATION_REGISTRY = _LEGACY_FIELD_PRESENTATION_REGISTRY


def _load_access_policy_module() -> Any:
    try:
        from . import contract_governance_access_policy as access_policy

        return access_policy
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_access_policy",
            Path(__file__).with_name("contract_governance_access_policy.py"),
        )
        if spec is None or spec.loader is None:
            raise
        access_policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(access_policy)
        return access_policy


_access_policy = _load_access_policy_module()


def _load_canonicalization_module() -> Any:
    try:
        from . import contract_governance_canonicalization as canonicalization

        return canonicalization
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_canonicalization",
            Path(__file__).with_name("contract_governance_canonicalization.py"),
        )
        if spec is None or spec.loader is None:
            raise
        canonicalization = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(canonicalization)
        return canonicalization


_canonicalization = _load_canonicalization_module()
_canonicalization._CONTRACT_KEY_CANONICAL_MAP = _CONTRACT_KEY_CANONICAL_MAP


def _load_surface_mapping_module() -> Any:
    try:
        from . import contract_governance_surface_mapping as surface_mapping

        return surface_mapping
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_surface_mapping",
            Path(__file__).with_name("contract_governance_surface_mapping.py"),
        )
        if spec is None or spec.loader is None:
            raise
        surface_mapping = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(surface_mapping)
        return surface_mapping


_surface_mapping = _load_surface_mapping_module()


def _load_create_profile_module() -> Any:
    try:
        from . import contract_governance_create_profile as create_profile

        return create_profile
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_create_profile",
            Path(__file__).with_name("contract_governance_create_profile.py"),
        )
        if spec is None or spec.loader is None:
            raise
        create_profile = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(create_profile)
        return create_profile


_create_profile = _load_create_profile_module()
_create_profile._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE


def _load_field_semantics_module() -> Any:
    try:
        from . import contract_governance_field_semantics as field_semantics

        return field_semantics
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_field_semantics",
            Path(__file__).with_name("contract_governance_field_semantics.py"),
        )
        if spec is None or spec.loader is None:
            raise
        field_semantics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(field_semantics)
        return field_semantics


_field_semantics = _load_field_semantics_module()
_field_semantics._PROJECT_FORM_PAGE_PRESERVE_FIELDS = _PROJECT_FORM_PAGE_PRESERVE_FIELDS
_field_semantics._BUSINESS_DETAIL_RELATION_FIELDS = _BUSINESS_DETAIL_RELATION_FIELDS
_field_semantics._TECHNICAL_RELATION_FIELD_PREFIXES = _TECHNICAL_RELATION_FIELD_PREFIXES
_field_semantics._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_field_semantics._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_field_semantics._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY


def _load_form_layout_module() -> Any:
    try:
        from . import contract_governance_form_layout as form_layout

        return form_layout
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_form_layout",
            Path(__file__).with_name("contract_governance_form_layout.py"),
        )
        if spec is None or spec.loader is None:
            raise
        form_layout = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(form_layout)
        return form_layout


_form_layout = _load_form_layout_module()
_form_layout._ENTERPRISE_COMPANY_FIELD_LABELS = _ENTERPRISE_COMPANY_FIELD_LABELS
_form_layout._ENTERPRISE_USER_FIELD_LABELS = _ENTERPRISE_USER_FIELD_LABELS


def _load_form_actions_module() -> Any:
    try:
        from . import contract_governance_form_actions as form_actions

        return form_actions
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_form_actions",
            Path(__file__).with_name("contract_governance_form_actions.py"),
        )
        if spec is None or spec.loader is None:
            raise
        form_actions = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(form_actions)
        return form_actions


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
    try:
        from . import contract_governance_form_render as form_render

        return form_render
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_form_render",
            Path(__file__).with_name("contract_governance_form_render.py"),
        )
        if spec is None or spec.loader is None:
            raise
        form_render = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(form_render)
        return form_render


_form_render = _load_form_render_module()
_form_render._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_render._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_render._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY
_form_render._RENDER_PROFILES = _RENDER_PROFILES


def _load_form_validation_module() -> Any:
    try:
        from . import contract_governance_form_validation as form_validation

        return form_validation
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_form_validation",
            Path(__file__).with_name("contract_governance_form_validation.py"),
        )
        if spec is None or spec.loader is None:
            raise
        form_validation = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(form_validation)
        return form_validation


_form_validation = _load_form_validation_module()
_form_validation._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_validation._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_validation._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY
_form_validation._RENDER_PROFILES = _RENDER_PROFILES


def _load_form_fields_module() -> Any:
    try:
        from . import contract_governance_form_fields as form_fields

        return form_fields
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_form_fields",
            Path(__file__).with_name("contract_governance_form_fields.py"),
        )
        if spec is None or spec.loader is None:
            raise
        form_fields = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(form_fields)
        return form_fields


_form_fields = _load_form_fields_module()
_form_fields._BUSINESS_DETAIL_RELATION_FIELDS = _BUSINESS_DETAIL_RELATION_FIELDS
_form_fields._FORM_CORE_FIELD_MAX = _FORM_CORE_FIELD_MAX
_form_fields._RENDER_PROFILE_CREATE = _RENDER_PROFILE_CREATE
_form_fields._RENDER_PROFILE_EDIT = _RENDER_PROFILE_EDIT
_form_fields._RENDER_PROFILE_READONLY = _RENDER_PROFILE_READONLY


def _load_project_form_module() -> Any:
    try:
        from . import contract_governance_project_form as project_form

        return project_form
    except ImportError:
        spec = importlib.util.spec_from_file_location(
            "contract_governance_project_form",
            Path(__file__).with_name("contract_governance_project_form.py"),
        )
        if spec is None or spec.loader is None:
            raise
        project_form = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(project_form)
        return project_form


_project_form = _load_project_form_module()


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
    if not isinstance(profile, dict):
        return
    model_name = _safe_text(profile.get("model_name"))
    if not model_name:
        return
    normalized = {
        "model_name": model_name,
        "columns_order": [
            _safe_text(name)
            for name in (profile.get("columns_order") if isinstance(profile.get("columns_order"), list) else [])
            if _safe_text(name)
        ],
        "column_labels": {
            _safe_text(key): _safe_text(value)
            for key, value in (profile.get("column_labels") if isinstance(profile.get("column_labels"), dict) else {}).items()
            if _safe_text(key)
        },
        "row_primary": _safe_text(profile.get("row_primary")),
        "row_secondary": _safe_text(profile.get("row_secondary")),
        "status_field": _safe_text(profile.get("status_field")),
        "strict_columns": bool(profile.get("strict_columns")),
        "profile_key": _safe_text(profile.get("profile_key")),
        "signature_any": [
            _safe_text(item)
            for item in (profile.get("signature_any") if isinstance(profile.get("signature_any"), list) else [])
            if _safe_text(item)
        ],
    }
    if not normalized["columns_order"]:
        return
    dedupe_key = normalized["profile_key"] or normalized["model_name"]
    for index, existing in enumerate(_LEGACY_STANDARD_LIST_PROFILE_REGISTRY):
        existing_key = _safe_text(existing.get("profile_key")) or _safe_text(existing.get("model_name"))
        if existing_key == dedupe_key:
            _LEGACY_STANDARD_LIST_PROFILE_REGISTRY[index] = normalized
            return
    _LEGACY_STANDARD_LIST_PROFILE_REGISTRY.append(normalized)


def register_legacy_record_context_clear_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        LEGACY_RECORD_CONTEXT_CLEAR_MODELS.add(model)


def register_legacy_delete_only_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        LEGACY_DELETE_ONLY_MODELS.add(model)


def register_legacy_project_form_governance_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        _LEGACY_PROJECT_FORM_GOVERNANCE_MODELS.add(model)


def register_legacy_project_form_profile(model_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(profile, dict):
        return
    primary_fields = [_safe_text(name) for name in (profile.get("primary_fields") or []) if _safe_text(name)]
    create_hidden_fields = [
        _safe_text(name)
        for name in (profile.get("create_hidden_fields") or [])
        if _safe_text(name)
    ]
    action_priorities = [
        _safe_text(name)
        for name in (profile.get("action_priorities") or [])
        if _safe_text(name)
    ]
    action_noise_markers = [
        _safe_lower(name)
        for name in (profile.get("action_noise_markers") or [])
        if _safe_text(name)
    ]
    search_noise_markers = [
        _safe_lower(name)
        for name in (profile.get("search_noise_markers") or [])
        if _safe_text(name)
    ]
    action_group_labels = {
        _safe_text(key): _safe_text(value)
        for key, value in _as_dict(profile.get("action_group_labels")).items()
        if _safe_text(key) and _safe_text(value)
    }
    _LEGACY_PROJECT_FORM_PROFILE_REGISTRY[model] = {
        "primary_fields": primary_fields,
        "create_hidden_fields": create_hidden_fields,
        "action_priorities": action_priorities,
        "action_noise_markers": action_noise_markers,
        "search_noise_markers": search_noise_markers,
        "action_group_labels": action_group_labels,
        "max_fields": int(profile.get("max_fields") or _PROJECT_FORM_FIELD_MAX),
    }


def register_legacy_project_task_form_governance_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        _LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS.add(model)


def register_legacy_project_task_form_profile(model_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(profile, dict):
        return
    fields = [_safe_text(name) for name in (profile.get("fields") or []) if _safe_text(name)]
    if not fields:
        return
    labels = {
        _safe_text(key): _safe_text(value)
        for key, value in _as_dict(profile.get("field_labels")).items()
        if _safe_text(key) and _safe_text(value)
    }
    description_fields = [
        _safe_text(name)
        for name in (profile.get("description_fields") or [])
        if _safe_text(name)
    ]
    _LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY[model] = {
        "fields": fields,
        "field_labels": labels,
        "core_group_label": _safe_text(profile.get("core_group_label")) or "基础信息",
        "description_group_label": _safe_text(profile.get("description_group_label")) or "说明",
        "description_fields": description_fields,
    }


def register_legacy_project_kanban_governance_model(model_name: str) -> None:
    model = _safe_text(model_name)
    if model:
        _LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS.add(model)


def register_legacy_project_kanban_profile(model_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(profile, dict):
        return

    def _field_list(key: str) -> list[str]:
        return [_safe_text(name) for name in (profile.get(key) or []) if _safe_text(name)]

    _LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY[model] = {
        "primary_fields": _field_list("primary_fields"),
        "secondary_fields": _field_list("secondary_fields"),
        "status_fields": _field_list("status_fields"),
        "title_field": _safe_text(profile.get("title_field")),
        "max_meta": int(profile.get("max_meta") or 4),
    }


def register_legacy_kanban_row_action(model_name: str, action: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    if not model or not isinstance(action, dict):
        return
    key = _safe_text(action.get("key") or action.get("name"))
    if not key:
        return
    row = _deep_clone_json_like(action)
    row["key"] = key
    row.setdefault("name", key)
    _LEGACY_KANBAN_ROW_ACTION_REGISTRY.setdefault(model, [])
    existing = _LEGACY_KANBAN_ROW_ACTION_REGISTRY[model]
    existing[:] = [item for item in existing if _safe_text(item.get("key") or item.get("name")) != key]
    existing.append(row)


def register_legacy_field_presentation(model_name: str, field_name: str, profile: dict[str, Any]) -> None:
    model = _safe_text(model_name)
    field = _safe_text(field_name)
    if not model or not field or not isinstance(profile, dict):
        return
    normalized = {
        "label": _safe_text(profile.get("label")),
        "widget": _safe_text(profile.get("widget")),
        "cell_role": _safe_text(profile.get("cell_role")),
        "mutation": _deep_clone_json_like(profile.get("mutation")) if isinstance(profile.get("mutation"), dict) else {},
    }
    _LEGACY_FIELD_PRESENTATION_REGISTRY[(model, field)] = normalized


def register_capability_group_profile(group_key: str, profile: dict[str, Any]) -> None:
    key = _safe_text(group_key)
    if not key or not isinstance(profile, dict):
        return
    _CAPABILITY_GROUP_PROFILE_REGISTRY[key] = {
        "label": _safe_text(profile.get("label"), key),
        "icon": _safe_text(profile.get("icon")),
        "key_prefixes": tuple(
            _safe_lower(item)
            for item in (profile.get("key_prefixes") if isinstance(profile.get("key_prefixes"), list) else [])
            if _safe_text(item)
        ),
    }


def register_scene_semantic_profile(profile: dict[str, Any]) -> None:
    if not isinstance(profile, dict):
        return
    purpose = _safe_text(profile.get("purpose"))
    if not purpose:
        return
    normalized = {
        "purpose": purpose,
        "code_prefixes": tuple(
            _safe_lower(item)
            for item in (profile.get("code_prefixes") if isinstance(profile.get("code_prefixes"), list) else [])
            if _safe_text(item)
        ),
        "code_contains": tuple(
            _safe_lower(item)
            for item in (profile.get("code_contains") if isinstance(profile.get("code_contains"), list) else [])
            if _safe_text(item)
        ),
    }
    if not normalized["code_prefixes"] and not normalized["code_contains"]:
        return
    _SCENE_SEMANTIC_PROFILE_REGISTRY.append(normalized)


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
_DOMAIN_OVERRIDE_REGISTRY: list[dict[str, Any]] = []


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


def _parse_tags(raw: Any) -> set[str]:
    if isinstance(raw, list):
        items = raw
    else:
        items = str(raw or "").split(",")
    out: set[str] = set()
    for item in items:
        val = _safe_text(item).lower()
        if val:
            out.add(val)
    return out


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


def _view_type_tokens(*values: Any) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for item in _safe_lower(value).replace(";", ",").split(","):
            token = item.strip()
            if token:
                tokens.add(token)
    return tokens


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
    head = _as_dict(data.get("head"))
    view_types = _view_type_tokens(head.get("view_type"), data.get("view_type"))
    model = _safe_text(head.get("model") or data.get("model"))
    fields_map = _as_dict(data.get("fields"))
    views = _as_dict(data.get("views"))
    has_list_view = bool(_as_dict(views.get("tree") or views.get("list")))
    active_field = "active" if "active" in fields_map else ""
    filters_primary_max = _USER_SURFACE_PRIMARY_FILTER_MAX
    actions_primary_max = _USER_SURFACE_PRIMARY_ACTION_MAX
    record_open_policy = {
        "carry_query_mode": "preserve",
    }
    batch_policy = {
        "enabled": False,
        "active_field": "",
        "archive_value": None,
        "activate_value": None,
        "delete_allowed": False,
        "delete_only_mode": False,
        "delete_mode": "none",
        "available_actions": [],
    }
    if "form" in view_types and not (view_types & {"tree", "list"} or has_list_view):
        filters_primary_max = 0
        actions_primary_max = 3
    if view_types & {"tree", "list"} or has_list_view:
        permissions = _as_dict(data.get("permissions"))
        effective = _as_dict(permissions.get("effective"))
        rights = _as_dict(effective.get("rights"))
        write_allowed = bool(rights.get("write"))
        unlink_right_allowed = bool(rights.get("unlink"))
        delete_policy = _as_dict(data.get("delete_policy"))
        unlink_allowed = bool(delete_policy.get("allowed")) and _safe_lower(delete_policy.get("delete_mode")) == "unlink"
        if model in LEGACY_RECORD_CONTEXT_CLEAR_MODELS:
            _mark_legacy_user_surface_model_policy(data, f"{model}.record_open_context")
        if model in LEGACY_DELETE_ONLY_MODELS:
            _mark_legacy_user_surface_model_policy(data, f"{model}.delete_only")
        delete_allowed = bool(unlink_right_allowed and unlink_allowed)
        delete_only_mode = bool(delete_allowed and model in LEGACY_DELETE_ONLY_MODELS)
        available_actions = []
        if write_allowed and active_field and not delete_only_mode:
            available_actions.extend(["archive", "activate"])
        if delete_allowed:
            available_actions.append("delete")
        if model in LEGACY_RECORD_CONTEXT_CLEAR_MODELS:
            record_open_policy = {
                "carry_query_mode": "clear_scene_context",
            }
        batch_policy = {
            "enabled": bool(available_actions),
            "active_field": active_field,
            "archive_value": False if active_field else None,
            "activate_value": True if active_field else None,
            "delete_allowed": delete_allowed,
            "delete_only_mode": delete_only_mode,
            "delete_mode": "unlink" if delete_allowed and "delete" in available_actions else "none",
            "available_actions": available_actions,
        }
        if not write_allowed and not unlink_right_allowed:
            batch_policy["available_actions"] = []
            batch_policy["enabled"] = False
            batch_policy["delete_mode"] = "none"
    primary_model = _governance_primary_model(data)
    if model and primary_model and model == primary_model:
        filters_primary_max = min(filters_primary_max, 4)
        actions_primary_max = min(actions_primary_max, 3)
    data["surface_policies"] = {
        "filters_primary_max": filters_primary_max,
        "actions_primary_max": actions_primary_max,
        "filters_max": _USER_SURFACE_FILTER_MAX,
        "actions_max": _USER_SURFACE_ACTION_MAX,
        "delete_mode": batch_policy.get("delete_mode") or "none",
        "batch_policy": batch_policy,
        "record_open_policy": record_open_policy,
    }


def _is_project_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    has_form_view = isinstance(views.get("form"), dict)
    if not view_type and has_form_view:
        view_type = "form"
    primary_model = _governance_primary_model(data)
    if primary_model not in _LEGACY_PROJECT_FORM_GOVERNANCE_MODELS:
        return False
    if not primary_model or model != primary_model:
        return False
    if has_form_view:
        return "form" in view_type if view_type else True
    return view_type == "form"


def _legacy_project_form_profile(data: dict) -> dict[str, Any]:
    profile = _LEGACY_PROJECT_FORM_PROFILE_REGISTRY.get(_governance_primary_model(data)) or {}
    return _project_form.normalize_legacy_project_form_profile(
        profile,
        default_max_fields=_PROJECT_FORM_FIELD_MAX,
    )


def _is_enterprise_company_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    primary_model = _governance_primary_model(data)
    return bool(primary_model == "res.company" and model == "res.company" and "form" in view_type)


def _is_enterprise_user_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    primary_model = _governance_primary_model(data)
    return bool(primary_model == "res.users" and model == "res.users" and "form" in view_type)


def _is_project_kanban_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    kanban_view = _as_dict(views.get("kanban"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or kanban_view.get("model")
        or permissions.get("model")
    )
    current_view_type = _safe_text(data.get("view_type")).lower()
    if current_view_type and current_view_type not in {"kanban", "tree", "list"}:
        return False
    render_profile = _safe_text(data.get("render_profile")).lower()
    if render_profile in {_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY}:
        return False
    if _safe_text(data.get("record_id") or data.get("res_id")) and isinstance(views.get("form"), dict):
        return False
    view_type = _safe_text(current_view_type or head.get("view_type")).lower()
    if not view_type and isinstance(views.get("kanban"), dict):
        view_type = "kanban"
    primary_model = _governance_primary_model(data)
    return bool(
        primary_model
        and primary_model in _LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS
        and model == primary_model
        and ("kanban" in view_type or isinstance(views.get("kanban"), dict))
    )


def _is_project_task_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    form_view = _as_dict(views.get("form"))
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or form_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and isinstance(views.get("form"), dict):
        view_type = "form"
    primary_model = _governance_primary_model(data)
    return bool(
        primary_model
        and primary_model in _LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS
        and model == primary_model
        and "form" in view_type
    )


def _is_model_tree_contract(data: dict, model_name: str) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    tree_view = _as_dict(views.get("tree") or views.get("list"))
    has_tree_surface = bool(tree_view)
    permissions = _as_dict(data.get("permissions"))
    model = _safe_text(
        head.get("model")
        or data.get("model")
        or tree_view.get("model")
        or permissions.get("model")
    )
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if not view_type and has_tree_surface:
        view_type = "tree"
    primary_model = _governance_primary_model(data)
    return bool(
        primary_model == model_name
        and model == model_name
        and ("tree" in view_type or "list" in view_type or has_tree_surface)
    )


def _is_form_contract(data: dict) -> bool:
    head = _as_dict(data.get("head"))
    views = _as_dict(data.get("views"))
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if view_type == "form":
        return True
    return isinstance(views.get("form"), dict)


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
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    primary_model = _governance_primary_model(data)
    registered_profile = _LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY.get(primary_model) or {}

    available = [name for name in fields_map.keys() if not _is_technical_field(name, _as_dict(fields_map.get(name)))]
    primary: list[str] = []
    secondary: list[str] = []
    status: list[str] = []

    def _pick(target: list[str], name: str) -> None:
        if name in available and name not in target:
            target.append(name)

    for name in registered_profile.get("primary_fields") or []:
        _pick(primary, name)
    for name in registered_profile.get("secondary_fields") or []:
        _pick(secondary, name)
    for name in registered_profile.get("status_fields") or []:
        _pick(status, name)

    if not primary:
        for fallback in ("name", "display_name"):
            _pick(primary, fallback)
            if primary:
                break
    if len(primary) < 3:
        for name in available:
            _pick(primary, name)
            if len(primary) >= 3:
                break
    if len(secondary) < 4:
        for name in available:
            if name in primary:
                continue
            _pick(secondary, name)
            if len(secondary) >= 4:
                break
    if not status:
        for name in ("lifecycle_state", "stage_id", "state"):
            _pick(status, name)
            if status:
                break

    selected = [name for name in primary + secondary if name]
    selected = selected[:8]
    data["visible_fields"] = selected
    configured_title_field = _safe_text(registered_profile.get("title_field"))
    default_profile = {
        "title_field": configured_title_field if configured_title_field in fields_map else (primary[0] if primary else "name"),
        "primary_fields": primary[:3],
        "secondary_fields": secondary[:4],
        "status_fields": status[:2],
        "max_meta": int(registered_profile.get("max_meta") or 4),
    }

    views = _as_dict(data.get("views"))
    kanban = _as_dict(views.get("kanban"))
    existing = kanban.get("fields") if isinstance(kanban.get("fields"), list) else []
    merged_fields: list[Any] = []
    merged_names: set[str] = set()
    orchestrated_names: list[str] = []

    def _field_row_name(row: Any) -> str:
        if isinstance(row, dict):
            return _safe_text(row.get("name") or row.get("field") or row.get("field_name"))
        return _safe_text(row)

    for row in existing:
        normalized = _field_row_name(row)
        descriptor = _as_dict(fields_map.get(normalized))
        if (
            normalized
            and normalized in fields_map
            and not _is_technical_field(normalized, descriptor)
            and normalized not in merged_names
        ):
            merged_fields.append(dict(row) if isinstance(row, dict) else normalized)
            merged_names.add(normalized)
            orchestrated_names.append(normalized)
    for name in selected:
        normalized = _safe_text(name)
        descriptor = _as_dict(fields_map.get(normalized))
        if (
            normalized
            and normalized in fields_map
            and not _is_technical_field(normalized, descriptor)
            and normalized not in merged_names
        ):
            merged_fields.append(normalized)
            merged_names.add(normalized)
    kanban["fields"] = merged_fields or ["id", "name"]

    existing_profile = _as_dict(kanban.get("kanban_profile") or data.get("kanban_profile"))
    slots = _as_dict(kanban.get("slots"))

    def _slot_names(key: str) -> list[str]:
        raw = slots.get(key)
        if not isinstance(raw, list):
            return []
        out: list[str] = []
        for item in raw:
            name = _field_row_name(item)
            if name and name in fields_map and name not in out:
                out.append(name)
        return out

    primary_override = _slot_names("primary")
    secondary_override = _slot_names("secondary")
    status_override = _slot_names("status")
    has_orchestrated_kanban = bool(orchestrated_names or primary_override or secondary_override or status_override)
    profile = dict(default_profile)
    profile.update(existing_profile)
    if has_orchestrated_kanban:
        if primary_override:
            profile["primary_fields"] = primary_override
        elif orchestrated_names:
            profile["primary_fields"] = orchestrated_names[:3]
        if secondary_override:
            profile["secondary_fields"] = secondary_override
        elif orchestrated_names:
            profile["secondary_fields"] = orchestrated_names[3:7]
        if status_override:
            profile["status_fields"] = status_override[:2]
        if not _safe_text(profile.get("title_field")):
            profile["title_field"] = "name" if "name" in fields_map else (orchestrated_names[0] if orchestrated_names else default_profile["title_field"])
    data["kanban_profile"] = profile
    kanban["kanban_profile"] = dict(profile)
    row_actions = kanban.get("row_actions") if isinstance(kanban.get("row_actions"), list) else []
    existing_keys = {
        _safe_text(row.get("key") or row.get("name"))
        for row in row_actions
        if isinstance(row, dict)
    }
    for action in _LEGACY_KANBAN_ROW_ACTION_REGISTRY.get(primary_model, []):
        action_key = _safe_text(action.get("key") or action.get("name"))
        if not action_key or action_key in existing_keys:
            continue
        row_actions.append(_deep_clone_json_like(action))
        existing_keys.add(action_key)
    kanban["row_actions"] = row_actions
    views["kanban"] = kanban
    data["views"] = views


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
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect_layout_field_names(nodes: list, out: list[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type"))
            if node_type == "field":
                name = _safe_text(node.get("name"))
                if name and name not in out:
                    out.append(name)
            for children in _iter_children(node):
                _collect_layout_field_names(children, out)

    def _prune_layout(nodes: list, allowed: set[str]) -> list[dict]:
        cleaned: list[dict] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type"))
            if node_type == "field":
                name = _safe_text(node.get("name"))
                if name and name in allowed:
                    cleaned.append(node)
                continue
            copied = dict(node)
            structured_children_present = False
            for key in ("children", "tabs", "pages", "nodes", "items"):
                raw_children = node.get(key)
                if not isinstance(raw_children, list):
                    continue
                pruned_children = _prune_layout(raw_children, allowed)
                copied[key] = pruned_children
                if key in {"children", "tabs", "pages"} and pruned_children:
                    structured_children_present = True
            keep_node = True
            if node_type in {"group", "page", "notebook", "sheet", "header"}:
                has_structured_key = any(isinstance(node.get(key), list) for key in ("children", "tabs", "pages"))
                if has_structured_key and not structured_children_present:
                    keep_node = False
            if keep_node:
                cleaned.append(copied)
        return cleaned

    selected_order = [name for name in selected_fields if _safe_text(name)]
    selected_set = set(selected_order)
    filtered_layout = _prune_layout(layout, selected_set)

    existing_field_names: list[str] = []
    _collect_layout_field_names(filtered_layout, existing_field_names)
    if not existing_field_names:
        primary_fields = _legacy_project_form_profile(data).get("primary_fields") or []
        for name in primary_fields:
            if name in selected_fields:
                filtered_layout.append({"type": "field", "name": name})
        _collect_layout_field_names(filtered_layout, existing_field_names)

    # Ensure filtered layout covers selected user-surface fields, so frontend can render
    # a coherent contract-driven form without falling back to unordered field maps.
    existing_set = set(existing_field_names)
    missing_selected = [name for name in selected_order if name and name not in existing_set]
    for name in missing_selected:
        filtered_layout.append({"type": "field", "name": name})
    form["layout"] = filtered_layout
    views["form"] = form
    data["views"] = views


def _trim_contract_field_maps(data: dict, selected_fields: list[str]) -> None:
    selected = [_safe_text(name) for name in selected_fields if _safe_text(name)]
    if not selected:
        return
    allowed = set(selected)
    fields_map = _as_dict(data.get("fields"))
    if fields_map:
        data["fields"] = {name: fields_map[name] for name in selected if name in fields_map}
    field_policies = _as_dict(data.get("field_policies"))
    if field_policies:
        data["field_policies"] = {name: field_policies[name] for name in selected if name in field_policies}
    field_semantics = _as_dict(data.get("field_semantics"))
    if field_semantics:
        data["field_semantics"] = {name: field_semantics[name] for name in selected if name in field_semantics}
    validation_rules = data.get("validation_rules")
    if isinstance(validation_rules, list):
        data["validation_rules"] = [
            row
            for row in validation_rules
            if not isinstance(row, dict) or not _safe_text(row.get("field")) or _safe_text(row.get("field")) in allowed
        ]


def _govern_project_form_search(data: dict) -> None:
    search = _as_dict(data.get("search"))
    filters = search.get("filters")
    if not isinstance(filters, list):
        return
    noise_markers = _legacy_project_form_profile(data).get("search_noise_markers") or []
    cleaned = []
    seen: set[str] = set()
    for row in filters:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        label = _safe_text(row.get("label"))
        if not key or key in seen:
            continue
        if not label:
            continue
        if any(marker in _safe_lower(label) for marker in noise_markers):
            continue
        cleaned.append(row)
        seen.add(key)
        if len(cleaned) >= 8:
            break
    search["filters"] = cleaned
    data["search"] = search


def _action_priority(action: dict, data: dict | None = None) -> int:
    label = _safe_text(action.get("label"))
    priorities = _legacy_project_form_profile(data or {}).get("action_priorities") or []
    for idx, key in enumerate(priorities):
        if key and key in label:
            return idx
    return len(priorities) + 1


def _is_noisy_project_action(action: dict, data: dict | None = None) -> bool:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    if not label and not key:
        return True
    if label.isdigit():
        return True
    markers = _legacy_project_form_profile(data or {}).get("action_noise_markers") or []
    for marker in markers:
        if marker in key or marker in label:
            return True
    return False


def _classify_project_action_group(action: dict) -> str:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    merged = f"{key} {label}"
    if any(marker in merged for marker in ("阶段", "提交", "审批", "transition", "workflow", "lifecycle")):
        return "workflow"
    if any(marker in merged for marker in ("查看", "open", "dashboard", "看板", "列表")):
        return "drilldown"
    if any(marker in merged for marker in ("创建", "保存", "提交")):
        return "basic"
    return "other"


def _build_project_action_groups(rows: list[dict], data: dict | None = None) -> list[dict]:
    grouped: dict[str, list[dict]] = {"basic": [], "workflow": [], "drilldown": [], "other": []}
    for row in rows:
        if not isinstance(row, dict):
            continue
        group_key = _classify_project_action_group(row)
        grouped.setdefault(group_key, []).append(row)

    result: list[dict] = []
    group_labels = dict(_PROJECT_FORM_DEFAULT_ACTION_GROUP_LABELS)
    group_labels.update(_legacy_project_form_profile(data or {}).get("action_group_labels") or {})
    for key in ("basic", "workflow", "drilldown", "other"):
        actions = grouped.get(key) or []
        if not actions:
            continue
        primary = actions[:_PROJECT_FORM_ACTION_GROUP_LIMIT]
        overflow = actions[_PROJECT_FORM_ACTION_GROUP_LIMIT:]
        result.append({
            "key": key,
            "label": group_labels.get(key, key),
            "actions": primary,
            "overflow_actions": overflow,
            "overflow_count": len(overflow),
        })
    return result


def _emit_scene_action_semantics(data: dict, *, header_rows: list[dict], record_rows: list[dict]) -> None:
    semantic_page = _as_dict(data.get("semantic_page"))
    actions = _as_dict(semantic_page.get("actions"))
    actions["header_actions"] = [dict(row) for row in header_rows if isinstance(row, dict)]
    actions["record_actions"] = [dict(row) for row in record_rows if isinstance(row, dict)]
    actions.setdefault("toolbar_actions", [])
    actions["owner_layer"] = "scene_orchestration"
    actions["source"] = "contract_governance.curated_action_facts"
    semantic_page["actions"] = actions
    data["semantic_page"] = semantic_page


def _govern_project_form_actions(data: dict) -> None:
    toolbar = _as_dict(data.get("toolbar"))
    if isinstance(toolbar.get("header"), list):
        toolbar["header"] = []
    data["toolbar"] = toolbar

    rows = data.get("buttons")
    if not isinstance(rows, list):
        return
    header_rows: list[dict] = []
    smart_rows: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _is_noisy_project_action(row, data):
            continue
        level = _safe_lower(row.get("level"))
        if level == "header":
            header_rows.append(row)
        elif level in {"smart", "row"}:
            smart_rows.append(row)

    header_rows = sorted(header_rows, key=lambda item: (_action_priority(item, data), _safe_text(item.get("label"))))
    smart_rows = sorted(smart_rows, key=lambda item: (_action_priority(item, data), _safe_text(item.get("label"))))
    curated = header_rows[:_PROJECT_FORM_HEADER_ACTION_MAX] + smart_rows[:_PROJECT_FORM_SMART_ACTION_MAX]
    data["buttons"] = curated
    _emit_scene_action_semantics(
        data,
        header_rows=header_rows[:_PROJECT_FORM_HEADER_ACTION_MAX],
        record_rows=smart_rows[:_PROJECT_FORM_SMART_ACTION_MAX],
    )
    data["action_groups"] = _build_project_action_groups(curated, data)


def _build_project_lifecycle_summary(data: dict) -> None:
    _project_form.build_project_lifecycle_summary(data)


def _govern_project_form_contract_for_user(data: dict) -> None:
    selected = _pick_project_form_fields(data)
    profile = _legacy_project_form_profile(data)
    _trim_contract_field_maps(data, selected)
    data["visible_fields"] = selected
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    native_layout_fields = _collect_layout_field_names(form.get("layout"))
    if not native_layout_fields:
        _backfill_form_layout_from_visible_fields(data)
    data["form_profile"] = {
        "core_fields": selected[:8],
        "advanced_fields": selected[8:],
        "max_fields": int(profile.get("max_fields") or _PROJECT_FORM_FIELD_MAX),
    }
    # Keep parser-native notebook/page tree intact for project form alignment.
    # Do not prune form layout by selected fields in user mode.
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["form_profile"] = _as_dict(data.get("form_profile"))
    views["form"] = form
    data["views"] = views

    permissions = _as_dict(data.get("permissions"))
    field_groups = _as_dict(permissions.get("field_groups"))
    if field_groups:
        permissions["field_groups"] = field_groups
    data["permissions"] = permissions

    _govern_project_form_actions(data)
    _govern_project_form_search(data)
    _build_project_lifecycle_summary(data)
    _realign_access_policy_with_visible_fields(data)


def _govern_project_task_form_for_user(data: dict) -> None:
    if not _is_project_task_form_contract(data):
        return
    primary_model = _governance_primary_model(data)
    profile = _LEGACY_PROJECT_TASK_FORM_PROFILE_REGISTRY.get(primary_model) or {}
    if not profile:
        return
    fields_map = _as_dict(data.get("fields"))
    configured_fields = [_safe_text(name) for name in (profile.get("fields") or []) if _safe_text(name)]
    selected = [name for name in configured_fields if name in fields_map]
    if not selected:
        return
    label_map = _as_dict(profile.get("field_labels"))
    description_fields = set(profile.get("description_fields") or [])
    core_group_label = _safe_text(profile.get("core_group_label")) or "基础信息"
    description_group_label = _safe_text(profile.get("description_group_label")) or "说明"

    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": core_group_label,
            "priority": 1,
            "collapsible": False,
            "fields": [name for name in selected if name not in description_fields],
        },
        {
            "name": "advanced",
            "label": description_group_label,
            "priority": 2,
            "collapsible": True,
            "fields": [name for name in selected if name in description_fields],
        },
    ]

    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "project_task_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "project_task_core_group",
                    "string": core_group_label,
                    "children": [
                        _make_labeled_field_node(name, fields_map, label_map)
                        for name in selected
                        if name not in description_fields
                    ],
                },
                {
                    "type": "group",
                    "name": "project_task_description_group",
                    "string": description_group_label,
                    "children": [
                        _make_labeled_field_node(name, fields_map, label_map)
                        for name in selected
                        if name in description_fields
                    ],
                },
            ],
        }
    ]
    views["form"] = form
    data["views"] = views


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
    if not _is_model_tree_contract(data, model_name):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in columns_order if name in fields_map]
    if not selected:
        return

    views = _as_dict(data.get("views"))
    tree = _as_dict(views.get("tree") or views.get("list"))
    tree_governance = _as_dict(tree.get("governance"))
    tree_view_orchestration = _as_dict(tree_governance.get("view_orchestration"))
    tree_source_trace = _as_dict(tree.get("source_trace"))
    tree_trace_orchestration = _as_dict(tree_source_trace.get("view_orchestration"))
    has_orchestrated_tree = bool(
        tree_view_orchestration.get("applied")
        or tree_trace_orchestration.get("business_config_contracts")
    )
    native_schema_rows = tree.get("columns_schema") if isinstance(tree.get("columns_schema"), list) else []
    native_schema_by_name = {
        _safe_text(row.get("name")): dict(row)
        for row in native_schema_rows
        if isinstance(row, dict) and _safe_text(row.get("name"))
    }
    native_columns = []
    for row in tree.get("columns") or []:
        if isinstance(row, dict):
            name = _safe_text(row.get("name"))
        else:
            name = _safe_text(row)
        if name and name not in native_columns:
            native_columns.append(name)
    for name in native_schema_by_name:
        if name not in native_columns:
            native_columns.append(name)
    # Governance may order and enrich standard business columns. Once a
    # business orchestration was applied to the native tree block, that
    # orchestrated order is the user-facing order and standard governance only
    # appends its defaults.
    if has_orchestrated_tree and native_columns:
        selected = [name for name in native_columns if name in fields_map]
        for name in columns_order:
            if name in fields_map and name not in selected:
                selected.append(name)
    elif strict_columns:
        selected = [name for name in columns_order if name in fields_map]
    else:
        for name in native_columns:
            if name in fields_map and name not in selected:
                selected.append(name)

    def _field_label(name: str) -> str:
        schema_label = _safe_text(native_schema_by_name.get(name, {}).get("label") or native_schema_by_name.get(name, {}).get("string"))
        field_label = _safe_text(_as_dict(fields_map.get(name)).get("string"))
        if has_orchestrated_tree and schema_label:
            return schema_label
        return column_labels.get(name) or schema_label or field_label or name

    def _column_schema(name: str) -> dict:
        field = _as_dict(fields_map.get(name))
        schema = dict(native_schema_by_name.get(name) or {})
        schema["name"] = name
        schema["label"] = _field_label(name)
        schema["string"] = schema["label"]
        schema["type"] = schema.get("type") or field.get("type") or "char"
        schema["widget"] = schema.get("widget") or field.get("type") or "char"
        presentation = _legacy_field_presentation(model_name, name)
        if presentation:
            if presentation.get("label"):
                schema["label"] = presentation["label"]
                schema["string"] = presentation["label"]
            if presentation.get("widget"):
                schema["widget"] = presentation["widget"]
            if presentation.get("cell_role"):
                schema["cell_role"] = presentation["cell_role"]
            if isinstance(presentation.get("mutation"), dict) and presentation["mutation"]:
                schema["mutation"] = _deep_clone_json_like(presentation["mutation"])
        if name == status_field:
            schema["cell_role"] = "status"
            schema["tone_by_value"] = {
                "draft": "neutral",
                "in_progress": "info",
                "paused": "warning",
                "done": "success",
                "closing": "warning",
                "warranty": "info",
                "closed": "neutral",
            }
        if isinstance(field.get("selection"), list) and not isinstance(schema.get("selection"), list):
            schema["selection"] = [
                {"value": item[0], "label": item[1]}
                for item in field.get("selection")
                if isinstance(item, (list, tuple)) and len(item) >= 2
            ]
        return schema

    tree["columns"] = selected
    tree["columns_schema"] = [_column_schema(name) for name in selected]
    views["tree"] = tree
    data["views"] = views

    metric_fields = [
        name
        for name in (
            "contract_income_total",
            "contract_amount",
            "dashboard_invoice_amount",
            "amount_total",
            "total_amount",
            "planned_revenue",
            "budget_total",
        )
        if name in fields_map
    ]
    active_field = "active" if "active" in fields_map else ""
    assignee_field = "user_id" if "user_id" in fields_map else ""
    surface_policies = _as_dict(data.get("surface_policies"))
    surface_batch_policy = _as_dict(surface_policies.get("batch_policy"))
    delete_policy = _as_dict(data.get("delete_policy"))
    permissions = _as_dict(data.get("permissions"))
    effective = _as_dict(permissions.get("effective"))
    rights = _as_dict(effective.get("rights"))
    write_allowed = bool(rights.get("write"))
    unlink_right_allowed = bool(rights.get("unlink"))
    raw_available_actions = (
        surface_batch_policy.get("available_actions")
        if isinstance(surface_batch_policy.get("available_actions"), list)
        else []
    )
    if rights and not (write_allowed or unlink_right_allowed):
        raw_available_actions = []
    delete_mode = _safe_text(
        surface_policies.get("delete_mode")
        or delete_policy.get("delete_mode")
        or data.get("delete_mode"),
        "none",
    )
    available_actions = []
    if (write_allowed or unlink_right_allowed) and not raw_available_actions:
        raw_available_actions = []
        if active_field:
            raw_available_actions.extend(["archive", "activate"])
        if delete_mode == "unlink":
            raw_available_actions.append("delete")
    for raw_action in raw_available_actions:
        action = _safe_lower(raw_action)
        if action in {"archive", "activate"}:
            if active_field and write_allowed and action not in available_actions:
                available_actions.append(action)
            continue
        if action == "delete":
            if unlink_right_allowed and delete_mode == "unlink" and action not in available_actions:
                available_actions.append(action)
    batch_policy = {
        "enabled": bool(available_actions),
        "active_field": active_field,
        "assignee_field": assignee_field,
        "archive_value": False if active_field else None,
        "activate_value": True if active_field else None,
        "assignee_options": {
            "model": "res.users",
            "fields": ["id", "name"],
            "domain": [["active", "=", True]],
            "order": "name asc",
            "limit": 80,
        }
        if assignee_field
        else None,
        "delete_mode": delete_mode if "delete" in available_actions else "none",
        "available_actions": available_actions,
    }

    list_profile = _as_dict(data.get("list_profile"))
    list_profile.update(
        {
            "source": "contract_governance.curated_list_facts",
            "columns": selected,
            "fact_columns": selected,
            "hidden_columns": [],
            "column_labels": {name: _field_label(name) for name in selected},
            "row_primary": row_primary,
            "row_secondary": row_secondary,
            "primary_field": row_primary,
            "status_field": status_field,
            "metric_fields": metric_fields,
            "preference_policy": {
                "scope": "ui_only",
                "allow_visibility": True,
                "allow_order": True,
                "allow_width": True,
                "locked_columns": [],
                "must_request_columns": selected,
            },
            "batch_policy": batch_policy,
            "grouping": {
                "sample_limits": [3, 5, 8],
                "default_sample_limit": 3,
                "sort": {
                    "key": "count",
                    "default_direction": "desc",
                    "directions": ["desc", "asc"],
                },
            },
        }
    )
    if strict_columns:
        list_profile["column_policy"] = {
            "mode": "strict",
            "reason": "native_tree_columns_are_the_user_visible_business_surface",
        }
        list_profile["preference_policy"]["allow_visibility"] = True
        list_profile["preference_policy"]["allow_order"] = True
        list_profile["preference_policy"]["locked_columns"] = []
    data["list_profile"] = list_profile
    views = _as_dict(data.get("views"))
    tree_view = _as_dict(views.get("tree") or views.get("list"))
    if tree_view:
        tree_view.setdefault("order", "write_date desc, id desc")
        tree_view.setdefault("default_order", "write_date desc, id desc")
        if "tree" in views:
            views["tree"] = tree_view
        else:
            views["list"] = tree_view
        data["views"] = views
    surface_policies["batch_policy"] = batch_policy
    surface_policies["delete_mode"] = batch_policy.get("delete_mode") or surface_policies.get("delete_mode") or "none"
    data["surface_policies"] = surface_policies

    semantic_page = _as_dict(data.get("semantic_page"))
    list_semantics = _as_dict(semantic_page.get("list_semantics"))
    list_semantics["owner_layer"] = "scene_orchestration"
    list_semantics["source"] = "contract_governance.curated_list_facts"
    list_semantics["columns"] = [
        {
            "name": name,
            "label": _field_label(name),
            "widget": _column_schema(name).get("widget"),
            "cell_role": _column_schema(name).get("cell_role") or "text",
        }
        for name in selected
    ]
    list_semantics["row_primary"] = row_primary
    list_semantics["row_secondary"] = row_secondary
    list_semantics["status_field"] = status_field
    list_semantics["metric_fields"] = metric_fields
    list_semantics["batch_policy"] = batch_policy
    semantic_page["list_semantics"] = list_semantics
    data["semantic_page"] = semantic_page
    _apply_standard_search_toolbar_labels(data)


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
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _ENTERPRISE_COMPANY_FORM_FIELDS if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "企业基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": selected,
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_company_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_company_core_group",
                    "string": "企业基础信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _ENTERPRISE_COMPANY_FIELD_LABELS)
                        for name in selected
                    ],
                }
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    if _resolve_render_profile(data) == _RENDER_PROFILE_CREATE:
        toolbar = _as_dict(data.get("toolbar"))
        if isinstance(toolbar.get("header"), list):
            toolbar["header"] = []
        data["toolbar"] = toolbar
        data["buttons"] = []
        data["action_groups"] = []
    _inject_enterprise_form_governance(
        data,
        next_action_key="department",
        next_action_label="进入组织架构",
    )


def _govern_enterprise_department_form_for_user(data: dict) -> None:
    if _governance_primary_model(data) != "hr.department":
        return
    if not _is_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _ENTERPRISE_DEPARTMENT_FORM_FIELDS if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "组织基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": selected,
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_department_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_department_core_group",
                    "string": "组织基础信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map, _ENTERPRISE_DEPARTMENT_FIELD_LABELS)
                        for name in selected
                    ],
                }
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    if _resolve_render_profile(data) == _RENDER_PROFILE_CREATE:
        toolbar = _as_dict(data.get("toolbar"))
        if isinstance(toolbar.get("header"), list):
            toolbar["header"] = []
        data["toolbar"] = toolbar
        data["buttons"] = []
        data["action_groups"] = []
    _inject_enterprise_form_governance(
        data,
        next_action_key="user",
        next_action_label="进入用户设置",
    )


def _govern_enterprise_user_form_for_user(data: dict) -> None:
    if not _is_enterprise_user_form_contract(data):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in _ENTERPRISE_USER_FORM_FIELDS if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "account",
            "label": "账号信息",
            "priority": 1,
            "collapsible": False,
            "fields": [name for name in selected if name in {"login", "name", "active", "password"}],
        },
        {
            "name": "contact",
            "label": "联系方式",
            "priority": 2,
            "collapsible": False,
            "fields": [name for name in selected if name in {"phone", "email"}],
        },
        {
            "name": "assignment",
            "label": "组织归属",
            "priority": 3,
            "collapsible": False,
            "fields": [
                name
                for name in selected
                if name in {"company_id", "sc_department_id", "sc_manager_user_id", "sc_role_profile", "sc_role_effective", "sc_role_landing_label"}
            ],
        },
        {
            "name": "permissions",
            "label": "业务角色",
            "priority": 4,
            "collapsible": False,
            "fields": [name for name in selected if name in {"sc_user_role_group_ids"}],
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_user_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_user_basic_group",
                    "string": "账号信息",
                    "children": [
                        _make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in {"login", "name", "active", "password"}
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_contact_group",
                    "string": "联系方式",
                    "children": [
                        _make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in {"phone", "email"}
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_assignment_group",
                    "string": "组织归属",
                    "children": [
                        _make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in {"company_id", "sc_department_id", "sc_manager_user_id", "sc_role_profile", "sc_role_effective", "sc_role_landing_label"}
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_permissions_group",
                    "string": "业务角色",
                    "children": [
                        _make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in {"sc_user_role_group_ids"}
                    ],
                },
            ],
        }
    ]
    form["statusbar"] = {"field": None, "states": []}
    form["header_buttons"] = []
    form["button_box"] = []
    form["stat_buttons"] = []
    views["form"] = form
    data["views"] = views

    field_policies = _as_dict(data.get("field_policies"))
    basic_fields = {"name", "login", "password", "phone", "email", "active", "sc_user_role_group_ids"}
    readonly_fields = {"sc_role_effective", "sc_role_landing_label"}
    contract_required_fields = set(_resolve_contract_required_fields(data, fields_map))
    for name in selected:
        descriptor = _as_dict(fields_map.get(name))
        readonly = name in readonly_fields or _to_bool(descriptor.get("readonly"), fallback=False)
        field_policies[name] = {
            "visible_profiles": [
                _RENDER_PROFILE_CREATE,
                _RENDER_PROFILE_EDIT,
                _RENDER_PROFILE_READONLY,
            ],
            "required_profiles": (
                [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]
                if name in contract_required_fields and not readonly
                else []
            ),
            "readonly_profiles": (
                [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
                if readonly
                else [_RENDER_PROFILE_READONLY]
            ),
            "source_required": name in contract_required_fields and not readonly,
            "source_readonly": readonly,
            "group": "core" if name in basic_fields else "secondary",
        }
    data["field_policies"] = field_policies

    toolbar = _as_dict(data.get("toolbar"))
    if isinstance(toolbar.get("header"), list):
        toolbar["header"] = []
    data["toolbar"] = toolbar
    data["buttons"] = []
    data["action_groups"] = []
    _inject_enterprise_form_governance(data)


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
    if not callable(handler):
        return
    normalized_name = _safe_text(name, "unnamed_override")
    for row in _DOMAIN_OVERRIDE_REGISTRY:
        if _safe_text(row.get("name")) == normalized_name:
            row["handler"] = handler
            row["priority"] = int(priority)
            return
    _DOMAIN_OVERRIDE_REGISTRY.append(
        {
            "name": normalized_name,
            "priority": int(priority),
            "handler": handler,
        }
    )
    _DOMAIN_OVERRIDE_REGISTRY.sort(key=lambda item: int(item.get("priority") or 100))


def _append_governance_diagnostic(data: dict, key: str, value: Any) -> None:
    diagnostic = data.get("diagnostic")
    if not isinstance(diagnostic, dict):
        diagnostic = {}
    diagnostic[key] = value
    data["diagnostic"] = diagnostic


def _apply_domain_overrides(data: dict, contract_mode: str) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in _DOMAIN_OVERRIDE_REGISTRY:
        handler = row.get("handler")
        if not callable(handler):
            continue
        try:
            handler(data, contract_mode)
        except Exception as exc:
            failures.append(
                {
                    "name": _safe_text(row.get("name")),
                    "error_type": exc.__class__.__name__,
                    "message": _safe_text(str(exc))[:240],
                }
            )
            continue
    return failures


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
    if isinstance(obj, dict):
        return {k: _deep_clone_json_like(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deep_clone_json_like(v) for v in obj]
    return obj


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
