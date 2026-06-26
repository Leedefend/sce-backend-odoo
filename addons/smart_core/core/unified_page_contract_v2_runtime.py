# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .source_authority import build_source_authority_contract

PATCH_OPERATIONS = ("replace", "merge", "append", "remove", "reorder", "invalidate")
SOURCE_KIND = "unified_page_contract_v2_runtime_projection"
SOURCE_AUTHORITIES = ("unified_page_contract_v2", "runtime_contract_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_runtime",
    )

FORBIDDEN_RUNTIME_KEYS = {
    "script",
    "scripts",
    "function",
    "functions",
    "eval",
    "expression",
    "expressions",
    "jsonLogic",
    "workflowDsl",
    "bpmn",
    "loop",
    "loops",
    "componentCode",
}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _count_containers(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        total += 1
        for key in ("children", "pages", "tabs", "nodes", "items"):
            total += _count_containers(row.get(key))
    return total


def _count_widgets(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        widget_list = _list(row.get("widgetList"))
        if widget_list:
            total += len(widget_list)
        elif _text(row.get("type") or row.get("kind")).lower() == "field":
            total += 1
        else:
            total += len([child for child in _list(row.get("children")) if isinstance(child, dict) and _text(child.get("type") or child.get("kind")).lower() == "field"])
            total += len([child for child in _list(row.get("pages")) if isinstance(child, dict) and _text(child.get("type") or child.get("kind")).lower() == "field"])
            total += len([child for child in _list(row.get("tabs")) if isinstance(child, dict) and _text(child.get("type") or child.get("kind")).lower() == "field"])
            total += len([child for child in _list(row.get("nodes")) if isinstance(child, dict) and _text(child.get("type") or child.get("kind")).lower() == "field"])
            total += len([child for child in _list(row.get("items")) if isinstance(child, dict) and _text(child.get("type") or child.get("kind")).lower() == "field"])
        for key in ("children", "pages", "tabs", "nodes", "items"):
            total += _count_widgets(row.get(key))
    return total


def _complexity_budget(contract: dict[str, Any]) -> dict[str, Any]:
    layout = _dict(contract.get("layoutContract"))
    status = _dict(contract.get("statusContract"))
    action = _dict(contract.get("actionContract"))
    data = _dict(contract.get("dataContract"))
    containers = _count_containers(layout.get("containerTree"))
    widgets = _count_widgets(layout.get("containerTree"))
    actions = len(_list(action.get("actionRuleList")))
    selector_status = len(_list(status.get("selectorStatus")))
    data_sources = len(_dict(data.get("dataSource")))
    score = containers + widgets + (actions * 2) + selector_status + data_sources
    return {
        "containers": containers,
        "widgets": widgets,
        "actions": actions,
        "selectorStatus": selector_status,
        "dataSources": data_sources,
        "score": score,
        "level": "high" if score >= 120 else "medium" if score >= 40 else "low",
        "maxScore": 200,
    }


def build_runtime_contract_v2(contract: dict[str, Any], *, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    source = _dict(contract)
    current = _dict(source.get("runtimeContract"))
    override = _dict(overrides)
    patch_ops = override.get("patchOperations") or current.get("patchOperations") or list(PATCH_OPERATIONS)
    normalized_ops = [op for op in patch_ops if op in PATCH_OPERATIONS]
    runtime = {
        "patchStrategy": _text(override.get("patchStrategy") or current.get("patchStrategy"), "incremental"),
        "cachePolicy": _text(override.get("cachePolicy") or current.get("cachePolicy"), "etag"),
        "optimistic": bool(override.get("optimistic") if "optimistic" in override else current.get("optimistic", False)),
        "lazyContainer": deepcopy(_list(override.get("lazyContainer") or current.get("lazyContainer"))),
        "virtualization": deepcopy(_dict(override.get("virtualization") or current.get("virtualization"))),
        "retryPolicy": deepcopy(_dict(override.get("retryPolicy") or current.get("retryPolicy") or {"maxRetries": 1})),
        "renderStrategy": _text(override.get("renderStrategy") or current.get("renderStrategy"), "sync"),
        "hydration": deepcopy(_dict(override.get("hydration") or current.get("hydration") or {"mode": "eager"})),
        "patchOperations": normalized_ops,
        "tracePolicy": deepcopy(_dict(override.get("tracePolicy") or current.get("tracePolicy") or {"required": True})),
        "complexityBudget": _complexity_budget(source),
        "aiEnvelope": _normalize_ai_envelope(override.get("aiEnvelope") or current.get("aiEnvelope")),
    }
    if runtime["patchStrategy"] not in {"incremental", "full"}:
        runtime["patchStrategy"] = "incremental"
    if runtime["cachePolicy"] not in {"none", "etag", "snapshot"}:
        runtime["cachePolicy"] = "etag"
    if runtime["renderStrategy"] not in {"sync", "scheduled", "virtualized"}:
        runtime["renderStrategy"] = "sync"
    return runtime


def _normalize_ai_envelope(value: Any) -> dict[str, Any]:
    row = _dict(value)
    if not row:
        return {"mode": "suggestion", "executable": False, "allowed": False}
    return {
        "mode": "suggestion",
        "executable": False,
        "allowed": bool(row.get("allowed") is True),
        "capabilities": [str(item) for item in _list(row.get("capabilities")) if str(item).strip()],
    }


def find_runtime_guard_issues(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    runtime = _dict(contract.get("runtimeContract"))
    meta = _dict(contract.get("meta"))
    action = _dict(contract.get("actionContract"))
    layout = _dict(contract.get("layoutContract"))
    status = _dict(contract.get("statusContract"))
    data = _dict(contract.get("dataContract"))
    if not runtime:
        issues.append("runtimeContract is required")
    for key in ("etag", "snapshotId", "traceId", "requestId"):
        if not _text(meta.get(key)):
            issues.append(f"meta.{key} is required")
    ops = _list(runtime.get("patchOperations"))
    unknown_ops = [op for op in ops if op not in PATCH_OPERATIONS]
    if unknown_ops:
        issues.append(f"unknown patch operations: {unknown_ops}")
    ai = _dict(runtime.get("aiEnvelope"))
    if ai.get("executable") is True or _text(ai.get("mode")) not in {"", "suggestion"}:
        issues.append("aiEnvelope must be suggestion-only and non-executable")
    for path, node in _walk(runtime):
        if isinstance(node, dict):
            for key in node:
                if key in FORBIDDEN_RUNTIME_KEYS:
                    issues.append(f"forbidden runtime key at {path}.{key}")
    graph = _dict(action.get("dependencyGraph"))
    for source, targets in graph.items():
        if not isinstance(targets, list):
            issues.append(f"dependencyGraph.{source} must be a list")
        for target in _list(targets):
            if isinstance(target, dict):
                issues.append(f"dependencyGraph.{source} contains executable object edge")
    registry = _dict(layout.get("componentRegistry"))
    if not registry:
        issues.append("layoutContract.componentRegistry is required for runtime adapter resolution")
    for row in _list(status.get("selectorStatus")):
        if isinstance(row, dict) and not _text(row.get("selector")):
            issues.append("selectorStatus row missing selector")
    issues.extend(find_data_source_authority_issues(data))
    issues.extend(find_metadata_projection_issues(data))
    issues.extend(find_policy_contract_issues(contract))
    issues.extend(find_form_structure_contract_issues(contract))
    return issues


def find_data_source_authority_issues(data_contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    data_sources = _dict(data_contract.get("dataSource"))
    for key, source in data_sources.items():
        source_row = _dict(source)
        if not source_row:
            continue
        source_authority = _dict(source_row.get("sourceAuthority") or source_row.get("source_authority"))
        if not source_authority:
            issues.append(f"dataContract.dataSource.{key}.sourceAuthority is required")
            continue
        if source_authority.get("projection_only") is not True:
            issues.append(f"dataContract.dataSource.{key}.sourceAuthority.projection_only must be true")
        if source_authority.get("no_business_fact_authority") is not True:
            issues.append(f"dataContract.dataSource.{key}.sourceAuthority.no_business_fact_authority must be true")
        if not _text(source_authority.get("fact_authority")):
            issues.append(f"dataContract.dataSource.{key}.sourceAuthority.fact_authority is required")
    return issues


def find_metadata_projection_issues(data_contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    data_meta = _dict(data_contract.get("dataMeta"))
    legacy_projection = _dict(data_meta.get("legacyContractProjection") or data_meta.get("legacy_contract_projection"))
    if "legacyContractProjection" in data_meta or "legacy_contract_projection" in data_meta:
        issues.append("dataContract.dataMeta.legacyContractProjection must not be emitted in stable V2 contract")
    for key in ("business_operation_profile", "visible_fields", "field_groups"):
        if key in data_meta:
            issues.append(f"dataContract.dataMeta.{key} must not be emitted; use formal V2 camelCase metadata")
    for key in ("business_operation_profile", "field_groups", "form_structure_contract", "formStructureContract", "list_profile", "visible_fields"):
        if key in legacy_projection:
            issues.append(f"legacyContractProjection.{key} must not be emitted; use formal V2 metadata")
    _validate_metadata_projection_authority(
        issues,
        value=data_meta.get("businessOperationProfile"),
        source_key="business_operation_profile",
        projected_path="dataContract.dataMeta.businessOperationProfile",
    )
    visible_fields = data_meta.get("visibleFields")
    _validate_metadata_projection_authority(
        issues,
        value=visible_fields,
        source_key="visible_fields",
        projected_path="dataContract.dataMeta.visibleFields",
    )
    visible_fields_row = _dict(visible_fields)
    if visible_fields_row and not _list(visible_fields_row.get("fields")):
        issues.append("dataContract.dataMeta.visibleFields.fields is required")
    field_groups = data_meta.get("fieldGroups")
    _validate_metadata_projection_authority(
        issues,
        value=field_groups,
        source_key="field_groups",
        projected_path="dataContract.dataMeta.fieldGroups",
    )
    field_groups_row = _dict(field_groups)
    if field_groups_row and not _list(field_groups_row.get("groups")):
        issues.append("dataContract.dataMeta.fieldGroups.groups is required")
    return issues


def _validate_metadata_projection_authority(
    issues: list[str],
    *,
    value: Any,
    source_key: str,
    projected_path: str,
) -> None:
    row = _dict(value)
    if not row:
        return
    source_authority = _dict(row.get("sourceAuthority") or row.get("source_authority"))
    if not source_authority:
        issues.append(f"{projected_path}.sourceAuthority is required")
        return
    if source_authority.get("projection_only") is not True:
        issues.append(f"{projected_path}.sourceAuthority.projection_only must be true")
    if source_authority.get("no_business_fact_authority") is not True:
        issues.append(f"{projected_path}.sourceAuthority.no_business_fact_authority must be true")
    if source_authority.get("formal_projection") is not True:
        issues.append(f"{projected_path}.sourceAuthority.formal_projection must be true")
    if _text(source_authority.get("source_key")) != source_key:
        issues.append(f"{projected_path}.sourceAuthority.source_key must be {source_key}")


def find_policy_contract_issues(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    source = _dict(contract)
    action = _dict(source.get("actionContract"))
    layout = _dict(source.get("layoutContract"))
    for key in ("delete_policy", "surface_policies", "list_profile"):
        if key in source:
            issues.append(f"root compatibility field {key} must not be emitted by V2 contract")
    for key in ("delete_policy", "surface_policies"):
        if key in action:
            issues.append(f"actionContract compatibility field {key} must not be emitted by V2 contract")
    if "list_profile" in layout:
        issues.append("layoutContract compatibility field list_profile must not be emitted by V2 contract")
    _validate_policy_projection(
        issues,
        projected_value=action.get("deletePolicy"),
        source_key="delete_policy",
        projected_path="actionContract.deletePolicy",
    )
    _validate_policy_projection(
        issues,
        projected_value=action.get("surfacePolicies"),
        source_key="surface_policies",
        projected_path="actionContract.surfacePolicies",
    )
    _validate_policy_projection(
        issues,
        projected_value=layout.get("listProfile"),
        source_key="list_profile",
        projected_path="layoutContract.listProfile",
    )
    return issues


def _validate_policy_projection(
    issues: list[str],
    *,
    projected_value: Any,
    source_key: str,
    projected_path: str,
) -> None:
    if not isinstance(projected_value, dict) or not projected_value:
        return
    projected = _dict(projected_value)
    source_authority = _dict(projected.get("sourceAuthority") or projected.get("source_authority"))
    if not source_authority:
        issues.append(f"{projected_path}.sourceAuthority is required")
    else:
        if source_authority.get("projection_only") is not True:
            issues.append(f"{projected_path}.sourceAuthority.projection_only must be true")
        if source_authority.get("no_business_fact_authority") is not True:
            issues.append(f"{projected_path}.sourceAuthority.no_business_fact_authority must be true")
        if source_authority.get("formal_projection") is not True:
            issues.append(f"{projected_path}.sourceAuthority.formal_projection must be true")
        if _text(source_authority.get("source_key")) != source_key:
            issues.append(f"{projected_path}.sourceAuthority.source_key must be {source_key}")


def find_form_structure_contract_issues(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if "form_structure_contract" in contract:
        issues.append("root compatibility field form_structure_contract must not be emitted by V2 contract")
    structure = _dict(contract.get("formStructureContract") or contract.get("form_structure_contract"))
    if not structure:
        return issues
    if _text(structure.get("source")) != "ui.contract.v2.form_structure_contract":
        issues.append("formStructureContract.source must be ui.contract.v2.form_structure_contract")
    if _text(structure.get("viewType") or structure.get("view_type")) not in {"", "form"}:
        issues.append("formStructureContract.viewType must be form")
    source_authority = _dict(structure.get("sourceAuthority") or structure.get("source_authority"))
    if source_authority and source_authority.get("governed_form_structure") is not True:
        issues.append("formStructureContract.sourceAuthority.governed_form_structure must be true")
    governance_source = _dict(source_authority.get("governance_source"))
    if source_authority and not governance_source:
        issues.append("formStructureContract.sourceAuthority.governance_source is required")

    fields = _dict(_dict(contract.get("dataContract")).get("dataMeta")).get("fields")
    known_fields = set(_dict(fields).keys())
    if not known_fields:
        known_fields = _collect_layout_field_names(_list(_dict(contract.get("layoutContract")).get("containerTree")))
    slots = [_dict(row) for row in _list(structure.get("slots")) if isinstance(row, dict)]
    if not slots:
        issues.append("formStructureContract.slots is required")
    slot_names: set[str] = set()
    referenced_fields: list[str] = []
    field_slots: dict[str, set[str]] = {}
    field_slot_counts: dict[tuple[str, str], int] = {}
    for index, slot in enumerate(slots):
        slot_name = _text(slot.get("slot") or slot.get("name"))
        if not slot_name:
            issues.append(f"formStructureContract.slots[{index}].slot is required")
        elif slot_name in slot_names:
            issues.append(f"duplicate formStructureContract slot: {slot_name}")
        else:
            slot_names.add(slot_name)
        slot_refs = _field_refs_from_structure_row(slot)
        referenced_fields.extend(slot_refs)
        for field_name in slot_refs:
            field_slots.setdefault(field_name, set()).add(slot_name)
            field_slot_counts[(field_name, slot_name)] = field_slot_counts.get((field_name, slot_name), 0) + 1

    field_roles = _dict(structure.get("fieldRoles") or structure.get("field_roles"))
    governance_field_names = {
        _text(item)
        for item in _list(governance_source.get("field_names") or governance_source.get("fieldNames"))
        if _text(item)
    }
    for field_name, role in field_roles.items():
        name = _text(field_name)
        role_dict = _dict(role)
        if not name:
            issues.append("formStructureContract.fieldRoles contains blank field name")
            continue
        if known_fields and name not in known_fields:
            issues.append(f"formStructureContract.fieldRoles.{name} references unknown field")
        role_slot = _text(role_dict.get("slot"))
        if role_slot and slot_names and role_slot not in slot_names:
            issues.append(f"formStructureContract.fieldRoles.{name}.slot references unknown slot {role_slot}")

    seen_fields: set[str] = set()
    duplicate_fields: set[str] = set()
    for name in referenced_fields:
        if known_fields and name not in known_fields:
            issues.append(f"formStructureContract references unknown field: {name}")
        if name not in governance_field_names and _is_form_structure_internal_field(name):
            issues.append(f"formStructureContract references internal field: {name}")
        duplicate_allowed_as_overview_summary = (
            "overview" in field_slots.get(name, set())
            and len(field_slots.get(name, set()) - {"overview"}) == 1
            and all(count == 1 for (field_name, _slot), count in field_slot_counts.items() if field_name == name)
        )
        if name in seen_fields and not duplicate_allowed_as_overview_summary:
            duplicate_fields.add(name)
        seen_fields.add(name)
    for name in sorted(duplicate_fields):
        issues.append(f"formStructureContract references field more than once: {name}")

    layout_fields = _collect_layout_field_names(_list(_dict(contract.get("layoutContract")).get("containerTree")))
    for name in referenced_fields:
        if layout_fields and name not in layout_fields:
            issues.append(f"formStructureContract field not projected to layout: {name}")
    if governance_field_names:
        for name in sorted(set(referenced_fields) - governance_field_names):
            issues.append(f"formStructureContract references field outside governance: {name}")
    if layout_fields:
        allowed_layout_fields = set(referenced_fields)
        for name in sorted(layout_fields - allowed_layout_fields):
            if _is_form_structure_runtime_control_field(name):
                continue
            issues.append(f"formStructureContract layout projects field outside structure: {name}")
    return issues


def _is_form_structure_runtime_control_field(name: str) -> bool:
    if not name:
        return False
    control_fields = {
        "can_review",
        "hide_reviews",
        "need_validation",
        "next_review",
        "reviewer_ids",
        "validation_status",
    }
    control_prefixes = (
        "can_",
        "allow_",
        "has_",
        "hide_",
        "need_",
    )
    control_suffixes = (
        "_count",
    )
    return (
        name in control_fields
        or any(name.startswith(prefix) for prefix in control_prefixes)
        or any(name.endswith(suffix) for suffix in control_suffixes)
    )


def _is_form_structure_internal_field(name: str) -> bool:
    if not name:
        return False
    allowed_legacy_fields = {
        "legacy_document_no",
        "legacy_contract_no",
        "legacy_status",
    }
    if name in allowed_legacy_fields:
        return False
    internal_fields = {
        "active",
        "archived",
        "color",
        "can_review",
        "entry_data",
        "has_comment",
        "has_message",
        "hide_reviews",
        "is_favorite",
        "is_locked",
        "my_activity_date_deadline",
        "name_short",
        "need_validation",
        "next_review",
        "sequence",
        "source_origin",
        "task_properties",
        "reject_reason",
        "rejected",
        "rejected_message",
        "review_ids",
        "reviewer_ids",
        "to_validate_message",
        "validated",
        "validated_message",
        "validation_status",
    }
    internal_prefixes = (
        "access_",
        "alias_",
        "allow_",
        "dashboard_",
        "favorite_",
        "last_update_",
        "privacy_",
    )
    internal_tokens = (
        "_delta",
        "_source",
        "_source_",
        "_visible",
        "legacy_",
        "source_created",
        "validation",
    )
    internal_suffixes = (
        "_count",
        "_rate",
    )
    return (
        name in internal_fields
        or any(name.startswith(prefix) for prefix in internal_prefixes)
        or any(token in name for token in internal_tokens)
        or any(name.endswith(suffix) for suffix in internal_suffixes)
    )


def _field_refs_from_structure_row(row: dict[str, Any]) -> list[str]:
    refs = [_text(item) for item in _list(row.get("fieldRefs") or row.get("field_refs") or row.get("fields"))]
    out = [name for name in refs if name]
    for group in _list(row.get("groups")):
        if isinstance(group, dict):
            out.extend(_field_refs_from_structure_row(group))
    return out


def _collect_layout_field_names(rows: list[Any]) -> set[str]:
    out: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _text(row.get("type") or row.get("kind")).lower() == "field":
            name = _text(row.get("name") or row.get("fieldCode") or row.get("field_code"))
            if name:
                out.add(name)
        for widget in _list(row.get("widgetList") or row.get("widget_list")):
            widget_dict = _dict(widget)
            name = _text(widget_dict.get("fieldCode") or widget_dict.get("field_code"))
            if name:
                out.add(name)
        for key in ("children", "pages", "tabs", "nodes", "items"):
            out.update(_collect_layout_field_names(_list(row.get(key))))
    return out


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
