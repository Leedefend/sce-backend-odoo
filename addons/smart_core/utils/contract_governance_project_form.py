# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def normalize_legacy_project_form_profile(profile: dict, *, default_max_fields: int) -> dict[str, Any]:
    max_fields = int(profile.get("max_fields") or default_max_fields)
    return {
        "primary_fields": [
            _safe_text(name)
            for name in (profile.get("primary_fields") or [])
            if _safe_text(name)
        ],
        "create_hidden_fields": [
            _safe_text(name)
            for name in (profile.get("create_hidden_fields") or [])
            if _safe_text(name)
        ],
        "action_priorities": [
            _safe_text(name)
            for name in (profile.get("action_priorities") or [])
            if _safe_text(name)
        ],
        "action_noise_markers": [
            _safe_lower(name)
            for name in (profile.get("action_noise_markers") or [])
            if _safe_text(name)
        ],
        "search_noise_markers": [
            _safe_lower(name)
            for name in (profile.get("search_noise_markers") or [])
            if _safe_text(name)
        ],
        "action_group_labels": {
            _safe_text(key): _safe_text(value)
            for key, value in _as_dict(profile.get("action_group_labels")).items()
            if _safe_text(key) and _safe_text(value)
        },
        "max_fields": max_fields if max_fields > 0 else default_max_fields,
    }


def pick_project_form_fields(
    data: dict,
    *,
    profile: dict,
    iter_field_order: Any,
    is_technical_field: Any,
    default_max_fields: int,
) -> list[str]:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return []
    primary_fields = profile.get("primary_fields") or []
    max_fields = int(profile.get("max_fields") or default_max_fields)
    ordered_fields = iter_field_order(data)

    def _collect_page_fields(nodes: list, current_page: str = "", out: list[str] | None = None) -> list[str]:
        collected = out or []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = _safe_lower(node.get("type") or node.get("kind"))
            page_name = current_page
            if node_type == "page":
                page_name = _safe_text(node.get("name") or node.get("label") or node.get("string"))
            if node_type == "field" and page_name:
                name = _safe_text(node.get("name"))
                descriptor = _as_dict(fields_map.get(name))
                if name and descriptor and not is_technical_field(name, descriptor) and name not in collected:
                    collected.append(name)
            for key in ("children", "tabs", "pages", "nodes", "items"):
                candidate = node.get(key)
                if isinstance(candidate, list):
                    _collect_page_fields(candidate, page_name, collected)
        return collected

    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    page_fields = _collect_page_fields(layout if isinstance(layout, list) else [])

    selected: list[str] = []
    for name in primary_fields:
        descriptor = _as_dict(fields_map.get(name))
        if descriptor and not is_technical_field(name, descriptor) and name not in selected:
            selected.append(name)

    for name in page_fields:
        if len(selected) >= max_fields:
            break
        if name not in selected:
            selected.append(name)

    for name in ordered_fields:
        if len(selected) >= max_fields:
            break
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor or is_technical_field(name, descriptor):
            continue
        if name not in selected:
            selected.append(name)

    for name, descriptor_raw in fields_map.items():
        if len(selected) >= max_fields:
            break
        descriptor = _as_dict(descriptor_raw)
        if is_technical_field(name, descriptor):
            continue
        required = bool(descriptor.get("required"))
        readonly = bool(descriptor.get("readonly"))
        if required and not readonly and name not in selected:
            selected.append(name)

    if "name" in fields_map and "name" not in selected:
        selected.insert(0, "name")
    return selected[:max_fields]


def govern_project_kanban_contract(
    data: dict,
    *,
    primary_model: str,
    registered_profile: dict,
    registered_row_actions: list[dict],
    is_technical_field: Any,
    deep_clone_json_like: Any,
) -> None:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return

    available = [name for name in fields_map.keys() if not is_technical_field(name, _as_dict(fields_map.get(name)))]
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
            and not is_technical_field(normalized, descriptor)
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
            and not is_technical_field(normalized, descriptor)
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
    for action in registered_row_actions:
        action_key = _safe_text(action.get("key") or action.get("name"))
        if not action_key or action_key in existing_keys:
            continue
        row_actions.append(deep_clone_json_like(action))
        existing_keys.add(action_key)
    kanban["row_actions"] = row_actions
    views["kanban"] = kanban
    data["views"] = views


