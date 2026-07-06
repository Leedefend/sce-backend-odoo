# -*- coding: utf-8 -*-
"""Contract-backed form field configuration intents."""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET

from odoo.exceptions import ValidationError

from ..core.base_handler import BaseIntentHandler
from ..core.request_params import parse_non_negative_int
from ..utils.backend_contract_boundaries import (
    BUSINESS_CONFIG_INTENTS,
    FORM_FIELD_CONFIG_INTENTS,
    LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
    VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY,
    VIEW_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
    ensure_view_orchestration_source,
)
from ..utils.reason_codes import REASON_MISSING_PARAMS, REASON_NOT_FOUND, REASON_OK, REASON_USER_ERROR, REASON_WRITE_FAILED

BUSINESS_CONFIG_ADMIN_GROUP = "smart_core.group_smart_core_business_config_admin"
_logger = logging.getLogger(__name__)
_FORM_FIELD_LABEL_OVERRIDES: dict[tuple[str, str], str] = {}
BUSINESS_CONFIG_CONTRACT_AUTHORITIES = ("ui.business.config.contract", "ui.business.config.contract.version")
LOWCODE_BUSINESS_FIELD_TYPES = {
    "boolean",
    "char",
    "date",
    "datetime",
    "float",
    "html",
    "integer",
    "many2one",
    "monetary",
    "selection",
    "text",
}
LOWCODE_TECHNICAL_FIELD_NAMES = {
    "access_instruction_message",
    "access_token",
    "access_url",
    "access_warning",
    "activity_exception_decoration",
    "activity_exception_icon",
    "activity_ids",
    "activity_state",
    "activity_summary",
    "activity_type_icon",
    "activity_type_id",
    "activity_user_id",
    "activity_date_deadline",
    "alias_bounced_content",
    "alias_contact",
    "alias_defaults",
    "alias_domain",
    "alias_domain_id",
    "alias_email",
    "alias_force_thread_id",
    "alias_id",
    "alias_name",
    "alias_parent_model_id",
    "alias_parent_thread_id",
    "alias_status",
    "alias_user_id",
    "message_attachment_count",
    "message_bounce",
    "message_channel_ids",
    "message_follower_ids",
    "message_has_error",
    "message_has_error_counter",
    "message_has_sms_error",
    "message_ids",
    "message_is_follower",
    "message_main_attachment_id",
    "message_needaction",
    "message_needaction_counter",
    "message_partner_ids",
    "message_unread",
    "message_unread_counter",
    "my_activity_date_deadline",
    "rating_ids",
    "rating_last_feedback",
    "rating_last_image",
    "rating_last_value",
    "rating_percentage_satisfaction",
    "rating_status",
    "rating_status_period",
    "website_message_ids",
}
LOWCODE_TECHNICAL_FIELD_PREFIXES = (
    "activity_",
    "alias_",
    "message_",
    "rating_",
    "website_",
    "legacy_source_",
)
LOWCODE_TECHNICAL_FIELD_LABEL_KEYWORDS = (
    "access",
    "activity",
    "alias",
    "bounce",
    "bounced",
    "followers",
    "message",
    "milestones",
    "portal",
    "project manager",
    "rating",
    "security token",
    "task dependencies",
)


def _optional_non_negative_int(params: dict, *keys: str):
    raw = None
    for key in keys:
        if key in params:
            raw = params.get(key)
            break
    value, error = parse_non_negative_int(raw, allow_empty=True)
    if error:
        return None, keys[0]
    return int(value or 0), None


def _has_param(params: dict, *keys: str) -> bool:
    return any(key in params for key in keys)


def register_form_field_label_override(model_name: str, field_name: str, label: str) -> None:
    model = str(model_name or "").strip()
    field = str(field_name or "").strip()
    clean_label = str(label or "").strip()
    if model and field and clean_label:
        _FORM_FIELD_LABEL_OVERRIDES[(model, field)] = clean_label


def _form_field_label_override(model_name: str, field_name: str) -> str:
    return _FORM_FIELD_LABEL_OVERRIDES.get((str(model_name or "").strip(), str(field_name or "").strip()), "")


def _is_lowcode_business_field_candidate(field_name: str, field_type: str, label: str = "") -> bool:
    name = str(field_name or "").strip()
    normalized_type = str(field_type or "").strip()
    label_text = str(label or "").strip().lower()
    if not name:
        return False
    if name in LOWCODE_TECHNICAL_FIELD_NAMES:
        return False
    if name.startswith(LOWCODE_TECHNICAL_FIELD_PREFIXES):
        return False
    if normalized_type and normalized_type not in LOWCODE_BUSINESS_FIELD_TYPES:
        return False
    if any(keyword in label_text for keyword in LOWCODE_TECHNICAL_FIELD_LABEL_KEYWORDS):
        return False
    return True


def _available_lowcode_model_fields(env, model: str) -> list[dict]:
    Model = env[model]
    technical_prefixes = ("__",)
    technical_names = {"id", "display_name", "create_uid", "create_date", "write_uid", "write_date", "__last_update"}
    try:
        fields_meta = Model.sudo().fields_get() if hasattr(Model, "sudo") else Model.fields_get()
    except Exception:
        fields_meta = {}
    if not isinstance(fields_meta, dict) or not fields_meta:
        fields_meta = {
            name: {}
            for name in sorted(getattr(Model, "_fields", {}) or {})
        }
    out = []
    for name in sorted(fields_meta):
        field_name = str(name or "").strip()
        if not field_name or field_name in technical_names or field_name.startswith(technical_prefixes):
            continue
        meta = fields_meta.get(name) if isinstance(fields_meta.get(name), dict) else {}
        field_type = str(meta.get("type") or getattr((getattr(Model, "_fields", {}) or {}).get(name), "type", "") or "").strip()
        label = str(meta.get("string") or getattr((getattr(Model, "_fields", {}) or {}).get(name), "string", "") or field_name).strip()
        if not _is_lowcode_business_field_candidate(field_name, field_type, label):
            continue
        out.append({
            "name": field_name,
            "label": label or field_name,
            "type": field_type or "unknown",
        })
    return out


def _clean_lowcode_user_label(field_name: str, label: str) -> str:
    name = str(field_name or "").strip()
    text = str(label or name or "").strip()
    if name.startswith("p1_visible_") and text.startswith("P1可见"):
        text = text[len("P1可见"):].strip()
    return text or name


def _lowcode_business_field_name_set(env, model: str) -> set[str]:
    return {item["name"] for item in _available_lowcode_model_fields(env, model)}


def _normalize_view_type_scope(view_type: str | None) -> str:
    normalized = str(view_type or "").strip()
    return "tree" if normalized == "list" else normalized


def _reject_legacy_role_group_scope(params: dict):
    return "role_group_ids" if _has_param(params, "role_group_ids", "roleGroupIds") else None


def _append_business_config_scope_domain(params: dict, domain: list, *, include_status: bool = False):
    legacy_role_scope = _reject_legacy_role_group_scope(params)
    if legacy_role_scope:
        return legacy_role_scope
    view_type = _normalize_view_type_scope(params.get("view_type") or params.get("viewType"))
    role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
    if view_type:
        domain.append(("view_type", "in", [False, view_type]))
    if _has_param(params, "action_id", "actionId"):
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return invalid_field
        domain.append(("action_id", "=", action_id or False))
    if _has_param(params, "view_id", "viewId"):
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return invalid_field
        domain.append(("view_id", "=", view_id or False))
    if role_key:
        domain.append(("role_key", "=", role_key))
    if include_status:
        status = str(params.get("status") or "").strip()
        if status:
            domain.append(("status", "=", status))
    return None


def _business_config_contract_name(model: str, view_type: str, action_id: int | None, view_id: int | None) -> str:
    return "view_orchestration:%s:%s:action:%s:view:%s" % (
        model,
        view_type or "all",
        int(action_id or 0),
        int(view_id or 0),
    )


def _contract_reload_hint(*, model: str = "", view_type: str = "", action_id: int | None = None, view_id: int | None = None, role_key: str = "", version_no: int | None = None) -> dict:
    return {
        "required": True,
        "reason": "view_orchestration_config_changed",
        "model": str(model or ""),
        "view_type": _normalize_view_type_scope(view_type) or "form",
        "action_id": int(action_id or 0),
        "view_id": int(view_id or 0),
        "role_key": str(role_key or ""),
        "orchestration_version": str(version_no or ""),
    }


def _contract_reload_hint_for_record(rec) -> dict:
    return _contract_reload_hint(
        model=str(rec.model or ""),
        view_type=str(rec.view_type or ""),
        action_id=int(rec.action_id.id or 0),
        view_id=int(rec.view_id.id or 0),
        role_key=str(rec.role_key or ""),
        version_no=int(rec.version_no or 1),
    )


def _custom_field_metadata_boundary() -> dict:
    return {
        "metadata_authority": "ir.model.fields",
        "placement_authority": "ui.business.config.contract.view_orchestration",
        "compatibility_write": "ui.form.field.policy",
        "rollback_boundary": "contract_rollback_does_not_delete_model_field",
    }


def _view_orchestration_field_names(contract_json: dict, view_type: str = "form") -> list[str]:
    payload = contract_json if isinstance(contract_json, dict) else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    normalized_view_type = _normalize_view_type_scope(view_type) or "form"
    spec = views.get(normalized_view_type)
    if not isinstance(spec, dict) and normalized_view_type == "tree":
        spec = views.get("list")
    if not isinstance(spec, dict):
        return []
    rows = spec.get("fields") if normalized_view_type == "form" else spec.get("columns")
    if not isinstance(rows, list):
        rows = spec.get("fields") if isinstance(spec.get("fields"), list) else []
    names = []
    for row in rows:
        if _view_orchestration_row_hidden(row):
            continue
        if isinstance(row, str):
            name = row.strip()
        elif isinstance(row, dict):
            name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
        else:
            name = ""
        if name and name not in names:
            names.append(name)
    return names


def _view_orchestration_row_hidden(row) -> bool:
    if not isinstance(row, dict):
        return False

    def truthy(value) -> bool:
        if value is True or value == 1:
            return True
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "hide", "hidden"}
        return False

    if row.get("visible") is False:
        return True
    if truthy(row.get("invisible")) or truthy(row.get("column_invisible")):
        return True
    attrs = row.get("attrs") if isinstance(row.get("attrs"), dict) else {}
    modifiers = row.get("modifiers") if isinstance(row.get("modifiers"), dict) else {}
    attributes = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
    attribute_modifiers = attributes.get("modifiers") if isinstance(attributes.get("modifiers"), dict) else {}
    if any(
        truthy(value)
        for value in (
            attrs.get("invisible"),
            attrs.get("column_invisible"),
            modifiers.get("invisible"),
            modifiers.get("column_invisible"),
            attributes.get("invisible"),
            attributes.get("column_invisible"),
            attribute_modifiers.get("invisible"),
            attribute_modifiers.get("column_invisible"),
        )
    ):
        return True
    label = str(row.get("label") or row.get("string") or "").strip()
    return label.upper().endswith("_HIDDEN")


def _collect_view_orchestration_layout_field_names(value) -> list[str]:
    names = []

    def visit(node):
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        if not isinstance(node, dict):
            return
        node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
        field_name = str(node.get("name") or node.get("field") or "").strip()
        if node_type == "field" and field_name and field_name not in names:
            names.append(field_name)
        for child_key in ("children", "pages", "tabs", "nodes", "items"):
            children = node.get(child_key)
            if isinstance(children, list):
                visit(children)

    visit(value)
    return names


def _view_orchestration_form_layout_fields(contract_json: dict) -> list[str]:
    payload = contract_json if isinstance(contract_json, dict) else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    form_spec = views.get("form") if isinstance(views.get("form"), dict) else {}
    layout = form_spec.get("layout") if isinstance(form_spec.get("layout"), list) else []
    return _collect_view_orchestration_layout_field_names(layout)


def _view_orchestration_field_labels(contract_json: dict, view_type: str = "form") -> list[str]:
    labels_by_name = _view_orchestration_field_label_map(contract_json, view_type)
    return [
        f"{name}:{label or name}"
        for name, label in labels_by_name.items()
        if name
    ]


def _view_orchestration_field_label_map(contract_json: dict, view_type: str = "form") -> dict[str, str]:
    payload = contract_json if isinstance(contract_json, dict) else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    normalized_view_type = _normalize_view_type_scope(view_type) or "form"
    spec = views.get(normalized_view_type)
    if not isinstance(spec, dict) and normalized_view_type == "tree":
        spec = views.get("list")
    if not isinstance(spec, dict):
        return {}
    rows = spec.get("fields") if normalized_view_type == "form" else spec.get("columns")
    if not isinstance(rows, list):
        rows = spec.get("fields") if isinstance(spec.get("fields"), list) else []
    labels = {}
    for row in rows:
        if _view_orchestration_row_hidden(row):
            continue
        if isinstance(row, str):
            name = row.strip()
            label = name
        elif isinstance(row, dict):
            name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
            label = str(row.get("label") or row.get("string") or name).strip()
        else:
            name = ""
            label = ""
        if name and name not in labels:
            labels[name] = label or name
    return labels


def _view_orchestration_search_names(contract_json: dict, key: str) -> list[str]:
    payload = contract_json if isinstance(contract_json, dict) else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    spec = views.get("search")
    if not isinstance(spec, dict):
        return []
    rows = spec.get(key) if isinstance(spec.get(key), list) else []
    names = []
    for row in rows:
        if isinstance(row, str):
            name = row.strip()
        elif isinstance(row, dict):
            name = str(row.get("field") or row.get("name") or row.get("group_by") or row.get("groupBy") or "").strip()
        else:
            name = ""
        if name and name not in names:
            names.append(name)
    return names


def _sanitize_config_name_list(value) -> list[str]:
    rows = value if isinstance(value, list) else []
    names = []
    for item in rows:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("field") or item.get("field_name") or item.get("group_by") or "").strip()
        else:
            name = ""
        if name and name not in names:
            names.append(name)
    return names


def _sanitize_layout_token(value) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if not re.match(r"^[A-Za-z0-9_.:-]{1,64}$", text):
        return ""
    return text


def _sanitize_field_string_map(value) -> dict[str, str]:
    rows = value if isinstance(value, dict) else {}
    return {
        str(name or "").strip(): _sanitize_layout_token(raw)
        for name, raw in rows.items()
        if str(name or "").strip() and _sanitize_layout_token(raw)
    }


def _sanitize_positive_int_map(value, *, minimum: int = 1, maximum: int = 4) -> dict[str, int]:
    rows = value if isinstance(value, dict) else {}
    out: dict[str, int] = {}
    for name, raw in rows.items():
        key = str(name or "").strip()
        if not key:
            continue
        try:
            number = int(raw)
        except (TypeError, ValueError):
            continue
        if minimum <= number <= maximum:
            out[key] = number
    return out


