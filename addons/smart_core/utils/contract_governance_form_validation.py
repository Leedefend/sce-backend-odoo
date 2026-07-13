# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


_RENDER_PROFILE_CREATE = "create"
_RENDER_PROFILE_EDIT = "edit"
_RENDER_PROFILE_READONLY = "readonly"
_RENDER_PROFILES = {_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY}


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def normalize_profile_list(raw: Any, fallback: list[str] | None = None) -> list[str]:
    if not isinstance(raw, list):
        return list(fallback or [])
    out: list[str] = []
    for item in raw:
        profile = _safe_text(item).lower()
        if profile in _RENDER_PROFILES and profile not in out:
            out.append(profile)
    return out or list(fallback or [])


def build_form_validation_rules(
    data: dict,
    contract_mode: str,
    *,
    required_fields: list[str],
    to_bool: Callable[[Any], bool],
) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    fields_map = _as_dict(data.get("fields"))
    for name in required_fields:
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            continue
        readonly = to_bool(descriptor.get("readonly"))
        if not readonly:
            rules.append(
                {
                    "code": "REQUIRED",
                    "field": name,
                    "when_profiles": [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
                    "message": f"{_safe_text(descriptor.get('string'), name)} 为必填字段",
                }
            )
    record_rules = _as_dict(_as_dict(data.get("validator")).get("record_rules"))
    for row in record_rules.get("sql_checks") if isinstance(record_rules.get("sql_checks"), list) else []:
        if not isinstance(row, dict):
            continue
        message = _safe_text(row.get("message"))
        definition = _safe_text(row.get("definition"))
        if not message and not definition:
            continue
        item = {
            "code": "SQL_CHECK",
            "name": _safe_text(row.get("name")),
            "message": message or definition,
        }
        if contract_mode == "hud":
            item["expr"] = definition
        rules.append(item)
    return rules


def apply_business_form_policy(
    data: dict,
    *,
    to_bool: Callable[[Any], bool],
) -> None:
    policy_root = _as_dict(data.get("business_form_policy"))
    if not policy_root:
        return
    fields_map = _as_dict(data.get("fields"))
    field_policies = _as_dict(data.get("field_policies"))
    required_fields = {
        _safe_text(name)
        for name in (policy_root.get("required_fields") if isinstance(policy_root.get("required_fields"), list) else [])
        if _safe_text(name) in fields_map
    }
    rows = policy_root.get("fields") if isinstance(policy_root.get("fields"), list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = _safe_text(row.get("name") or row.get("field") or row.get("field_name"))
        if not name or name not in fields_map:
            continue
        descriptor = _as_dict(fields_map.get(name))
        source_readonly = to_bool(descriptor.get("readonly"))
        base = _as_dict(field_policies.get(name))
        visible_profiles = normalize_profile_list(row.get("visible_profiles"), base.get("visible_profiles") or [
            _RENDER_PROFILE_CREATE,
            _RENDER_PROFILE_EDIT,
            _RENDER_PROFILE_READONLY,
        ])
        readonly_profiles = normalize_profile_list(row.get("readonly_profiles"), base.get("readonly_profiles") or [_RENDER_PROFILE_READONLY])
        required_profiles = normalize_profile_list(row.get("required_profiles"), base.get("required_profiles") or [])
        if name in required_fields and not source_readonly:
            required_profiles = normalize_profile_list(
                required_profiles + [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
                [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
            )
        if source_readonly:
            readonly_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
            required_profiles = []
        base.update({
            "visible_profiles": visible_profiles,
            "required_profiles": required_profiles,
            "readonly_profiles": readonly_profiles,
            "source_required": bool(required_profiles),
            "source_readonly": source_readonly or bool(row.get("source_readonly")),
            "group": _safe_text(row.get("group"), base.get("group") or "secondary"),
        })
        field_policies[name] = base
    for name in required_fields:
        if name not in field_policies:
            descriptor = _as_dict(fields_map.get(name))
            readonly = to_bool(descriptor.get("readonly"))
            field_policies[name] = {
                "visible_profiles": [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY],
                "required_profiles": [] if readonly else [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
                "readonly_profiles": (
                    [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
                    if readonly
                    else [_RENDER_PROFILE_READONLY]
                ),
                "source_required": not readonly,
                "source_readonly": readonly,
                "group": "core",
            }
        else:
            item = _as_dict(field_policies.get(name))
            if not to_bool(item.get("source_readonly")):
                item["required_profiles"] = normalize_profile_list(
                    (item.get("required_profiles") if isinstance(item.get("required_profiles"), list) else [])
                    + [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
                    [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
                )
                item["source_required"] = True
                field_policies[name] = item
    data["field_policies"] = field_policies

    validation_rules = data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []
    existing_required = {
        _safe_text(rule.get("field"))
        for rule in validation_rules
        if isinstance(rule, dict) and _safe_text(rule.get("code")).upper() == "REQUIRED"
    }
    for name in sorted(required_fields):
        if name in existing_required:
            continue
        descriptor = _as_dict(fields_map.get(name))
        if to_bool(descriptor.get("readonly")):
            continue
        validation_rules.append({
            "code": "REQUIRED",
            "field": name,
            "when_profiles": [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
            "message": f"{_safe_text(descriptor.get('string'), name)} 为必填字段",
        })
    data["validation_rules"] = validation_rules