def filter_project_form_layout(data: dict, selected_fields: list[str], *, profile: dict) -> None:
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
        primary_fields = profile.get("primary_fields") or []
        for name in primary_fields:
            if name in selected_fields:
                filtered_layout.append({"type": "field", "name": name})
        _collect_layout_field_names(filtered_layout, existing_field_names)

    existing_set = set(existing_field_names)
    missing_selected = [name for name in selected_order if name and name not in existing_set]
    for name in missing_selected:
        filtered_layout.append({"type": "field", "name": name})
    form["layout"] = filtered_layout
    views["form"] = form
    data["views"] = views


def trim_contract_field_maps(data: dict, selected_fields: list[str]) -> None:
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


def govern_project_form_search(data: dict, *, profile: dict) -> None:
    search = _as_dict(data.get("search"))
    filters = search.get("filters")
    if not isinstance(filters, list):
        return
    noise_markers = profile.get("search_noise_markers") or []
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


def action_priority(action: dict, *, profile: dict) -> int:
    label = _safe_text(action.get("label"))
    priorities = profile.get("action_priorities") or []
    for idx, key in enumerate(priorities):
        if key and key in label:
            return idx
    return len(priorities) + 1


def is_noisy_project_action(action: dict, *, profile: dict) -> bool:
    key = _safe_lower(action.get("key"))
    label = _safe_lower(action.get("label"))
    if not label and not key:
        return True
    if label.isdigit():
        return True
    markers = profile.get("action_noise_markers") or []
    for marker in markers:
        if marker in key or marker in label:
            return True
    return False


def classify_project_action_group(action: dict) -> str:
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


def build_project_action_groups(
    rows: list[dict],
    *,
    profile: dict,
    default_group_labels: dict[str, str],
    action_group_limit: int,
) -> list[dict]:
    grouped: dict[str, list[dict]] = {"basic": [], "workflow": [], "drilldown": [], "other": []}
    for row in rows:
        if not isinstance(row, dict):
            continue
        group_key = classify_project_action_group(row)
        grouped.setdefault(group_key, []).append(row)

    result: list[dict] = []
    group_labels = dict(default_group_labels)
    group_labels.update(profile.get("action_group_labels") or {})
    for key in ("basic", "workflow", "drilldown", "other"):
        actions = grouped.get(key) or []
        if not actions:
            continue
        primary = actions[:action_group_limit]
        overflow = actions[action_group_limit:]
        result.append({
            "key": key,
            "label": group_labels.get(key, key),
            "actions": primary,
            "overflow_actions": overflow,
            "overflow_count": len(overflow),
        })
    return result


def emit_scene_action_semantics(data: dict, *, header_rows: list[dict], record_rows: list[dict]) -> None:
    semantic_page = _as_dict(data.get("semantic_page"))
    actions = _as_dict(semantic_page.get("actions"))
    actions["header_actions"] = [dict(row) for row in header_rows if isinstance(row, dict)]
    actions["record_actions"] = [dict(row) for row in record_rows if isinstance(row, dict)]
    actions.setdefault("toolbar_actions", [])
    actions["owner_layer"] = "scene_orchestration"
    actions["source"] = "contract_governance.curated_action_facts"
    semantic_page["actions"] = actions
    data["semantic_page"] = semantic_page