def _sanitize_bool_map(value) -> dict[str, bool]:
    rows = value if isinstance(value, dict) else {}
    out: dict[str, bool] = {}
    for name, raw in rows.items():
        key = str(name or "").strip()
        if not key:
            continue
        out[key] = str(raw).strip().lower() not in {"0", "false", "no", "hide", "hidden"}
    return out


def _normalize_form_column_count(value) -> int:
    try:
        columns = int(value)
    except (TypeError, ValueError):
        return 0
    return columns if 1 <= columns <= 4 else 0


def _business_config_view_orchestration_payload(
    *,
    view_type: str,
    names: list[str],
    existing: dict | None = None,
    search_key: str = "filters",
) -> dict:
    payload = dict(existing or {})
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    normalized_view_type = _normalize_view_type_scope(view_type)
    spec = dict(views.get(normalized_view_type) or {})
    if normalized_view_type == "tree":
        spec["columns"] = [{"name": name, "sequence": (idx + 1) * 10} for idx, name in enumerate(names)]
    elif normalized_view_type == "search":
        target_key = "group_by" if search_key == "group_by" else "filters"
        spec[target_key] = [{"field": name, "sequence": (idx + 1) * 10} for idx, name in enumerate(names)]
    views[normalized_view_type] = spec
    orchestration["views"] = views
    payload["view_orchestration"] = orchestration
    return payload


def _business_config_contract_summary(contract_json: dict) -> dict:
    payload = contract_json if isinstance(contract_json, dict) else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    form_fields = _view_orchestration_field_names(payload, "form")
    form_field_labels = _view_orchestration_field_labels(payload, "form")
    tree_columns = _view_orchestration_field_names(payload, "tree")
    search_filters = _view_orchestration_search_names(payload, "filters")
    search_group_by = _view_orchestration_search_names(payload, "group_by")
    analysis_items = _view_orchestration_analysis_names(views)
    return {
        "view_types": sorted(str(key) for key in views if str(key or "").strip()),
        "form_field_count": len(form_fields),
        "list_column_count": len(tree_columns),
        "search_filter_count": len(search_filters),
        "search_group_by_count": len(search_group_by),
        "analysis_item_count": len(analysis_items),
        "form_fields": form_fields,
        "form_field_labels": form_field_labels,
        "list_columns": tree_columns,
        "search_filters": search_filters,
        "search_group_by": search_group_by,
        "analysis_items": analysis_items,
    }


def _analysis_item_name(value, fallback_prefix: str = "") -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("field") or value.get("intent") or value.get("type") or "").strip()
    text = str(value or "").strip()
    return f"{fallback_prefix}:{text}" if fallback_prefix and text else text


def _append_analysis_list_items(items: list[str], view_type: str, key: str, value):
    values = value if isinstance(value, list) else [value]
    for row in values:
        name = _analysis_item_name(row)
        if name:
            items.append(f"{view_type}.{key}.{name}")


def _append_analysis_mapping_items(items: list[str], view_type: str, key: str, value):
    if not isinstance(value, dict):
        return
    for slot, row in sorted(value.items()):
        rows = row if isinstance(row, list) else [row]
        for item in rows:
            name = _analysis_item_name(item)
            if name:
                items.append(f"{view_type}.{key}.{slot}.{name}")


def _view_orchestration_analysis_names(views: dict) -> list[str]:
    items: list[str] = []
    for view_type in ("pivot", "graph"):
        view = views.get(view_type) if isinstance(views.get(view_type), dict) else {}
        for key in ("measures", "dimensions"):
            _append_analysis_list_items(items, view_type, key, view.get(key) or [])
        for key in ("measure", "dimension", "type"):
            name = _analysis_item_name(view.get(key))
            if name:
                items.append(f"{view_type}.{key}.{name}")
    calendar = views.get("calendar") if isinstance(views.get("calendar"), dict) else {}
    for key in ("date_slots", "resource_slots", "color_slots"):
        _append_analysis_mapping_items(items, "calendar", key, calendar.get(key) or {})
    dashboard = views.get("dashboard") if isinstance(views.get("dashboard"), dict) else {}
    for key in ("metric_slots", "chart_slots", "navigation_slots"):
        _append_analysis_mapping_items(items, "dashboard", key, dashboard.get(key) or {})
    for key in ("cards", "kpis"):
        _append_analysis_list_items(items, "dashboard", key, dashboard.get(key) or [])
    return sorted(dict.fromkeys(items))


def _view_orchestration_analysis_config(contract_json: dict, view_type: str) -> dict:
    payload = contract_json if isinstance(contract_json, dict) else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    view = views.get(view_type) if isinstance(views.get(view_type), dict) else {}
    if view_type in {"pivot", "graph"}:
        measures = []
        dimensions = []
        for row in view.get("measures") if isinstance(view.get("measures"), list) else []:
            name = _analysis_item_name(row)
            if name and name not in measures:
                measures.append(name)
        for row in view.get("dimensions") if isinstance(view.get("dimensions"), list) else []:
            name = _analysis_item_name(row)
            if name and name not in dimensions:
                dimensions.append(name)
        scalar_measure = _analysis_item_name(view.get("measure"))
        scalar_dimension = _analysis_item_name(view.get("dimension"))
        if scalar_measure and scalar_measure not in measures:
            measures.insert(0, scalar_measure)
        if scalar_dimension and scalar_dimension not in dimensions:
            dimensions.insert(0, scalar_dimension)
        return {
            "measures": measures,
            "dimensions": dimensions,
            "type": str(view.get("type") or "").strip(),
        }
    return {}


def _view_orchestration_has_configured_view(view_orchestration: dict) -> bool:
    views = view_orchestration.get("views") if isinstance(view_orchestration.get("views"), dict) else {}
    if not views:
        return False
    for view_spec in views.values():
        if not isinstance(view_spec, dict):
            continue
        for value in view_spec.values():
            if isinstance(value, bool):
                return True
            if isinstance(value, (int, float)) and value:
                return True
            if isinstance(value, str) and value.strip():
                return True
            if isinstance(value, (list, tuple, set)) and len(value) > 0:
                return True
            if isinstance(value, dict) and len(value) > 0:
                return True
    return False


def _business_config_analysis_payload(*, view_type: str, measures: list[str], dimensions: list[str], chart_type: str = "") -> dict:
    sequence = lambda idx: (idx + 1) * 10
    spec = {
        "measures": [{"name": name, "sequence": sequence(idx)} for idx, name in enumerate(measures)],
        "dimensions": [{"name": name, "sequence": sequence(idx)} for idx, name in enumerate(dimensions)],
    }
    if measures:
        spec["measure"] = measures[0]
    if dimensions:
        spec["dimension"] = dimensions[0]
    if view_type == "graph":
        spec["type"] = chart_type or "bar"
    elif chart_type:
        spec["chart_policy"] = {"type": chart_type}
    return {
        "view_orchestration": {
            "views": {
                view_type: spec,
            },
            "context": {
                "source": "business_config_analysis_editor",
                "source_status": LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
            },
        }
    }


def _lowcode_view_orchestration_payload(payload: dict, *, source: str = VIEW_ORCHESTRATION_SOURCE_TENANT_LOWCODING) -> dict:
    return ensure_view_orchestration_source(payload, source)


def _lowcode_form_source_authority(handler) -> dict:
    return {
        "kind": handler.SOURCE_KIND,
        "authorities": list(handler.SOURCE_AUTHORITIES),
        "projection_only": True,
        "write_proxy": True,
        "no_business_fact_authority": True,
        "runtime_carrier": handler.INTENT_TYPE,
        "lowcode_boundary": "form_config",
        "contract_source": VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY,
    }


def _lowcode_contract_write_unavailable(env) -> bool:
    if "ui.business.config.contract" not in env:
        return True
    Contract = env["ui.business.config.contract"]
    return not all(hasattr(Contract, attr) for attr in ("sudo", "search", "create"))


def _lowcode_form_contract_write_error(handler, message: str, exc: Exception | None = None) -> dict:
    suffix = "：%s" % exc if exc is not None else ""
    return handler._err(500, "%s，已阻止兼容策略表单独生效%s" % (message, suffix), REASON_WRITE_FAILED)


def _lowcode_contract_write_failed_error(handler, exc: Exception) -> dict:
    return handler._err(500, "正式低代码契约写入失败：%s" % exc, REASON_WRITE_FAILED)


def _write_lowcode_form_contract_or_error(
    handler,
    *,
    model: str,
    action_id: int,
    view_id: int,
    rows: list[dict],
    form_columns: int = 0,
    group_columns: dict[str, int] | None = None,
    group_visibility: dict[str, bool] | None = None,
) -> tuple[int, dict | None]:
    if _lowcode_contract_write_unavailable(handler.env):
        return 0, _lowcode_form_contract_write_error(handler, "正式低代码契约不可写")
    try:
        count = _upsert_view_orchestration_field_rows(
            handler.env,
            model=model,
            view_type="form",
            action_id=action_id,
            view_id=view_id,
            rows=rows,
            form_columns=form_columns,
            group_columns=group_columns,
            group_visibility=group_visibility,
        )
    except Exception as exc:
        return 0, _lowcode_form_contract_write_error(handler, "正式低代码契约写入失败", exc)
    if count <= 0 and (rows or form_columns or group_columns or group_visibility):
        return 0, _lowcode_form_contract_write_error(handler, "正式低代码契约未写入")
    return count, None


def _search_published_view_orchestration_contracts(env, *, model: str, view_type: str, action_id: int = 0, view_id: int = 0, role_key: str = ""):
    if "ui.business.config.contract" not in env:
        return []
    Contract = env["ui.business.config.contract"]
    if hasattr(Contract, "sudo"):
        Contract = Contract.sudo()
    domain = [
        ("active", "=", True),
        ("status", "=", "published"),
        ("model", "=", model),
        ("view_type", "in", [False, _normalize_view_type_scope(view_type)]),
        ("company_id", "in", [False, env.company.id]),
        ("action_id", "in", [False, int(action_id or 0)]),
        ("view_id", "in", [False, int(view_id or 0)]),
        ("role_key", "in", [False, str(role_key or "").strip()]),
    ]
    try:
        return Contract.search(domain, order="priority, version_no, id")
    except TypeError:
        return Contract.search(domain)


def _upsert_view_orchestration_field_rows(
    env,
    *,
    model: str,
    view_type: str = "form",
    action_id: int | None = None,
    view_id: int | None = None,
    rows: list[dict] | None = None,
    form_columns: int = 0,
    group_columns: dict[str, int] | None = None,
    group_visibility: dict[str, bool] | None = None,
) -> int:
    if not rows and not form_columns and not group_columns and not group_visibility:
        return 0
    if "ui.business.config.contract" not in env:
        return 0
    Contract = env["ui.business.config.contract"].sudo()
    name = _business_config_contract_name(model, view_type, action_id, view_id)
    domain = [("name", "=", name), ("company_id", "=", env.company.id)]
    rec = Contract.search(domain, limit=1)
    payload = dict(rec.contract_json or {}) if rec else {}
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
    spec = views.get(view_type) if isinstance(views.get(view_type), dict) else {}
    normalized_form_columns = _normalize_form_column_count(form_columns)
    if normalized_form_columns:
        spec["columns"] = normalized_form_columns
    fields_rows = spec.get("fields") if isinstance(spec.get("fields"), list) else []
    layout_group_by_field: dict[str, str] = {}
    group_meta_by_title: dict[str, dict] = {}
    field_layout_meta_by_name: dict[str, dict] = {}
    sanitized_group_columns = dict(group_columns or {})
    sanitized_group_visibility = dict(group_visibility or {})

    def collect_layout_groups(nodes, group_title: str = "") -> None:
        for node in nodes if isinstance(nodes, list) else []:
            if not isinstance(node, dict):
                continue
            node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
            title = str(node.get("string") or node.get("label") or node.get("title") or "").strip()
            next_group = title if node_type == "group" and title else group_title
            if node_type == "group" and title:
                attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
                group_meta_by_title[title] = {
                    "visible": node.get("visible"),
                    "columns": node.get("columns") or node.get("cols") or attrs.get("columns") or attrs.get("cols"),
                }
            field_name = str(node.get("name") or node.get("field") or "").strip()
            if node_type == "field" and field_name and next_group:
                layout_group_by_field[field_name] = next_group
            if node_type == "field" and field_name:
                field_layout_meta_by_name[field_name] = {
                    "class": node.get("class") or node.get("className"),
                    "field_size": node.get("field_size") or node.get("fieldSize") or node.get("size"),
                }
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                collect_layout_groups(node.get(child_key), next_group)

    collect_layout_groups(spec.get("layout"))
    for section in spec.get("sections") if isinstance(spec.get("sections"), list) else []:
        if not isinstance(section, dict):
            continue
        title = str(section.get("title") or section.get("label") or section.get("name") or "").strip()
        if not title:
            continue
        current = group_meta_by_title.get(title, {})
        group_meta_by_title[title] = {
            "visible": current.get("visible") if current.get("visible") is not None else section.get("visible"),
            "columns": current.get("columns") or section.get("columns") or section.get("cols"),
        }
    for title, columns in sanitized_group_columns.items():
        group_title = str(title or "").strip()
        if not group_title:
            continue
        current = group_meta_by_title.get(group_title, {})
        group_meta_by_title[group_title] = {**current, "columns": columns}
    for title, visible in sanitized_group_visibility.items():
        group_title = str(title or "").strip()
        if not group_title:
            continue
        current = group_meta_by_title.get(group_title, {})
        group_meta_by_title[group_title] = {**current, "visible": bool(visible)}
    by_name = {
        str(row.get("name") or row.get("field") or row.get("field_name") or "").strip(): dict(row)
        for row in fields_rows
        if isinstance(row, dict) and str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
    }
    for row in rows:
        field_name = str((row or {}).get("name") or "").strip()
        if not field_name:
            continue
        current = by_name.get(field_name, {"name": field_name})
        for key in ("label", "visible", "sequence", "group_title", "class", "field_size", "width"):
            if key in row and row.get(key) is not None:
                current[key] = row.get(key)
        by_name[field_name] = current
    for field_name, current in by_name.items():
        if not str(current.get("group_title") or "").strip() and layout_group_by_field.get(field_name):
            current["group_title"] = layout_group_by_field[field_name]
        for key, value in field_layout_meta_by_name.get(field_name, {}).items():
            if value and not current.get(key):
                current[key] = value
    spec["fields"] = sorted(by_name.values(), key=lambda item: (int(item.get("sequence") or 100), str(item.get("name") or "")))
    grouped: dict[str, list[dict]] = {}
    for row in spec["fields"]:
        if not isinstance(row, dict):
            continue
        field_name = str(row.get("name") or row.get("field") or row.get("field_name") or "").strip()
        if not field_name or row.get("visible") is False:
            continue
        group_title = str(row.get("group_title") or "").strip()
        if not group_title:
            group_title = "业务配置字段"
        grouped.setdefault(group_title, []).append(row)
    if grouped:
        spec["sections"] = [
            {
                "name": "business_config_section_%s" % (index + 1),
                "title": title,
                **({"visible": group_meta_by_title.get(title, {}).get("visible")} if group_meta_by_title.get(title, {}).get("visible") is not None else {}),
                **({"columns": group_meta_by_title.get(title, {}).get("columns")} if group_meta_by_title.get(title, {}).get("columns") else {}),
                "sequence": (index + 1) * 10,
                "fields": [
                    str(item.get("name") or item.get("field") or item.get("field_name") or "").strip()
                    for item in sorted(items, key=lambda item: (int(item.get("sequence") or 100), str(item.get("name") or "")))
                    if str(item.get("name") or item.get("field") or item.get("field_name") or "").strip()
                ],
            }
            for index, (title, items) in enumerate(sorted(
                grouped.items(),
                key=lambda item: (min(int(row.get("sequence") or 100) for row in item[1]), item[0]),
            ))
        ]
        spec["layout"] = [
            {
                "type": "group",
                "string": title,
                **({"visible": group_meta_by_title.get(title, {}).get("visible")} if group_meta_by_title.get(title, {}).get("visible") is not None else {}),
                **({"columns": group_meta_by_title.get(title, {}).get("columns")} if group_meta_by_title.get(title, {}).get("columns") else {}),
                "children": [
                    {
                        "type": "field",
                        "name": str(item.get("name") or item.get("field") or item.get("field_name") or "").strip(),
                        **({"class": item.get("class")} if item.get("class") else {}),
                        **({"field_size": item.get("field_size")} if item.get("field_size") else {}),
                    }
                    for item in sorted(items, key=lambda item: (int(item.get("sequence") or 100), str(item.get("name") or "")))
                    if str(item.get("name") or item.get("field") or item.get("field_name") or "").strip()
                ],
            }
            for title, items in sorted(
                grouped.items(),
                key=lambda item: (min(int(row.get("sequence") or 100) for row in item[1]), item[0]),
            )
        ]
    elif group_meta_by_title:
        spec["sections"] = [
            {
                "name": "business_config_section_%s" % (index + 1),
                "title": title,
                **({"visible": meta.get("visible")} if meta.get("visible") is not None else {}),
                **({"columns": meta.get("columns")} if meta.get("columns") else {}),
                "sequence": (index + 1) * 10,
                "fields": [],
            }
            for index, (title, meta) in enumerate(sorted(group_meta_by_title.items()))
        ]
    views[view_type] = spec
    orchestration["views"] = views
    payload["view_orchestration"] = orchestration
    payload = _lowcode_view_orchestration_payload(payload, source=VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY)
    vals = {
        "name": name,
        "model": model,
        "view_type": view_type,
        "action_id": int(action_id or 0) or False,
        "view_id": int(view_id or 0) or False,
        "company_id": env.company.id,
        "contract_json": payload,
        "status": "published",
    }
    if rec:
        rec.write(vals)
    else:
        rec = Contract.create(vals)
    rec.action_publish()
    layout_changed = bool(normalized_form_columns or sanitized_group_columns or sanitized_group_visibility)
    return len(rows or []) or (1 if layout_changed else 0)


class FormFieldPolicySetHandler(BaseIntentHandler):
    INTENT_TYPE = FORM_FIELD_CONFIG_INTENTS["policy_set"]
    DESCRIPTION = "Set current form field visibility policy from a contract action."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_form_field_policy_contract_action"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        "ui.business.config.contract.version",
        "ui.form.field.policy",
        "ir.model.fields",
        "ir.actions.act_window",
        "ir.ui.view",
    )
    NON_IDEMPOTENT_ALLOWED = "field policy writes configuration state"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return _lowcode_form_source_authority(self)

    def _model_record(self, model_name: str):
        return self.env["ir.model"].search([("model", "=", model_name)], limit=1)

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        field_name = str(params.get("field_name") or params.get("fieldName") or "").strip()
        if not model or not field_name:
            return self._err(400, "缺少 model 或 field_name", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        if field_name not in self.env[model]._fields:
            return self._err(404, "字段不存在：%s.%s" % (model, field_name), REASON_NOT_FOUND)
        model_rec = self._model_record(model)
        if not model_rec or model_rec.transient:
            return self._err(400, "临时模型不能配置表单字段：%s" % model, REASON_USER_ERROR)
        field_rec = self.env["ir.model.fields"].search([("model", "=", model), ("name", "=", field_name)], limit=1)
        if field_rec and field_rec.ttype == "binary":
            return self._err(400, "二进制字段不能作为业务表单字段配置：%s.%s" % (model, field_name), REASON_USER_ERROR)

        raw_visible = params.get("visible")
        has_visible = "visible" in params
        label = str(params.get("label") or (field_rec.field_description if field_rec else field_name) or field_name).strip()
        group_title = str(params.get("group_title") or params.get("groupTitle") or "").strip()
        sequence, invalid_field = _optional_non_negative_int(params, "sequence")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)

        Policy = self.env["ui.form.field.policy"]
        Policy.check_access_rights("create")
        domain = [
            ("active", "=", True),
            ("model", "=", model),
            ("field_name", "=", field_name),
            ("company_id", "=", self.env.company.id),
            ("action_id", "=", action_id or False),
            ("view_id", "=", view_id or False),
        ]
        policy = Policy.search(domain, limit=1)
        visible = (
            str(raw_visible).strip().lower() not in {"0", "false", "no", "hide", "hidden"}
            if has_visible
            else (bool(policy.visible) if policy else True)
        )
        vals = {
            "active": True,
            "model_id": model_rec.id,
            "model": model,
            "field_id": field_rec.id if field_rec else False,
            "field_name": field_name,
            "label": label,
            "visible": bool(visible),
            "company_id": self.env.company.id,
            "action_id": action_id or False,
            "view_id": view_id or False,
        }
        if group_title:
            vals["group_title"] = group_title
        if sequence > 0:
            vals["sequence"] = sequence
        mirror_row = {
            "name": field_name,
            "label": label,
            "visible": bool(visible),
            "sequence": int(sequence or getattr(policy, "sequence", 0) or 100),
            **({"group_title": group_title} if group_title else {}),
        }
        mirrored_count, contract_error = _write_lowcode_form_contract_or_error(
            self,
            model=model,
            action_id=action_id,
            view_id=view_id,
            rows=[mirror_row],
        )
        if contract_error:
            return contract_error
        if policy:
            policy.check_access_rights("write")
            policy.write(vals)
        else:
            policy = Policy.create(vals)
        return {
            "ok": True,
            "data": {
                "id": int(policy.id),
                "model": model,
                "field_name": field_name,
                "visible": bool(policy.visible),
                "label": str(policy.label or ""),
                "group_title": str(policy.group_title or ""),
                "sequence": int(policy.sequence or 0),
                "business_config_mirrored_count": mirrored_count,
                "contract_reload": _contract_reload_hint(
                    model=model,
                    view_type="form",
                    action_id=action_id,
                    view_id=view_id,
                ),
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
        }


class FormCustomFieldCreateHandler(BaseIntentHandler):
    INTENT_TYPE = FORM_FIELD_CONFIG_INTENTS["custom_field_create"]
    DESCRIPTION = "Create a safe custom form field from a contract action."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_form_custom_field_contract_action"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        "ui.business.config.contract.version",
        "ui.form.custom.field.wizard",
        "ir.model.fields",
        "ui.form.field.policy",
    )
    NON_IDEMPOTENT_ALLOWED = "custom field creation changes configuration metadata"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return _lowcode_form_source_authority(self)

    def _suggest_field_name(self, model: str, label: str) -> str:
        ascii_slug = re.sub(r"[^a-z0-9_]+", "_", str(label or "").lower()).strip("_")
        if not ascii_slug or not re.match(r"^[a-z]", ascii_slug):
            ascii_slug = "custom_field"
        ascii_slug = re.sub(r"_+", "_", ascii_slug)[:40].strip("_") or "custom_field"
        base = "x_%s" % ascii_slug
        candidate = base
        index = 2
        Field = self.env["ir.model.fields"].sudo()
        while (
            candidate in self.env[model]._fields
            or Field.search_count([("model", "=", model), ("name", "=", candidate)])
        ):
            candidate = "%s_%s" % (base[:48], index)
            index += 1
            if index > 200:
                candidate = "%s_%s" % (base[:42], int(time.time()) % 100000)
                if (
                    candidate not in self.env[model]._fields
                    and not Field.search_count([("model", "=", model), ("name", "=", candidate)])
                ):
                    break
        return candidate[:56]

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        label = str(params.get("label") or "").strip()
        if not model or not label:
            return self._err(400, "缺少 model 或 label", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        sequence, invalid_field = _optional_non_negative_int(params, "sequence")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
        if not model_rec or model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        if model_rec.transient:
            return self._err(400, "临时模型不能新增业务字段：%s" % model, REASON_USER_ERROR)
        field_name = str(params.get("field_name") or params.get("fieldName") or "").strip()
        if not field_name or field_name in {"x_", "x_custom_field"}:
            field_name = self._suggest_field_name(model, label)
        Field = self.env["ir.model.fields"].sudo()
        if field_name in self.env[model]._fields or Field.search_count([("model", "=", model), ("name", "=", field_name)]):
            return self._err(400, "字段已存在：%s.%s" % (model, field_name), REASON_USER_ERROR)
        ttype = str(params.get("ttype") or "char").strip() or "char"
        group_title = str(params.get("group_title") or "业务配置字段").strip() or "业务配置字段"
        dry_run = params.get("dry_run") is True or params.get("dryRun") is True
        Wizard = self.env["ui.form.custom.field.wizard"]
        Wizard.check_access_rights("create")
        if dry_run:
            return {
                "ok": True,
                "data": {
                    "dry_run": True,
                    "would_create": True,
                    "model": model,
                    "field_name": field_name,
                    "label": label,
                    "ttype": ttype,
                    "group_title": group_title,
                    "sequence": sequence if sequence > 0 else 100,
                    "action_id": action_id,
                    "view_id": view_id,
                    "field_metadata_boundary": _custom_field_metadata_boundary(),
                },
                "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
            }
        wizard = Wizard.create({
            "model_id": model_rec.id,
            "field_name": field_name,
            "label": label,
            "ttype": ttype,
            "help": str(params.get("help") or "").strip(),
            "required": bool(params.get("required") is True),
            "index": bool(params.get("index") is True),
            "action_id": action_id or False,
            "view_id": view_id or False,
            "group_title": group_title,
            "sequence": sequence if sequence > 0 else 100,
            "active_policy": True,
            "company_id": self.env.company.id,
        })
        try:
            result = wizard.action_create_field_policy()
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        try:
            self.env.registry.signal_changes()
        except Exception:
            pass
        policy_id = int(result.get("res_id") or 0) if isinstance(result, dict) else 0
        policy = self.env["ui.form.field.policy"].browse(policy_id).exists() if policy_id else self.env["ui.form.field.policy"]
        effective_field_name = str(policy.field_name or wizard.field_name or field_name or "").strip()
        mirrored_count = _upsert_view_orchestration_field_rows(
            self.env,
            model=model,
            view_type="form",
            action_id=action_id,
            view_id=view_id,
            rows=[{
                "name": effective_field_name,
                "label": str(policy.label or label),
                "visible": True,
                "sequence": int(policy.sequence or sequence or 100),
            }],
        )
        return {
            "ok": True,
            "data": {
                "policy_id": int(policy.id or 0),
                "field_name": effective_field_name,
                "model": model,
                "business_config_mirrored_count": mirrored_count,
                "field_metadata_boundary": _custom_field_metadata_boundary(),
                "contract_reload": _contract_reload_hint(
                    model=model,
                    view_type="form",
                    action_id=action_id,
                    view_id=view_id,
                ),
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
        }


class FormFieldOrderSetHandler(BaseIntentHandler):
    INTENT_TYPE = FORM_FIELD_CONFIG_INTENTS["order_set"]
    DESCRIPTION = "Set form field order for current form scope from contract action."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_form_field_order_contract_action"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        "ui.business.config.contract.version",
        "ui.form.field.policy",
        "ir.model.fields",
        "ir.actions.act_window",
        "ir.ui.view",
    )
    NON_IDEMPOTENT_ALLOWED = "field order writes configuration state"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return _lowcode_form_source_authority(self)

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        raw_field_order = params.get("field_order") or params.get("fieldOrder")
        if not isinstance(raw_field_order, list) or not raw_field_order:
            return self._err(400, "field_order 必须是非空数组", REASON_USER_ERROR)
        field_order = [str(name or "").strip() for name in raw_field_order]
        field_order = [name for name in field_order if name]
        if not field_order:
            return self._err(400, "field_order 不能为空", REASON_USER_ERROR)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        unknown = [name for name in field_order if name not in self.env[model]._fields]
        if unknown:
            return self._err(404, "字段不存在：%s.%s" % (model, unknown[0]), REASON_NOT_FOUND)
        raw_field_groups = params.get("field_groups") or params.get("fieldGroups") or {}
        field_groups = {
            str(name or "").strip(): str(group_title or "").strip()
            for name, group_title in (raw_field_groups.items() if isinstance(raw_field_groups, dict) else [])
            if str(name or "").strip() and str(group_title or "").strip()
        }
        unknown_groups = [name for name in field_groups if name not in self.env[model]._fields]
        if unknown_groups:
            return self._err(404, "字段不存在：%s.%s" % (model, unknown_groups[0]), REASON_NOT_FOUND)
        model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
        if not model_rec or model_rec.transient:
            return self._err(400, "临时模型不能配置表单字段：%s" % model, REASON_USER_ERROR)

        Field = self.env["ir.model.fields"]
        field_rows = Field.search([("model", "=", model), ("name", "in", field_order)])
        field_map = {str(row.name or "").strip(): row for row in field_rows}
        Policy = self.env["ui.form.field.policy"]
        Policy.check_access_rights("create")
        policies = Policy.search([
            ("active", "=", True),
            ("model", "=", model),
            ("field_name", "in", field_order),
            ("company_id", "=", self.env.company.id),
            ("action_id", "=", action_id or False),
            ("view_id", "=", view_id or False),
        ])
        policy_map = {str(row.field_name or "").strip(): row for row in policies}
        mirror_rows = [
            {
                "name": field_name,
                "label": str((field_map.get(field_name).field_description if field_map.get(field_name) else field_name) or field_name),
                "visible": True,
                "sequence": (index + 1) * 10,
                **({"group_title": field_groups[field_name]} if field_groups.get(field_name) else {}),
            }
            for index, field_name in enumerate(field_order)
        ]
        mirrored_count, contract_error = _write_lowcode_form_contract_or_error(
            self,
            model=model,
            action_id=action_id,
            view_id=view_id,
            rows=mirror_rows,
        )
        if contract_error:
            return contract_error
        for index, field_name in enumerate(field_order):
            sequence = (index + 1) * 10
            policy = policy_map.get(field_name)
            group_title = field_groups.get(field_name)
            if policy:
                policy.check_access_rights("write")
                vals = {"sequence": sequence}
                if group_title:
                    vals["group_title"] = group_title
                policy.write(vals)
                continue
            field_rec = field_map.get(field_name)
            label = str((field_rec.field_description if field_rec else field_name) or field_name).strip()
            vals = {
                "active": True,
                "model_id": model_rec.id,
                "model": model,
                "field_id": field_rec.id if field_rec else False,
                "field_name": field_name,
                "label": label,
                "visible": True,
                "sequence": sequence,
                "company_id": self.env.company.id,
                "action_id": action_id or False,
                "view_id": view_id or False,
            }
            if group_title:
                vals["group_title"] = group_title
            Policy.create(vals)
        return {
            "ok": True,
            "data": {
                "model": model,
                "field_order": field_order,
                "updated_count": len(field_order),
                "business_config_mirrored_count": mirrored_count,
                "contract_reload": _contract_reload_hint(
                    model=model,
                    view_type="form",
                    action_id=action_id,
                    view_id=view_id,
                ),
            },
            "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
        }


class FormFieldConfigBatchSetHandler(FormFieldOrderSetHandler):
    INTENT_TYPE = FORM_FIELD_CONFIG_INTENTS["batch_set"]
    DESCRIPTION = "Batch set form field order and visibility for current form scope."

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        visibility = params.get("field_visibility") or params.get("fieldVisibility")
        raw_field_order = params.get("field_order") or params.get("fieldOrder")
        raw_field_groups = params.get("field_groups") or params.get("fieldGroups") or {}
        field_sizes = _sanitize_field_string_map(params.get("field_sizes") or params.get("fieldSizes"))
        field_widths = _sanitize_field_string_map(params.get("field_widths") or params.get("fieldWidths"))
        field_classes = _sanitize_field_string_map(params.get("field_classes") or params.get("fieldClasses"))
        group_columns = _sanitize_positive_int_map(params.get("group_columns") or params.get("groupColumns"))
        group_visibility = _sanitize_bool_map(params.get("group_visibility") or params.get("groupVisibility"))
        form_columns = _normalize_form_column_count(params.get("form_columns") or params.get("formColumns"))
        has_field_order = isinstance(raw_field_order, list) and bool(raw_field_order)
        has_field_groups = isinstance(raw_field_groups, dict) and any(
            str(name or "").strip() and str(value or "").strip()
            for name, value in raw_field_groups.items()
        )
        has_field_layout = bool(field_sizes or field_widths or field_classes)
        has_form_layout = bool(form_columns or group_columns or group_visibility)
        layout_field_names = set(field_sizes) | set(field_widths) | set(field_classes)
        if model and isinstance(visibility, dict) and model in self.env:
            unknown = [
                str(field_name or "").strip()
                for field_name in visibility
                if str(field_name or "").strip() and str(field_name or "").strip() not in self.env[model]._fields
            ]
            if unknown:
                return self._err(404, "字段不存在：%s.%s" % (model, unknown[0]), REASON_NOT_FOUND)
        if model and has_field_groups and model in self.env:
            unknown = [
                str(field_name or "").strip()
                for field_name in raw_field_groups
                if str(field_name or "").strip() and str(field_name or "").strip() not in self.env[model]._fields
            ]
            if unknown:
                return self._err(404, "字段不存在：%s.%s" % (model, unknown[0]), REASON_NOT_FOUND)
        if model and has_field_layout and model in self.env:
            unknown = [name for name in layout_field_names if name not in self.env[model]._fields]
            if unknown:
                return self._err(404, "字段不存在：%s.%s" % (model, sorted(unknown)[0]), REASON_NOT_FOUND)
        if has_field_order:
            order_result = super().handle(payload=payload, ctx=ctx)
            if not order_result.get("ok"):
                return order_result
        else:
            if not model:
                return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
            if model not in self.env:
                return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
            if (not isinstance(visibility, dict) or not visibility) and not has_field_groups and not has_field_layout and not has_form_layout:
                return self._err(400, "field_order、field_visibility、field_groups 或布局配置必须至少提供一项", REASON_USER_ERROR)
            action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
            if invalid_field:
                return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
            view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
            if invalid_field:
                return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
            order_result = {
                "ok": True,
                "data": {
                    "model": model,
                    "field_order": [],
                    "updated_count": 0,
                    "business_config_mirrored_count": 0,
                    "contract_reload": _contract_reload_hint(
                        model=model,
                        view_type="form",
                        action_id=action_id,
                        view_id=view_id,
                    ),
                },
                "meta": {"intent": self.INTENT_TYPE, "reason_code": REASON_OK, "source_authority": self._source_authority_contract()},
            }

        def field_layout_attrs(name: str) -> dict:
            attrs = {}
            if field_classes.get(name):
                attrs["class"] = field_classes[name]
            if field_sizes.get(name):
                attrs["field_size"] = field_sizes[name]
            if field_widths.get(name):
                attrs["width"] = field_widths[name]
            return attrs

        if has_field_groups:
            Policy = self.env["ui.form.field.policy"]
            action_id, _ = _optional_non_negative_int(params, "action_id", "actionId")
            view_id, _ = _optional_non_negative_int(params, "view_id", "viewId")
            model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
            group_names = {
                str(field_name or "").strip(): str(group_title or "").strip()
                for field_name, group_title in raw_field_groups.items()
                if str(field_name or "").strip() and str(group_title or "").strip()
            }
            field_rows = self.env["ir.model.fields"].search([
                ("model", "=", model),
                ("name", "in", list(group_names)),
                ("ttype", "!=", "binary"),
            ])
            field_map = {str(row.name or "").strip(): row for row in field_rows}
            plans = []
            for name, group_title in group_names.items():
                policy = Policy.search([
                    ("active", "=", True),
                    ("model", "=", model),
                    ("field_name", "=", name),
                    ("company_id", "=", self.env.company.id),
                    ("action_id", "=", action_id or False),
                    ("view_id", "=", view_id or False),
                ], limit=1)
                if policy:
                    sequence = int(policy.sequence or 100)
                    label = str(policy.label or "")
                    visible = bool(policy.visible)
                    policy_vals = {"group_title": group_title}
                elif model_rec:
                    field_rec = field_map.get(name)
                    label = str((field_rec.field_description if field_rec else name) or name).strip()
                    sequence = 100
                    visible = True
                    policy_vals = {
                        "active": True,
                        "model_id": model_rec.id,
                        "model": model,
                        "field_id": field_rec.id if field_rec else False,
                        "field_name": name,
                        "label": label,
                        "visible": True,
                        "sequence": sequence,
                        "group_title": group_title,
                        "company_id": self.env.company.id,
                        "action_id": action_id or False,
                        "view_id": view_id or False,
                    }
                else:
                    continue
                plans.append({
                    "policy": policy,
                    "policy_vals": policy_vals,
                    "mirror": {
                        "name": name,
                        "label": label or name,
                        "visible": visible,
                        "sequence": sequence,
                        "group_title": group_title,
                        **field_layout_attrs(name),
                    },
                })
            mirrored_count, contract_error = _write_lowcode_form_contract_or_error(
                self,
                model=model,
                rows=[plan["mirror"] for plan in plans],
                action_id=action_id,
                view_id=view_id,
                form_columns=form_columns,
                group_columns=group_columns,
                group_visibility=group_visibility,
            )
            if contract_error:
                return contract_error
            updates = 0
            for plan in plans:
                policy = plan["policy"]
                if policy:
                    policy.write(plan["policy_vals"])
                else:
                    Policy.create(plan["policy_vals"])
                updates += 1
            order_result["data"]["group_updated_count"] = updates
            order_result["data"]["business_config_group_mirrored_count"] = mirrored_count
        if visibility and isinstance(visibility, dict):
            Policy = self.env["ui.form.field.policy"]
            action_id, _ = _optional_non_negative_int(params, "action_id", "actionId")
            view_id, _ = _optional_non_negative_int(params, "view_id", "viewId")
            model_rec = self.env["ir.model"].search([("model", "=", model)], limit=1)
            field_rows = self.env["ir.model.fields"].search([
                ("model", "=", model),
                ("name", "in", [str(name or "").strip() for name in visibility if str(name or "").strip()]),
                ("ttype", "!=", "binary"),
            ])
            field_map = {str(row.name or "").strip(): row for row in field_rows}
            plans = []
            for field_name, raw_visible in visibility.items():
                name = str(field_name or "").strip()
                if not name:
                    continue
                visible = str(raw_visible).strip().lower() not in {"0", "false", "no", "hide", "hidden"}
                policy = Policy.search([
                    ("active", "=", True),
                    ("model", "=", model),
                    ("field_name", "=", name),
                    ("company_id", "=", self.env.company.id),
                    ("action_id", "=", action_id or False),
                    ("view_id", "=", view_id or False),
                ], limit=1)
                if policy:
                    policy_vals = {"visible": bool(visible)}
                elif model_rec:
                    field_rec = field_map.get(name)
                    label = str((field_rec.field_description if field_rec else name) or name).strip()
                    policy_vals = {
                        "active": True,
                        "model_id": model_rec.id,
                        "model": model,
                        "field_id": field_rec.id if field_rec else False,
                        "field_name": name,
                        "label": label,
                        "visible": bool(visible),
                        "sequence": 100,
                        "company_id": self.env.company.id,
                        "action_id": action_id or False,
                        "view_id": view_id or False,
                    }
                else:
                    continue
                plans.append({
                    "policy": policy,
                    "policy_vals": policy_vals,
                    "mirror": {"name": name, "visible": bool(visible), **field_layout_attrs(name)},
                })
            mirrored_count, contract_error = _write_lowcode_form_contract_or_error(
                self,
                model=model,
                rows=[plan["mirror"] for plan in plans],
                action_id=action_id,
                view_id=view_id,
                form_columns=form_columns,
                group_columns=group_columns,
                group_visibility=group_visibility,
            )
            if contract_error:
                return contract_error
            updates = 0
            for plan in plans:
                policy = plan["policy"]
                if policy:
                    policy.write(plan["policy_vals"])
                else:
                    Policy.create(plan["policy_vals"])
                updates += 1
            order_result["data"]["visibility_updated_count"] = updates
            order_result["data"]["business_config_visibility_mirrored_count"] = mirrored_count
        if has_field_layout or (has_form_layout and not (has_field_groups or (visibility and isinstance(visibility, dict)))):
            action_id, _ = _optional_non_negative_int(params, "action_id", "actionId")
            view_id, _ = _optional_non_negative_int(params, "view_id", "viewId")
            field_rows = self.env["ir.model.fields"].search([
                ("model", "=", model),
                ("name", "in", list(layout_field_names)),
                ("ttype", "!=", "binary"),
            ]) if layout_field_names else []
            field_map = {str(row.name or "").strip(): row for row in field_rows}
            mirror_rows = [
                {
                    "name": name,
                    "label": str((field_map.get(name).field_description if field_map.get(name) else name) or name).strip(),
                    **field_layout_attrs(name),
                }
                for name in sorted(layout_field_names)
            ]
            mirrored_count, contract_error = _write_lowcode_form_contract_or_error(
                self,
                model=model,
                rows=mirror_rows,
                action_id=action_id,
                view_id=view_id,
                form_columns=form_columns,
                group_columns=group_columns,
                group_visibility=group_visibility,
            )
            if contract_error:
                return contract_error
            order_result["data"]["field_layout_updated_count"] = len(mirror_rows)
            order_result["data"]["business_config_layout_mirrored_count"] = mirrored_count
        order_result["data"]["business_config_boundary"] = {
            "formal_authority": "ui.business.config.contract.view_orchestration",
            "compatibility_write": "ui.form.field.policy",
            "user_preference_boundary": "not_user_preference",
            "runtime_scope": "current_form",
        }
        order_result["meta"]["intent"] = self.INTENT_TYPE
        order_result["meta"]["low_code_config"] = {
            "enabled": True,
            "scope": "current_form",
            "capabilities": [
                "field_order",
                "field_visibility",
                "field_groups",
                "field_size",
                "field_width",
                "form_columns",
                "group_columns",
                "group_visibility",
            ],
            "formal_authority": "ui.business.config.contract.view_orchestration",
            "compatibility_write": "ui.form.field.policy",
            "user_preference_boundary": "not_user_preference",
        }
        return order_result


class BusinessConfigLowCodeApplyHandler(FormFieldConfigBatchSetHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["lowcode_apply"]
    DESCRIPTION = "Apply low-code business form configuration in current form scope."

    def handle(self, payload=None, ctx=None):
        result = super().handle(payload=payload, ctx=ctx)
        if not isinstance(result, dict):
            return result
        meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
        meta["intent"] = self.INTENT_TYPE
        meta["delivery_profile"] = "business_low_code_form_config"
        result["meta"] = meta
        return result


class BusinessConfigFormAuditHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["form_audit"]
    DESCRIPTION = "Audit low-code form config consistency between business contract and legacy field policy."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    SOURCE_KIND = "ui_business_config_form_audit"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        "ui.business.config.contract.version",
        "ui.form.field.policy",
        "ir.model.fields",
        "ir.actions.act_window",
        "ir.ui.view",
    )

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)

        contracts = self.env["ui.business.config.contract"]._effective_view_orchestration_contracts(
            model,
            view_type="form",
            action_id=action_id,
            view_id=view_id,
            role_key=role_key,
        ) if "ui.business.config.contract" in self.env else []
        contract_items = []
        contract_fields = []
        contract_layout_fields = []
        contract_layout_mismatch_names = []
        for rec in contracts:
            contract_json = rec.contract_json or {}
            field_names = _view_orchestration_field_names(contract_json, "form")
            layout_fields = _view_orchestration_form_layout_fields(contract_json)
            layout_matches_fields = bool(layout_fields) and layout_fields == field_names
            contract_items.append({
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "version_no": int(rec.version_no or 1),
                "fields": field_names,
                "layout_fields": layout_fields,
                "has_layout": bool(layout_fields),
                "layout_matches_fields": layout_matches_fields,
            })
            for name in field_names:
                if name not in contract_fields:
                    contract_fields.append(name)
            for name in layout_fields:
                if name not in contract_layout_fields:
                    contract_layout_fields.append(name)
            if layout_fields and not layout_matches_fields:
                contract_layout_mismatch_names.append(str(rec.name or ""))

        policies = self.env["ui.form.field.policy"]._effective_policies(
            model,
            action_id=action_id,
            view_id=view_id,
            user=self.env.user,
        ) if "ui.form.field.policy" in self.env else []
        policy_items = []
        policy_fields = []
        for policy in policies:
            field_name = str(policy.field_name or "").strip()
            if not field_name:
                continue
            policy_items.append({
                "id": int(policy.id),
                "field_name": field_name,
                "visible": bool(policy.visible),
                "label": str(policy.label or ""),
                "sequence": int(policy.sequence or 100),
                "role_group_ids": [int(group_id) for group_id in policy.role_group_ids.ids],
            })
            if field_name not in policy_fields:
                policy_fields.append(field_name)

        contract_field_set = set(contract_fields)
        policy_field_set = set(policy_fields)
        contract_authoritative = bool(contract_items)
        skipped_legacy_policy_fields = sorted(contract_field_set & policy_field_set)
        legacy_only_policy_fields = sorted(policy_field_set - contract_field_set)
        suppressed_legacy_policy_fields = sorted(policy_field_set) if contract_authoritative else []
        active_legacy_policy_fields = [] if contract_authoritative else sorted(policy_field_set)
        return {
            "ok": True,
            "data": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "runtime_source": (
                    "ui.business.config.contract.view_orchestration"
                    if contract_authoritative
                    else "ui.form.field.policy"
                ),
                "contract_authoritative": contract_authoritative,
                "legacy_policy_runtime_enabled": not contract_authoritative,
                "business_config_contracts": contract_items,
                "business_config_form_fields": sorted(contract_fields),
                "business_config_form_layout_fields": contract_layout_fields,
                "business_config_form_layout_field_count": len(contract_layout_fields),
                "has_business_config_form_layout": bool(contract_layout_fields),
                "layout_matches_fields": bool(contract_layout_fields) and contract_layout_fields == contract_fields,
                "layout_mismatch_contracts": sorted(contract_layout_mismatch_names),
                "legacy_policy_fields": sorted(policy_fields),
                "skipped_legacy_policy_fields": skipped_legacy_policy_fields,
                "legacy_only_policy_fields": legacy_only_policy_fields,
                "suppressed_legacy_policy_fields": suppressed_legacy_policy_fields,
                "active_legacy_policy_fields": active_legacy_policy_fields,
                "has_conflict": bool(skipped_legacy_policy_fields),
                "policies": policy_items,
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigListSearchAuditHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["list_search_audit"]
    DESCRIPTION = "Audit business list/search config boundary against UI-only user preferences."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    SOURCE_KIND = "ui_business_config_list_search_audit"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        "ui.business.config.contract.version",
        "sc.user.view.preference",
        "ir.actions.act_window",
        "ir.ui.view",
    )

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _user_preference_count(self, *, model: str, action_id: int) -> int:
        if "sc.user.view.preference" not in self.env:
            return 0
        Preference = self.env["sc.user.view.preference"].sudo()
        domain = self._user_preference_domain(model=model, action_id=action_id)
        try:
            return int(Preference.search_count(domain))
        except Exception:
            return len(Preference.search(domain, limit=100))

    def _user_preference_domain(self, *, model: str, action_id: int) -> list:
        domain = [
            ("preference_key", "=", "list_columns"),
            ("view_type", "in", ["list", "tree"]),
        ]
        if model:
            domain.append(("model_name", "=", model))
        if action_id:
            domain.append(("action_id", "=", action_id))
        return domain

    def _user_preference_items(self, *, model: str, action_id: int, limit: int = 20) -> list[dict]:
        if "sc.user.view.preference" not in self.env:
            return []
        Preference = self.env["sc.user.view.preference"].sudo()
        domain = self._user_preference_domain(model=model, action_id=action_id)
        try:
            rows = Preference.search(domain, order="id desc", limit=limit)
        except TypeError:
            rows = Preference.search(domain, limit=limit)
        items = []
        for rec in rows:
            value = rec.value_json if isinstance(getattr(rec, "value_json", None), dict) else {}
            columns = value.get("columns") if isinstance(value.get("columns"), list) else []
            visible_columns = value.get("visible_columns") if isinstance(value.get("visible_columns"), list) else []
            user = getattr(rec, "user_id", None)
            action = getattr(rec, "action_id", None)
            items.append({
                "id": int(getattr(rec, "id", 0) or 0),
                "user_id": int(getattr(user, "id", 0) or 0),
                "user_name": str(getattr(user, "name", "") or getattr(user, "login", "") or ""),
                "scope_key": str(getattr(rec, "scope_key", "") or ""),
                "action_id": int(getattr(action, "id", 0) or 0),
                "model": str(getattr(rec, "model_name", "") or ""),
                "view_type": str(getattr(rec, "view_type", "") or ""),
                "preference_key": str(getattr(rec, "preference_key", "") or ""),
                "column_count": len(columns or visible_columns),
            })
        return items

    def _available_model_fields(self, model: str) -> list[dict]:
        return _available_lowcode_model_fields(self.env, model)

    def _business_field_name_set(self, model: str) -> set[str]:
        return _lowcode_business_field_name_set(self.env, model)

    def _model_field_labels(self, model: str, columns: list[str]) -> dict[str, str]:
        if not columns or model not in self.env:
            return {}
        try:
            Model = self.env[model].sudo() if hasattr(self.env[model], "sudo") else self.env[model]
            fields_meta = Model.fields_get(columns)
        except Exception:
            fields_meta = {}
        if not isinstance(fields_meta, dict):
            fields_meta = {}
        labels = {}
        for name in columns:
            meta = fields_meta.get(name) if isinstance(fields_meta.get(name), dict) else {}
            raw_label = meta.get("string") or getattr((getattr(self.env[model], "_fields", {}) or {}).get(name), "string", "") or name
            labels[name] = _clean_lowcode_user_label(name, raw_label)
        return labels

    def _action_tree_view_labels(self, *, model: str, action_id: int, view_id: int = 0) -> dict[str, str]:
        if not model or model not in self.env:
            return {}
        try:
            resolved_view_id = int(view_id or 0)
            if not resolved_view_id and action_id and "ir.actions.act_window" in self.env:
                action = self.env["ir.actions.act_window"].sudo().browse(int(action_id or 0))
                action_view = getattr(action, "view_id", None)
                if action.exists() and action_view and getattr(action_view, "type", "") in ("tree", "list"):
                    resolved_view_id = int(action_view.id or 0)
            Model = self.env[model].sudo() if hasattr(self.env[model], "sudo") else self.env[model]
            context = self._view_context(action_id=action_id, view_id=resolved_view_id)
            if hasattr(Model, "with_context"):
                Model = Model.with_context(**context)
            if hasattr(Model, "get_view"):
                view_def = Model.get_view(view_id=resolved_view_id or None, view_type="tree")
            else:
                view_def = Model.fields_view_get(view_id=resolved_view_id or None, view_type="tree", toolbar=False)
            arch = view_def.get("arch") if isinstance(view_def, dict) else ""
            root = ET.fromstring(str(arch or ""))
            labels = {}
            for node in root.iter("field"):
                name = str(node.get("name") or "").strip()
                label = str(node.get("string") or "").strip()
                if name and label and name not in labels:
                    labels[name] = label
            return labels
        except Exception:
            _logger.debug(
                "BUSINESS_CONFIG_LIST_ACTION_VIEW_LABELS_FAILED model=%s action_id=%s view_id=%s",
                model,
                action_id,
                view_id,
                exc_info=True,
            )
            return {}

    def _view_context(self, *, action_id: int, view_id: int) -> dict:
        context = {"contract_projection_readonly": True}
        if action_id:
            context["contract_action_id"] = action_id
        if view_id:
            context["contract_view_id"] = view_id
        return context

    def _runtime_view_contract(self, *, model: str, view_type: str, action_id: int, view_id: int) -> dict:
        if "app.view.config" not in self.env:
            return {}
        context = self._view_context(action_id=action_id, view_id=view_id)
        ViewConfig = self.env["app.view.config"]
        if hasattr(ViewConfig, "with_context"):
            ViewConfig = ViewConfig.with_context(**context)
        cfg = ViewConfig._generate_from_fields_view_get(model, view_type)
        if hasattr(cfg, "with_user"):
            cfg = cfg.with_user(self.env.user)
        if hasattr(cfg, "sudo"):
            cfg = cfg.sudo()
        if hasattr(cfg, "with_context"):
            cfg = cfg.with_context(**context)
        return cfg.get_contract_api(filter_runtime=True, check_model_acl=True) or {}

    def _suggested_columns(self, *, model: str, action_id: int, view_id: int) -> list[str]:
        try:
            contract = self._runtime_view_contract(model=model, view_type="tree", action_id=action_id, view_id=view_id)
        except Exception:
            _logger.debug(
                "BUSINESS_CONFIG_LIST_SUGGESTED_COLUMNS_FAILED model=%s action_id=%s view_id=%s",
                model,
                action_id,
                view_id,
                exc_info=True,
            )
            return []
        columns = _sanitize_config_name_list(contract.get("columns"))
        if not columns:
            columns = _sanitize_config_name_list(contract.get("columns_schema"))
        business_fields = self._business_field_name_set(model)
        if business_fields:
            columns = [name for name in columns if name in business_fields]
        return columns

    def _suggested_search(self, *, model: str, action_id: int, view_id: int) -> tuple[list[str], list[str]]:
        filters = []
        group_by = []
        try:
            contract = self._runtime_view_contract(model=model, view_type="search", action_id=action_id, view_id=view_id)
            search = contract.get("search") if isinstance(contract.get("search"), dict) else {}
            filters = _sanitize_config_name_list(search.get("filters"))
            group_by = _sanitize_config_name_list(search.get("group_by") or search.get("groupBys"))
        except Exception:
            _logger.debug(
                "BUSINESS_CONFIG_SEARCH_SUGGESTED_CONTRACT_FAILED model=%s action_id=%s view_id=%s",
                model,
                action_id,
                view_id,
                exc_info=True,
            )
            filters = []
            group_by = []
        if (filters or group_by) or "app.search.config" not in self.env:
            business_fields = self._business_field_name_set(model)
            if business_fields:
                filters = [name for name in filters if name in business_fields]
                group_by = [name for name in group_by if name in business_fields]
            return filters, group_by
        try:
            SearchConfig = self.env["app.search.config"]
            cfg = SearchConfig._generate_from_search(model)
            contract = cfg.get_search_contract(filter_runtime=True, include_user_filters=False) or {}
        except Exception:
            _logger.debug(
                "BUSINESS_CONFIG_SEARCH_SUGGESTED_FALLBACK_FAILED model=%s action_id=%s view_id=%s",
                model,
                action_id,
                view_id,
                exc_info=True,
            )
            return [], []
        business_fields = self._business_field_name_set(model)
        filters = _sanitize_config_name_list(contract.get("filters"))
        group_by = _sanitize_config_name_list(contract.get("group_by") or contract.get("groupBys"))
        if business_fields:
            filters = [name for name in filters if name in business_fields]
            group_by = [name for name in group_by if name in business_fields]
        return filters, group_by

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)

        contract_model = self.env["ui.business.config.contract"] if "ui.business.config.contract" in self.env else None
        if contract_model and hasattr(contract_model, "sudo"):
            contract_model = contract_model.sudo()
        list_contracts = contract_model._effective_view_orchestration_contracts(
            model,
            view_type="tree",
            action_id=action_id,
            view_id=view_id,
            role_key=role_key,
        ) if contract_model else []
        search_contracts = contract_model._effective_view_orchestration_contracts(
            model,
            view_type="search",
            action_id=action_id,
            view_id=view_id,
            role_key=role_key,
        ) if contract_model else []
        if not list_contracts:
            list_contracts = _search_published_view_orchestration_contracts(
                self.env,
                model=model,
                view_type="tree",
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
                role_key=role_key,
            )
        if not search_contracts:
            search_contracts = _search_published_view_orchestration_contracts(
                self.env,
                model=model,
                view_type="search",
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
                role_key=role_key,
            )

        list_columns = []
        list_column_labels = {}
        action_view_column_labels = {}
        model_field_labels = {}
        list_items = []
        for rec in list_contracts:
            contract_json = rec.contract_json or {}
            columns = _view_orchestration_field_names(contract_json, "tree")
            column_labels = _view_orchestration_field_label_map(contract_json, "tree")
            list_items.append({
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "version_no": int(rec.version_no or 1),
                "columns": columns,
                "column_labels": {
                    name: column_labels.get(name) or name
                    for name in columns
                },
            })
            for name in columns:
                if name not in list_columns:
                    list_columns.append(name)
                if name and name not in list_column_labels:
                    list_column_labels[name] = column_labels.get(name) or name
        if list_columns:
            action_view_column_labels = self._action_tree_view_labels(
                model=model,
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            )
            model_field_labels = self._model_field_labels(model, list_columns)
            def resolve_list_label(name: str) -> str:
                configured_label = str(list_column_labels.get(name) or "").strip()
                if configured_label == name:
                    configured_label = ""
                override_label = _form_field_label_override(model, name)
                if override_label:
                    return override_label
                cleaned_configured_label = _clean_lowcode_user_label(name, configured_label) if configured_label else ""
                return (
                    cleaned_configured_label
                    or action_view_column_labels.get(name)
                    or _clean_lowcode_user_label(name, model_field_labels.get(name) or name)
                )
            list_column_labels = {
                name: resolve_list_label(name)
                for name in list_columns
            }
            for item in list_items:
                item["column_labels"] = {
                    name: list_column_labels.get(name) or name
                    for name in item.get("columns", [])
                }

        search_filters = []
        search_group_by = []
        search_items = []
        for rec in search_contracts:
            filters = _view_orchestration_search_names(rec.contract_json or {}, "filters")
            group_by = _view_orchestration_search_names(rec.contract_json or {}, "group_by")
            search_items.append({
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "version_no": int(rec.version_no or 1),
                "filters": filters,
                "group_by": group_by,
            })
            for name in filters:
                if name not in search_filters:
                    search_filters.append(name)
            for name in group_by:
                if name not in search_group_by:
                    search_group_by.append(name)

        preference_count = self._user_preference_count(model=model, action_id=action_id)
        preference_items = self._user_preference_items(model=model, action_id=action_id)
        suggested_columns = [] if list_columns else self._suggested_columns(
            model=model,
            action_id=int(action_id or 0),
            view_id=int(view_id or 0),
        )
        suggested_filters, suggested_group_by = ([], [])
        if not search_filters and not search_group_by:
            suggested_filters, suggested_group_by = self._suggested_search(
                model=model,
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            )
        contract_authoritative = bool(list_items or search_items)
        has_suggested_defaults = bool(suggested_columns or suggested_filters or suggested_group_by)
        return {
            "ok": True,
            "data": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "runtime_source": (
                    "ui.business.config.contract.view_orchestration"
                    if contract_authoritative
                    else ("runtime_backend_view_contract" if has_suggested_defaults else "none")
                ),
                "contract_authoritative": contract_authoritative,
                "suggested_defaults_only": not contract_authoritative and has_suggested_defaults,
                "business_config_list_contracts": list_items,
                "business_config_search_contracts": search_items,
                "business_config_list_columns": list_columns,
                "business_config_list_column_labels": list_column_labels,
                "business_config_search_filters": search_filters,
                "business_config_search_group_by": search_group_by,
                "suggested_list_columns": suggested_columns,
                "suggested_search_filters": suggested_filters,
                "suggested_search_group_by": suggested_group_by,
                "available_model_fields": self._available_model_fields(model),
                "user_preference_count": preference_count,
                "user_preferences": preference_items,
                "user_preference_boundary": "ui_only",
                "has_business_list_config": bool(list_columns),
                "has_business_search_config": bool(search_filters or search_group_by),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigListSearchSetHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["list_search_set"]
    DESCRIPTION = "Save business list columns and search filters into view_orchestration contracts."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_business_config_list_search_set"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES
    NON_IDEMPOTENT_ALLOWED = "business list/search config is mutable authoring state"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": False,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _business_field_name_set(self, model: str) -> set[str]:
        return _lowcode_business_field_name_set(self.env, model)

    def _upsert_contract(self, *, model: str, view_type: str, action_id: int, view_id: int, role_key: str, payload: dict, publish: bool):
        if _lowcode_contract_write_unavailable(self.env):
            raise RuntimeError("ui.business.config.contract is not writable")
        Contract = self.env["ui.business.config.contract"].sudo()
        name = _business_config_contract_name(model, view_type, action_id, view_id)
        domain = [
            ("name", "=", name),
            ("company_id", "=", self.env.company.id),
            ("view_type", "=", view_type or False),
            ("action_id", "=", action_id or False),
            ("view_id", "=", view_id or False),
            ("role_key", "=", role_key or False),
        ]
        vals = {
            "name": name,
            "model": model,
            "view_type": view_type or False,
            "action_id": action_id or False,
            "view_id": view_id or False,
            "role_key": role_key or False,
            "contract_json": payload,
            "status": "published" if publish else "draft",
        }
        rec = Contract.search(domain, limit=1)
        if rec:
            rec.write(vals)
        else:
            rec = Contract.create(vals)
        if publish:
            rec.action_publish()
        return rec

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        publish = params.get("publish") is not False
        list_columns = _sanitize_config_name_list(params.get("list_columns") or params.get("listColumns"))
        search_filters = _sanitize_config_name_list(params.get("search_filters") or params.get("searchFilters"))
        search_group_by = _sanitize_config_name_list(params.get("search_group_by") or params.get("searchGroupBy"))
        if not list_columns and not search_filters and not search_group_by:
            return self._err(400, "缺少列表列或搜索配置", REASON_MISSING_PARAMS)

        model_fields = set(getattr(self.env[model], "_fields", {}) or {})
        business_fields = self._business_field_name_set(model)
        valid_fields = business_fields or model_fields
        unknown = sorted(set(list_columns + search_filters + search_group_by) - valid_fields)
        if unknown:
            return self._err(400, "配置引用不存在或不可用于低代码业务配置字段：%s" % ", ".join(unknown), REASON_USER_ERROR)

        saved = []
        try:
            if list_columns:
                tree_payload = _business_config_view_orchestration_payload(view_type="tree", names=list_columns)
                rec = self._upsert_contract(
                    model=model,
                    view_type="tree",
                    action_id=action_id,
                    view_id=view_id,
                    role_key=role_key,
                    payload=tree_payload,
                    publish=publish,
                )
                saved.append({
                    "id": int(rec.id),
                    "name": str(rec.name or ""),
                    "view_type": str(rec.view_type or ""),
                    "status": str(rec.status or ""),
                    "version_no": int(rec.version_no or 1),
                    "columns": list_columns,
                    "contract_reload": _contract_reload_hint_for_record(rec),
                })
            if search_filters or search_group_by:
                search_payload = {}
                if search_filters:
                    search_payload = _business_config_view_orchestration_payload(
                        view_type="search",
                        names=search_filters,
                        existing=search_payload,
                        search_key="filters",
                    )
                if search_group_by:
                    search_payload = _business_config_view_orchestration_payload(
                        view_type="search",
                        names=search_group_by,
                        existing=search_payload,
                        search_key="group_by",
                    )
                rec = self._upsert_contract(
                    model=model,
                    view_type="search",
                    action_id=action_id,
                    view_id=view_id,
                    role_key=role_key,
                    payload=search_payload,
                    publish=publish,
                )
                saved.append({
                    "id": int(rec.id),
                    "name": str(rec.name or ""),
                    "view_type": str(rec.view_type or ""),
                    "status": str(rec.status or ""),
                    "version_no": int(rec.version_no or 1),
                    "filters": search_filters,
                    "group_by": search_group_by,
                    "contract_reload": _contract_reload_hint_for_record(rec),
                })
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        except Exception as exc:
            return _lowcode_contract_write_failed_error(self, exc)
        return {
            "ok": True,
            "data": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "saved": saved,
                "saved_count": len(saved),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigAnalysisAuditHandler(BusinessConfigListSearchAuditHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["analysis_audit"]
    DESCRIPTION = "Audit business analysis view config from view_orchestration contracts."
    SOURCE_KIND = "ui_business_config_analysis_audit"
    SOURCE_AUTHORITIES = (
        "ui.business.config.contract",
        "ui.business.config.contract.version",
        "ir.actions.act_window",
        "ir.ui.view",
    )

    def _suggested_analysis(self, *, model: str, view_type: str, action_id: int, view_id: int) -> tuple[list[str], list[str], str]:
        try:
            contract = self._runtime_view_contract(model=model, view_type=view_type, action_id=action_id, view_id=view_id)
        except Exception:
            _logger.debug(
                "BUSINESS_CONFIG_ANALYSIS_SUGGESTED_CONTRACT_FAILED model=%s view_type=%s action_id=%s view_id=%s",
                model,
                view_type,
                action_id,
                view_id,
                exc_info=True,
            )
            contract = {}
        view = contract.get(view_type) if isinstance(contract.get(view_type), dict) else {}
        measures = _sanitize_config_name_list(view.get("measures"))
        dimensions = _sanitize_config_name_list(view.get("dimensions"))
        chart_type = str(view.get("type") or view.get("type_default") or "bar").strip() or "bar"
        business_fields = self._business_field_name_set(model)
        if business_fields:
            measures = [name for name in measures if name in business_fields]
            dimensions = [name for name in dimensions if name in business_fields]
        return measures, dimensions, chart_type

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        contract_model = self.env["ui.business.config.contract"] if "ui.business.config.contract" in self.env else None
        if contract_model and hasattr(contract_model, "sudo"):
            contract_model = contract_model.sudo()
        view_types = ["pivot", "graph"]
        configs = {}
        contract_items = []
        business_fields = self._business_field_name_set(model)
        for view_type in view_types:
            contracts = contract_model._effective_view_orchestration_contracts(
                model,
                view_type=view_type,
                action_id=action_id,
                view_id=view_id,
                role_key=role_key,
            ) if contract_model else []
            if not contracts:
                contracts = _search_published_view_orchestration_contracts(
                    self.env,
                    model=model,
                    view_type=view_type,
                    action_id=int(action_id or 0),
                    view_id=int(view_id or 0),
                    role_key=role_key,
                )
            measures = []
            dimensions = []
            chart_type = ""
            for rec in contracts:
                config = _view_orchestration_analysis_config(rec.contract_json or {}, view_type)
                for name in config.get("measures") or []:
                    if (not business_fields or name in business_fields) and name not in measures:
                        measures.append(name)
                for name in config.get("dimensions") or []:
                    if (not business_fields or name in business_fields) and name not in dimensions:
                        dimensions.append(name)
                if not chart_type and config.get("type"):
                    chart_type = str(config.get("type") or "")
                contract_items.append({
                    "id": int(getattr(rec, "id", 0) or 0),
                    "name": str(getattr(rec, "name", "") or ""),
                    "view_type": view_type,
                    "version_no": int(getattr(rec, "version_no", 1) or 1),
                    "measures": measures,
                    "dimensions": dimensions,
                    "type": chart_type,
                })
            configs[view_type] = {
                "measures": measures,
                "dimensions": dimensions,
                "type": chart_type,
            }
        suggested_pivot_measures, suggested_pivot_dimensions, suggested_pivot_type = ([], [], "")
        suggested_graph_measures, suggested_graph_dimensions, suggested_graph_type = ([], [], "")
        if not configs["pivot"]["measures"] and not configs["pivot"]["dimensions"]:
            suggested_pivot_measures, suggested_pivot_dimensions, suggested_pivot_type = self._suggested_analysis(
                model=model,
                view_type="pivot",
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            )
        if not configs["graph"]["measures"] and not configs["graph"]["dimensions"]:
            suggested_graph_measures, suggested_graph_dimensions, suggested_graph_type = self._suggested_analysis(
                model=model,
                view_type="graph",
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            )
        return {
            "ok": True,
            "data": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "business_config_analysis_contracts": contract_items,
                "pivot_measures": configs["pivot"]["measures"],
                "pivot_dimensions": configs["pivot"]["dimensions"],
                "graph_measures": configs["graph"]["measures"],
                "graph_dimensions": configs["graph"]["dimensions"],
                "graph_type": configs["graph"]["type"] or "bar",
                "suggested_pivot_measures": suggested_pivot_measures,
                "suggested_pivot_dimensions": suggested_pivot_dimensions,
                "suggested_graph_measures": suggested_graph_measures,
                "suggested_graph_dimensions": suggested_graph_dimensions,
                "suggested_graph_type": suggested_graph_type or suggested_pivot_type or "bar",
                "available_model_fields": self._available_model_fields(model),
                "business_config_boundary": "business_contract",
                "user_preference_boundary": "not_a_source",
                "has_business_analysis_config": any(
                    configs[item]["measures"] or configs[item]["dimensions"] for item in view_types
                ),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigAnalysisSetHandler(BusinessConfigListSearchSetHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["analysis_set"]
    DESCRIPTION = "Save business analysis view config into view_orchestration contracts."
    SOURCE_KIND = "ui_business_config_analysis_set"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES
    NON_IDEMPOTENT_ALLOWED = "business analysis config is mutable authoring state"

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        if not model:
            return self._err(400, "缺少 model", REASON_MISSING_PARAMS)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        publish = params.get("publish") is not False
        pivot_measures = _sanitize_config_name_list(params.get("pivot_measures") or params.get("pivotMeasures"))
        pivot_dimensions = _sanitize_config_name_list(params.get("pivot_dimensions") or params.get("pivotDimensions"))
        graph_measures = _sanitize_config_name_list(params.get("graph_measures") or params.get("graphMeasures"))
        graph_dimensions = _sanitize_config_name_list(params.get("graph_dimensions") or params.get("graphDimensions"))
        graph_type = str(params.get("graph_type") or params.get("graphType") or "bar").strip() or "bar"
        if not pivot_measures and not pivot_dimensions and not graph_measures and not graph_dimensions:
            return self._err(400, "缺少分析指标或维度配置", REASON_MISSING_PARAMS)

        model_fields = set(getattr(self.env[model], "_fields", {}) or {})
        business_fields = self._business_field_name_set(model)
        valid_fields = business_fields or model_fields
        unknown = sorted(set(pivot_measures + pivot_dimensions + graph_measures + graph_dimensions) - valid_fields)
        if unknown:
            return self._err(400, "配置引用不存在或不可用于低代码业务配置字段：%s" % ", ".join(unknown), REASON_USER_ERROR)

        saved = []
        try:
            if pivot_measures or pivot_dimensions:
                pivot_payload = _business_config_analysis_payload(
                    view_type="pivot",
                    measures=pivot_measures,
                    dimensions=pivot_dimensions,
                    chart_type=graph_type,
                )
                rec = self._upsert_contract(
                    model=model,
                    view_type="pivot",
                    action_id=action_id,
                    view_id=view_id,
                    role_key=role_key,
                    payload=pivot_payload,
                    publish=publish,
                )
                saved.append({
                    "id": int(rec.id),
                    "name": str(rec.name or ""),
                    "view_type": str(rec.view_type or ""),
                    "status": str(rec.status or ""),
                    "version_no": int(rec.version_no or 1),
                    "measures": pivot_measures,
                    "dimensions": pivot_dimensions,
                    "contract_reload": _contract_reload_hint_for_record(rec),
                })
            if graph_measures or graph_dimensions:
                graph_payload = _business_config_analysis_payload(
                    view_type="graph",
                    measures=graph_measures,
                    dimensions=graph_dimensions,
                    chart_type=graph_type,
                )
                rec = self._upsert_contract(
                    model=model,
                    view_type="graph",
                    action_id=action_id,
                    view_id=view_id,
                    role_key=role_key,
                    payload=graph_payload,
                    publish=publish,
                )
                saved.append({
                    "id": int(rec.id),
                    "name": str(rec.name or ""),
                    "view_type": str(rec.view_type or ""),
                    "status": str(rec.status or ""),
                    "version_no": int(rec.version_no or 1),
                    "measures": graph_measures,
                    "dimensions": graph_dimensions,
                    "type": graph_type,
                    "contract_reload": _contract_reload_hint_for_record(rec),
                })
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        except Exception as exc:
            return _lowcode_contract_write_failed_error(self, exc)
        return {
            "ok": True,
            "data": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "saved": saved,
                "saved_count": len(saved),
                "business_config_boundary": "business_contract",
                "user_preference_boundary": "not_a_source",
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigListSearchBootstrapHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["list_search_bootstrap"]
    DESCRIPTION = "Bootstrap business list/search contracts from current backend view contracts."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_business_config_list_search_bootstrap"
    SOURCE_AUTHORITIES = (
        "app.view.config",
        "app.search.config",
        "ir.actions.act_window",
        "ui.business.config.contract",
        "ui.business.config.contract.version",
    )
    NON_IDEMPOTENT_ALLOWED = "business list/search bootstrap publishes official low-code contracts"

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": False,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
            "personal_preference_boundary": "not_a_source",
        }

    def _available_model_fields(self, model: str) -> list[dict]:
        return _available_lowcode_model_fields(self.env, model)

    def _business_field_name_set(self, model: str) -> set[str]:
        return _lowcode_business_field_name_set(self.env, model)

    def _resolve_action_model(self, action_id: int) -> str:
        if not action_id or "ir.actions.act_window" not in self.env:
            return ""
        Action = self.env["ir.actions.act_window"].sudo()
        action = None
        if hasattr(Action, "browse"):
            action = Action.browse(action_id)
            if action and hasattr(action, "exists") and not action.exists():
                action = None
        if not action:
            rows = Action.search([("id", "=", action_id)], limit=1)
            action = rows[0] if isinstance(rows, list) and rows else rows
        return str(getattr(action, "res_model", "") or "").strip() if action else ""

    def _view_context(self, *, action_id: int, view_id: int) -> dict:
        context = {"contract_projection_readonly": True}
        if action_id:
            context["contract_action_id"] = action_id
        if view_id:
            context["contract_view_id"] = view_id
        return context

    def _runtime_view_contract(self, *, model: str, view_type: str, action_id: int, view_id: int) -> dict:
        if "app.view.config" not in self.env:
            return {}
        context = self._view_context(action_id=action_id, view_id=view_id)
        ViewConfig = self.env["app.view.config"]
        if hasattr(ViewConfig, "with_context"):
            ViewConfig = ViewConfig.with_context(**context)
        cfg = ViewConfig._generate_from_fields_view_get(model, view_type)
        if hasattr(cfg, "with_user"):
            cfg = cfg.with_user(self.env.user)
        if hasattr(cfg, "sudo"):
            cfg = cfg.sudo()
        if hasattr(cfg, "with_context"):
            cfg = cfg.with_context(**context)
        return cfg.get_contract_api(filter_runtime=True, check_model_acl=True) or {}

    def _bootstrap_columns(self, *, model: str, action_id: int, view_id: int) -> list[str]:
        contract = self._runtime_view_contract(model=model, view_type="tree", action_id=action_id, view_id=view_id)
        columns = _sanitize_config_name_list(contract.get("columns"))
        if columns:
            return columns
        return _sanitize_config_name_list(contract.get("columns_schema"))

    def _bootstrap_search(self, *, model: str, action_id: int, view_id: int) -> tuple[list[str], list[str]]:
        filters = []
        group_by = []
        try:
            contract = self._runtime_view_contract(model=model, view_type="search", action_id=action_id, view_id=view_id)
            search = contract.get("search") if isinstance(contract.get("search"), dict) else {}
            filters = _sanitize_config_name_list(search.get("filters"))
            group_by = _sanitize_config_name_list(search.get("group_by") or search.get("groupBys"))
        except Exception:
            filters = []
            group_by = []
        if (filters or group_by) or "app.search.config" not in self.env:
            return filters, group_by
        SearchConfig = self.env["app.search.config"]
        cfg = SearchConfig._generate_from_search(model)
        contract = cfg.get_search_contract(filter_runtime=True, include_user_filters=False) or {}
        return (
            _sanitize_config_name_list(contract.get("filters")),
            _sanitize_config_name_list(contract.get("group_by") or contract.get("groupBys")),
        )

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        model = str(params.get("model") or "").strip() or self._resolve_action_model(int(action_id or 0))
        if not model:
            return self._err(400, "缺少 model 或有效 action_id", REASON_MISSING_PARAMS)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        publish = params.get("publish") is not False
        raw_view_types = params.get("view_types") or params.get("viewTypes") or ["tree", "search"]
        target_view_types = {_normalize_view_type_scope(item) for item in raw_view_types if str(item or "").strip()} if isinstance(raw_view_types, list) else {"tree", "search"}

        try:
            list_columns = self._bootstrap_columns(model=model, action_id=int(action_id or 0), view_id=int(view_id or 0)) if "tree" in target_view_types else []
            search_filters, search_group_by = self._bootstrap_search(model=model, action_id=int(action_id or 0), view_id=int(view_id or 0)) if "search" in target_view_types else ([], [])
        except Exception as exc:
            return self._err(400, "无法从当前视图生成列表/搜索契约：%s" % type(exc).__name__, REASON_USER_ERROR)

        model_fields = set(getattr(self.env[model], "_fields", {}) or {})
        if model_fields:
            list_columns = [name for name in list_columns if name in model_fields]
            search_filters = [name for name in search_filters if name in model_fields]
            search_group_by = [name for name in search_group_by if name in model_fields]
        business_fields = self._business_field_name_set(model)
        if business_fields:
            list_columns = [name for name in list_columns if name in business_fields]
            search_filters = [name for name in search_filters if name in business_fields]
            search_group_by = [name for name in search_group_by if name in business_fields]
        if not list_columns and not search_filters and not search_group_by:
            return self._err(400, "当前视图没有可固化的列表列或搜索配置", REASON_USER_ERROR)

        setter = BusinessConfigListSearchSetHandler(
            env=self.env,
            payload={"params": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "list_columns": list_columns,
                "search_filters": search_filters,
                "search_group_by": search_group_by,
                "publish": publish,
            }},
        )
        result = setter.handle()
        if not result.get("ok"):
            return result
        data = dict(result.get("data") or {})
        data.update({
            "bootstrapped_from": "runtime_backend_view_contract",
            "personal_preference_boundary": "not_a_source",
            "list_columns": list_columns,
            "search_filters": search_filters,
            "search_group_by": search_group_by,
        })
        return {
            "ok": True,
            "data": data,
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigAnalysisBootstrapHandler(BusinessConfigListSearchBootstrapHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["analysis_bootstrap"]
    DESCRIPTION = "Bootstrap business analysis contracts from current backend pivot/graph view contracts."
    SOURCE_KIND = "ui_business_config_analysis_bootstrap"
    SOURCE_AUTHORITIES = (
        "app.view.config",
        "ir.model.fields",
        "ir.actions.act_window",
        "ui.business.config.contract",
        "ui.business.config.contract.version",
    )
    NON_IDEMPOTENT_ALLOWED = "business analysis bootstrap publishes official low-code contracts"

    def _source_authority_contract(self):
        contract = super()._source_authority_contract()
        contract["kind"] = self.SOURCE_KIND
        contract["runtime_carrier"] = self.INTENT_TYPE
        return contract

    def _bootstrap_analysis(self, *, model: str, view_type: str, action_id: int, view_id: int) -> tuple[list[str], list[str], str]:
        contract = self._runtime_view_contract(model=model, view_type=view_type, action_id=action_id, view_id=view_id)
        view = contract.get(view_type) if isinstance(contract.get(view_type), dict) else {}
        measures = _sanitize_config_name_list(view.get("measures"))
        dimensions = _sanitize_config_name_list(view.get("dimensions"))
        graph_type = str(view.get("type") or view.get("type_default") or "bar").strip() or "bar"
        if not measures and not dimensions:
            measures, dimensions = self._fallback_analysis_fields(model)
        return measures, dimensions, graph_type

    def _fallback_analysis_fields(self, model: str) -> tuple[list[str], list[str]]:
        technical_names = {"id", "display_name", "create_uid", "create_date", "write_uid", "write_date", "__last_update"}
        measure_types = {"monetary", "float", "integer"}
        dimension_types = {"many2one", "selection", "date", "datetime", "boolean", "char"}
        preferred_dimension_names = (
            "project_id", "company_id", "partner_id", "contract_id", "department_id",
            "user_id", "state", "status", "date", "month", "year",
        )
        try:
            fields_meta = self.env[model].sudo().fields_get() if hasattr(self.env[model], "sudo") else self.env[model].fields_get()
        except Exception:
            fields_meta = {}
        if not isinstance(fields_meta, dict) or not fields_meta:
            fields_meta = {
                name: {"type": getattr(field, "type", "")}
                for name, field in (getattr(self.env[model], "_fields", {}) or {}).items()
            }
        measures = []
        dimensions = []
        for name, meta in sorted(fields_meta.items()):
            field_name = str(name or "").strip()
            if not field_name or field_name in technical_names or field_name.startswith("__"):
                continue
            field_meta = meta if isinstance(meta, dict) else {}
            field_type = str(field_meta.get("type") or getattr((getattr(self.env[model], "_fields", {}) or {}).get(name), "type", "") or "").strip()
            if field_type in measure_types and field_name not in measures:
                measures.append(field_name)
            if field_type in dimension_types and field_name not in dimensions:
                dimensions.append(field_name)
        dimensions.sort(key=lambda item: (
            next((idx for idx, prefix in enumerate(preferred_dimension_names) if item == prefix or item.endswith("_%s" % prefix)), 99),
            item,
        ))
        return measures[:8], dimensions[:8]

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        model = str(params.get("model") or "").strip() or self._resolve_action_model(int(action_id or 0))
        if not model:
            return self._err(400, "缺少 model 或有效 action_id", REASON_MISSING_PARAMS)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        publish = params.get("publish") is not False
        raw_view_types = params.get("view_types") or params.get("viewTypes") or ["pivot", "graph"]
        target_view_types = {_normalize_view_type_scope(item) for item in raw_view_types if str(item or "").strip()} if isinstance(raw_view_types, list) else {"pivot", "graph"}
        target_view_types = target_view_types.intersection({"pivot", "graph"})
        if not target_view_types:
            return self._err(400, "缺少可自动固化的分析视图类型", REASON_MISSING_PARAMS)

        try:
            pivot_measures, pivot_dimensions, pivot_chart_type = self._bootstrap_analysis(
                model=model,
                view_type="pivot",
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            ) if "pivot" in target_view_types else ([], [], "")
            graph_measures, graph_dimensions, graph_type = self._bootstrap_analysis(
                model=model,
                view_type="graph",
                action_id=int(action_id or 0),
                view_id=int(view_id or 0),
            ) if "graph" in target_view_types else ([], [], "")
        except Exception as exc:
            return self._err(400, "无法从当前分析视图生成分析契约：%s" % type(exc).__name__, REASON_USER_ERROR)

        model_fields = set(getattr(self.env[model], "_fields", {}) or {})
        if model_fields:
            pivot_measures = [name for name in pivot_measures if name in model_fields]
            pivot_dimensions = [name for name in pivot_dimensions if name in model_fields]
            graph_measures = [name for name in graph_measures if name in model_fields]
            graph_dimensions = [name for name in graph_dimensions if name in model_fields]
        if not pivot_measures and not pivot_dimensions and not graph_measures and not graph_dimensions:
            return self._err(400, "当前分析视图没有可固化的指标或维度配置", REASON_USER_ERROR)

        setter = BusinessConfigAnalysisSetHandler(
            env=self.env,
            payload={"params": {
                "model": model,
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "pivot_measures": pivot_measures,
                "pivot_dimensions": pivot_dimensions,
                "graph_measures": graph_measures,
                "graph_dimensions": graph_dimensions,
                "graph_type": graph_type or pivot_chart_type or "bar",
                "publish": publish,
            }},
        )
        result = setter.handle()
        if not result.get("ok"):
            return result
        data = dict(result.get("data") or {})
        data.update({
            "bootstrapped_from": "runtime_backend_analysis_view_contract",
            "personal_preference_boundary": "not_a_source",
            "pivot_measures": pivot_measures,
            "pivot_dimensions": pivot_dimensions,
            "graph_measures": graph_measures,
            "graph_dimensions": graph_dimensions,
            "graph_type": graph_type or pivot_chart_type or "bar",
        })
        return {
            "ok": True,
            "data": data,
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigFormBootstrapHandler(BusinessConfigListSearchBootstrapHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["form_bootstrap"]
    DESCRIPTION = "Bootstrap business form contract from current backend form view contract."
    SOURCE_KIND = "ui_business_config_form_bootstrap"
    SOURCE_AUTHORITIES = (
        "app.view.config",
        "ir.actions.act_window",
        "ui.business.config.contract",
        "ui.business.config.contract.version",
    )
    NON_IDEMPOTENT_ALLOWED = "business form bootstrap publishes official low-code contract"

    def _collect_layout_field_names(self, value) -> list[str]:
        names = []

        def visit(node):
            if isinstance(node, list):
                for child in node:
                    visit(child)
                return
            if not isinstance(node, dict):
                return
            node_type = str(node.get("type") or "").strip().lower()
            field_name = str(node.get("name") or node.get("field") or "").strip()
            if node_type == "field" and field_name and field_name not in names:
                names.append(field_name)
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(child_key)
                if isinstance(children, list):
                    visit(children)

        visit(value)
        return names

    def _filter_layout_to_fields(self, value, allowed_fields: set[str]):
        def clean(node):
            if isinstance(node, list):
                out = []
                for child in node:
                    cleaned = clean(child)
                    if cleaned is None:
                        continue
                    if isinstance(cleaned, list):
                        out.extend(cleaned)
                    else:
                        out.append(cleaned)
                return out
            if not isinstance(node, dict):
                return node
            node_type = str(node.get("type") or "").strip().lower()
            field_name = str(node.get("name") or node.get("field") or "").strip()
            if node_type == "field" and field_name and field_name not in allowed_fields:
                return None
            next_node = dict(node)
            for child_key in ("children", "pages", "tabs", "nodes", "items"):
                children = next_node.get(child_key)
                if isinstance(children, list):
                    next_node[child_key] = clean(children)
            return next_node

        cleaned = clean(value)
        return cleaned if isinstance(cleaned, list) else []

    def _bootstrap_form_payload(self, *, model: str, action_id: int, view_id: int) -> dict:
        contract = self._runtime_view_contract(model=model, view_type="form", action_id=action_id, view_id=view_id)
        layout = contract.get("layout") if isinstance(contract.get("layout"), list) else []
        field_names = self._collect_layout_field_names(layout)
        model_fields = set(getattr(self.env[model], "_fields", {}) or {})
        if model_fields:
            field_names = [name for name in field_names if name in model_fields]
        business_fields = self._business_field_name_set(model)
        if business_fields:
            field_names = [name for name in field_names if name in business_fields]
        if not field_names:
            raise ValidationError("当前表单视图没有可固化的字段布局")
        layout = self._filter_layout_to_fields(layout, set(field_names)) if layout else []
        fields = [{"name": name, "sequence": (idx + 1) * 10} for idx, name in enumerate(field_names)]
        form_spec = {
            "fields": fields,
        }
        if layout:
            form_spec["layout"] = layout
        title = str(contract.get("title") or "").strip()
        if title:
            form_spec["title"] = title
        for key in ("defaults", "context", "domain"):
            value = contract.get(key)
            if isinstance(value, dict):
                form_spec[key] = value
        return {
            "view_orchestration": {
                "views": {
                    "form": form_spec,
                },
                "context": {
                    "source": "runtime_backend_form_view_contract",
                    "action_id": int(action_id or 0),
                    "view_id": int(view_id or 0),
                },
            }
        }

    def handle(self, payload=None, ctx=None):
        del payload, ctx
        params = self.params if isinstance(self.params, dict) else {}
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        model = str(params.get("model") or "").strip() or self._resolve_action_model(int(action_id or 0))
        if not model:
            return self._err(400, "缺少 model 或有效 action_id", REASON_MISSING_PARAMS)
        if model not in self.env:
            return self._err(404, "模型不存在：%s" % model, REASON_NOT_FOUND)
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        publish = params.get("publish") is not False
        try:
            contract_json = self._bootstrap_form_payload(model=model, action_id=int(action_id or 0), view_id=int(view_id or 0))
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        except Exception as exc:
            return self._err(400, "无法从当前表单生成表单契约：%s" % type(exc).__name__, REASON_USER_ERROR)
        saver = BusinessConfigContractSaveHandler(
            env=self.env,
            payload={"params": {
                "name": _business_config_contract_name(model, "form", int(action_id or 0), int(view_id or 0)),
                "model": model,
                "view_type": "form",
                "action_id": int(action_id or 0),
                "view_id": int(view_id or 0),
                "role_key": role_key,
                "contract_json": contract_json,
                "publish": publish,
            }},
        )
        result = saver.handle()
        if not result.get("ok"):
            return result
        data = dict(result.get("data") or {})
        field_names = _view_orchestration_field_names(contract_json, "form")
        data.update({
            "bootstrapped_from": "runtime_backend_form_view_contract",
            "personal_preference_boundary": "not_a_source",
            "form_fields": field_names,
            "field_count": len(field_names),
        })
        return {
            "ok": True,
            "data": data,
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractSaveHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["contract_save"]
    DESCRIPTION = "Save low-code business config contract payload into contract model."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_business_config_contract_save"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES
    NON_IDEMPOTENT_ALLOWED = "business config contract is mutable authoring state"

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        view_type = str(params.get("view_type") or params.get("viewType") or "").strip()
        role_key = str(params.get("role_key") or params.get("roleKey") or "").strip()
        contract_json = params.get("contract_json") or params.get("contractJson")
        publish = bool(params.get("publish") is True)
        if not name or not model:
            return self._err(400, "缺少 name 或 model", REASON_MISSING_PARAMS)
        legacy_role_scope = _reject_legacy_role_group_scope(params)
        if legacy_role_scope:
            return self._err(400, "%s 不属于业务配置作用域，请使用 role_key" % legacy_role_scope, REASON_USER_ERROR)
        action_id, invalid_field = _optional_non_negative_int(params, "action_id", "actionId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        view_id, invalid_field = _optional_non_negative_int(params, "view_id", "viewId")
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        if not isinstance(contract_json, dict):
            return self._err(400, "contract_json 必须是对象", REASON_USER_ERROR)
        if "legacy_lowcode_draft" in contract_json:
            return self._err(400, "legacy_lowcode_draft 已停止作为保存来源，请使用 view_orchestration", REASON_USER_ERROR)
        contract_json = _lowcode_view_orchestration_payload(contract_json)
        precheck = self._precheck_contract_payload(contract_json)
        if precheck["errors"]:
            return self._err(400, "contract_json 预检失败", REASON_USER_ERROR)
        Contract = self.env["ui.business.config.contract"]
        domain = [
            ("name", "=", name),
            ("company_id", "=", self.env.company.id),
            ("view_type", "=", view_type or False),
            ("action_id", "=", action_id or False),
            ("view_id", "=", view_id or False),
            ("role_key", "=", role_key or False),
        ]
        rec = Contract.search(domain, limit=1)
        vals = {
            "name": name,
            "model": model,
            "view_type": view_type or False,
            "action_id": action_id or False,
            "view_id": view_id or False,
            "role_key": role_key or False,
            "contract_json": contract_json,
            "status": "published" if publish else "draft",
        }
        try:
            if rec:
                rec.write(vals)
            else:
                rec = Contract.create(vals)
            if publish:
                rec.action_publish()
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        except Exception as exc:
            return _lowcode_contract_write_failed_error(self, exc)
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "view_type": str(rec.view_type or ""),
                "action_id": int(rec.action_id.id or 0),
                "view_id": int(rec.view_id.id or 0),
                "role_key": str(rec.role_key or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "precheck": precheck,
                "contract_reload": _contract_reload_hint_for_record(rec),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }

    def _precheck_contract_payload(self, payload: dict) -> dict:
        warnings = []
        errors = []
        view_orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
        self._precheck_view_orchestration_layout(view_orchestration, warnings, errors)
        explicit_objects = isinstance(payload.get("objects"), list)
        objects = payload.get("objects") if explicit_objects else []
        if not view_orchestration:
            errors.append("contract_json 必须包含 view_orchestration。")
        elif not _view_orchestration_has_configured_view(view_orchestration):
            errors.append("view_orchestration.views 必须至少包含一个非空视图配置。")
        has_view_fields = bool(_view_orchestration_field_names(payload, "form"))
        for obj in objects:
            if not isinstance(obj, dict):
                errors.append("objects 包含非对象节点。")
                continue
            obj_name = str(obj.get("name") or "").strip()
            if not obj_name:
                errors.append("存在未命名业务对象。")
            fields_rows = obj.get("fields") if isinstance(obj.get("fields"), list) else []
            if not fields_rows and (explicit_objects or not has_view_fields):
                warnings.append("业务对象 %s 未配置字段。" % (obj_name or "<unknown>"))
        rules = payload.get("rules") if isinstance(payload.get("rules"), list) else []
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                errors.append("rules[%s] 非对象。" % idx)
                continue
            if not str(rule.get("name") or "").strip():
                warnings.append("rules[%s] 缺少 name。" % idx)
            if str(rule.get("trigger") or "").strip() == "scheduled" and not rule.get("cron"):
                warnings.append("rules[%s] 为 scheduled 但未配置 cron。" % idx)
        return {"warnings": warnings, "errors": errors}

    def _precheck_view_orchestration_layout(self, view_orchestration: dict, warnings: list[str], errors: list[str]) -> None:
        views = view_orchestration.get("views") if isinstance(view_orchestration.get("views"), dict) else {}
        form_spec = views.get("form") if isinstance(views.get("form"), dict) else {}
        if "layout" not in form_spec:
            return
        layout = form_spec.get("layout")
        if not isinstance(layout, list):
            errors.append("view_orchestration.views.form.layout 必须是数组。")
            return

        child_keys = ("children", "pages", "tabs", "nodes", "items")

        def visit(nodes, path):
            for index, node in enumerate(nodes):
                node_path = "%s[%s]" % (path, index)
                if not isinstance(node, dict):
                    errors.append("%s 必须是对象。" % node_path)
                    continue
                node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
                field_name = str(node.get("name") or node.get("field") or "").strip()
                if not node_type:
                    warnings.append("%s 缺少 type/kind。" % node_path)
                if node_type == "field" and not field_name:
                    errors.append("%s 字段节点缺少 name。" % node_path)
                for child_key in child_keys:
                    if child_key not in node:
                        continue
                    children = node.get(child_key)
                    if not isinstance(children, list):
                        errors.append("%s.%s 必须是数组。" % (node_path, child_key))
                        continue
                    visit(children, "%s.%s" % (node_path, child_key))

        visit(layout, "view_orchestration.views.form.layout")


class BusinessConfigContractGetHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["contract_get"]
    DESCRIPTION = "Get low-code business config contract payload by name/model."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    SOURCE_KIND = "ui_business_config_contract_get"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        invalid_field = _append_business_config_scope_domain(params, domain, include_status=True)
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        rec = self.env["ui.business.config.contract"].search(domain, limit=1)
        if not rec:
            return self._err(404, "未找到业务配置", REASON_NOT_FOUND)
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "view_type": str(rec.view_type or ""),
                "action_id": int(rec.action_id.id or 0),
                "view_id": int(rec.view_id.id or 0),
                "role_key": str(rec.role_key or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "contract_json": rec.contract_json or {},
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractListHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["contract_list"]
    DESCRIPTION = "List low-code business config contracts in current company."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    SOURCE_KIND = "ui_business_config_contract_list"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        model = str(params.get("model") or "").strip()
        domain = [("company_id", "=", self.env.company.id)]
        if model:
            domain.append(("model", "=", model))
        invalid_field = _append_business_config_scope_domain(params, domain, include_status=True)
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        rows = self.env["ui.business.config.contract"].search(domain, limit=100, order="write_date desc, id desc")
        data = [{
            "id": int(rec.id),
            "name": str(rec.name or ""),
            "model": str(rec.model or ""),
            "view_type": str(rec.view_type or ""),
            "action_id": int(rec.action_id.id or 0),
            "view_id": int(rec.view_id.id or 0),
            "role_key": str(rec.role_key or ""),
            "status": str(rec.status or "draft"),
            "version_no": int(rec.version_no or 1),
        } for rec in rows]
        return {
            "ok": True,
            "data": {"items": data},
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractVersionsHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["contract_versions"]
    DESCRIPTION = "List low-code business config contract versions in current scope."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    SOURCE_KIND = "ui_business_config_contract_versions"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _version_item(self, version) -> dict:
        snapshot = version.snapshot_json if isinstance(version.snapshot_json, dict) else {}
        return {
            "id": int(version.id),
            "version_no": int(version.version_no or 1),
            "status": str(version.status or "draft"),
            "created_by": getattr(getattr(version, "created_by", None), "display_name", "") or "",
            "summary": _business_config_contract_summary(snapshot),
        }

    def _contract_item(self, rec) -> dict:
        versions = self.env["ui.business.config.contract.version"].search(
            [("contract_id", "=", rec.id)], order="version_no desc, id desc", limit=20
        )
        return {
            "id": int(rec.id),
            "name": str(rec.name or ""),
            "model": str(rec.model or ""),
            "view_type": str(rec.view_type or ""),
            "action_id": int(rec.action_id.id or 0),
            "view_id": int(rec.view_id.id or 0),
            "role_key": str(rec.role_key or ""),
            "status": str(rec.status or "draft"),
            "version_no": int(rec.version_no or 1),
            "summary": _business_config_contract_summary(rec.contract_json or {}),
            "versions": [self._version_item(version) for version in versions],
        }

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        invalid_field = _append_business_config_scope_domain(params, domain, include_status=True)
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        rows = self.env["ui.business.config.contract"].search(domain, limit=100, order="write_date desc, id desc")
        contracts = [self._contract_item(rec) for rec in rows]
        return {
            "ok": True,
            "data": {
                "model": model,
                "contracts": contracts,
                "contract_count": len(contracts),
                "version_count": sum(len(item["versions"]) for item in contracts),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractPublishHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["contract_publish"]
    DESCRIPTION = "Publish a low-code business config contract by name/model."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_business_config_contract_publish"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES
    NON_IDEMPOTENT_ALLOWED = "business config contract publish mutates active runtime configuration"

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        invalid_field = _append_business_config_scope_domain(params, domain)
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        rec = self.env["ui.business.config.contract"].search(domain, limit=1)
        if not rec:
            return self._err(404, "未找到业务配置", REASON_NOT_FOUND)
        try:
            rec.action_publish()
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        except Exception as exc:
            return _lowcode_contract_write_failed_error(self, exc)
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "contract_reload": _contract_reload_hint_for_record(rec),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }


class BusinessConfigContractRollbackHandler(BaseIntentHandler):
    INTENT_TYPE = BUSINESS_CONFIG_INTENTS["contract_rollback"]
    DESCRIPTION = "Rollback a low-code business config contract to a previous or specified snapshot."
    REQUIRED_GROUPS = [BUSINESS_CONFIG_ADMIN_GROUP]
    ACL_MODE = "explicit_check"
    SOURCE_KIND = "ui_business_config_contract_rollback"
    SOURCE_AUTHORITIES = BUSINESS_CONFIG_CONTRACT_AUTHORITIES
    NON_IDEMPOTENT_ALLOWED = "business config contract rollback mutates active runtime configuration"

    def _source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "write_proxy": True,
            "no_business_fact_authority": True,
            "runtime_carrier": self.INTENT_TYPE,
        }

    def _err(self, code: int, message: str, reason_code: str):
        return {"ok": False, "error": {"code": reason_code, "message": message, "reason_code": reason_code}, "code": code}

    def handle(self, payload=None, ctx=None):
        params = self.params if isinstance(self.params, dict) else {}
        name = str(params.get("name") or "").strip()
        model = str(params.get("model") or "").strip()
        if not name and not model:
            return self._err(400, "name 或 model 至少提供一个", REASON_MISSING_PARAMS)
        target_version_no, invalid_version_field = _optional_non_negative_int(params, "version_no", "versionNo")
        if invalid_version_field:
            return self._err(400, "%s 必须是非负整数" % invalid_version_field, REASON_USER_ERROR)
        domain = [("company_id", "=", self.env.company.id)]
        if name:
            domain.append(("name", "=", name))
        if model:
            domain.append(("model", "=", model))
        invalid_field = _append_business_config_scope_domain(params, domain)
        if invalid_field:
            return self._err(400, "%s 必须是非负整数" % invalid_field, REASON_USER_ERROR)
        rec = self.env["ui.business.config.contract"].search(domain, limit=1)
        if not rec:
            return self._err(404, "未找到业务配置", REASON_NOT_FOUND)
        version_domain = [("contract_id", "=", rec.id)]
        version_limit = 2
        if target_version_no:
            version_domain.append(("version_no", "=", target_version_no))
            version_limit = 1
        versions = self.env["ui.business.config.contract.version"].search(
            version_domain, order="version_no desc, id desc", limit=version_limit
        )
        if not versions:
            return self._err(404, "未找到目标版本", REASON_NOT_FOUND)
        if not target_version_no and len(versions) < 2:
            return self._err(400, "无可回滚版本", REASON_USER_ERROR)
        target = versions[0] if target_version_no else versions[1]
        try:
            rec.write({
                "contract_json": target.snapshot_json or {},
                "status": "published",
                "version_no": int(target.version_no or rec.version_no or 1),
            })
            rec.action_publish()
        except ValidationError as exc:
            return self._err(400, str(exc), REASON_USER_ERROR)
        except Exception as exc:
            return _lowcode_contract_write_failed_error(self, exc)
        return {
            "ok": True,
            "data": {
                "id": int(rec.id),
                "name": str(rec.name or ""),
                "model": str(rec.model or ""),
                "status": str(rec.status or "draft"),
                "version_no": int(rec.version_no or 1),
                "rolled_back_to_version": int(target.version_no or 1),
                "contract_reload": _contract_reload_hint_for_record(rec),
            },
            "meta": {"intent": self.INTENT_TYPE, "source_authority": self._source_authority_contract(), "reason_code": REASON_OK},
        }