def govern_project_form_actions(
    data: dict,
    *,
    profile: dict,
    default_group_labels: dict[str, str],
    action_group_limit: int,
    header_action_max: int,
    smart_action_max: int,
) -> None:
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
        if is_noisy_project_action(row, profile=profile):
            continue
        level = _safe_lower(row.get("level"))
        if level == "header":
            header_rows.append(row)
        elif level in {"smart", "row"}:
            smart_rows.append(row)

    header_rows = sorted(header_rows, key=lambda item: (action_priority(item, profile=profile), _safe_text(item.get("label"))))
    smart_rows = sorted(smart_rows, key=lambda item: (action_priority(item, profile=profile), _safe_text(item.get("label"))))
    curated = header_rows[:header_action_max] + smart_rows[:smart_action_max]
    data["buttons"] = curated
    emit_scene_action_semantics(
        data,
        header_rows=header_rows[:header_action_max],
        record_rows=smart_rows[:smart_action_max],
    )
    data["action_groups"] = build_project_action_groups(
        curated,
        profile=profile,
        default_group_labels=default_group_labels,
        action_group_limit=action_group_limit,
    )


def govern_project_form_contract(
    data: dict,
    *,
    selected_fields: list[str],
    profile: dict,
    collect_layout_field_names: Any,
    backfill_form_layout_from_visible_fields: Any,
    govern_project_form_search: Any,
    build_project_lifecycle_summary: Any,
    realign_access_policy_with_visible_fields: Any,
    default_max_fields: int,
    default_group_labels: dict[str, str],
    action_group_limit: int,
    header_action_max: int,
    smart_action_max: int,
) -> None:
    trim_contract_field_maps(data, selected_fields)
    data["visible_fields"] = selected_fields
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    native_layout_fields = collect_layout_field_names(form.get("layout"))
    if not native_layout_fields:
        backfill_form_layout_from_visible_fields(data)
    data["form_profile"] = {
        "core_fields": selected_fields[:8],
        "advanced_fields": selected_fields[8:],
        "max_fields": int(profile.get("max_fields") or default_max_fields),
    }
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

    govern_project_form_actions(
        data,
        profile=profile,
        default_group_labels=default_group_labels,
        action_group_limit=action_group_limit,
        header_action_max=header_action_max,
        smart_action_max=smart_action_max,
    )
    govern_project_form_search(data)
    build_project_lifecycle_summary(data)
    realign_access_policy_with_visible_fields(data)


def govern_project_task_form(
    data: dict,
    *,
    profile: dict,
    make_labeled_field_node: Any,
) -> None:
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
                        make_labeled_field_node(name, fields_map, label_map)
                        for name in selected
                        if name not in description_fields
                    ],
                },
                {
                    "type": "group",
                    "name": "project_task_description_group",
                    "string": description_group_label,
                    "children": [
                        make_labeled_field_node(name, fields_map, label_map)
                        for name in selected
                        if name in description_fields
                    ],
                },
            ],
        }
    ]
    views["form"] = form
    data["views"] = views


def build_project_lifecycle_summary(data: dict) -> None:
    workflow = _as_dict(data.get("workflow"))
    states = workflow.get("states")
    transitions = workflow.get("transitions")
    if not isinstance(states, list):
        states = []
    if not isinstance(transitions, list):
        transitions = []

    state_keys = []
    for row in states:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        label = _safe_text(row.get("label"), key)
        if not key:
            continue
        state_keys.append({"key": key, "label": label})

    transition_rows = []
    for row in transitions:
        if not isinstance(row, dict):
            continue
        trigger = _as_dict(row.get("trigger"))
        label = _safe_text(trigger.get("label") or trigger.get("name"))
        if not label:
            continue
        transition_rows.append({
            "label": label,
            "kind": _safe_text(trigger.get("kind")),
        })

    data["lifecycle"] = {
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "current_state": "",
        "steps": state_keys,
        "allowed_transitions": transition_rows[:8],
        "blockers": [],
        "progress_percent": 0 if state_keys else None,
    }
    data["workflow_surface"] = {
        "owner_layer": "business_fact",
        "source": "contract_governance.workflow_facts",
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "states": state_keys,
        "transitions": transitions[:8],
        "highlight_states": workflow.get("highlight_states") if isinstance(workflow.get("highlight_states"), list) else [],
    }
