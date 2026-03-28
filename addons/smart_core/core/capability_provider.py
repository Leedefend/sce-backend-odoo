# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
from .capability_group_defaults import (
    DEFAULT_CAPABILITY_GROUPS,
    default_group_meta,
    default_group_order_map,
    infer_group_key,
)


def _default_group_meta(group_key: str) -> dict:
    return default_group_meta(group_key)


def _infer_group_key(capability_key: str) -> str:
    return infer_group_key(capability_key)


def build_capability_groups(capabilities: List[dict]) -> List[dict]:
    grouped: dict[str, dict] = {}
    for idx, cap in enumerate(capabilities or []):
        if not isinstance(cap, dict):
            continue
        group_key = str(cap.get("group_key") or "").strip() or _infer_group_key(cap.get("key"))
        group_label = str(cap.get("group_label") or "").strip()
        meta = _default_group_meta(group_key)
        bucket = grouped.setdefault(
            group_key,
            {
                "key": group_key,
                "label": group_label or meta["label"],
                "icon": str(cap.get("group_icon") or meta.get("icon") or ""),
                "sequence": int(cap.get("group_sequence") or 0) or len(grouped) + 1,
                "capabilities": [],
                "capability_count": 0,
                "state_counts": {"READY": 0, "LOCKED": 0, "PREVIEW": 0},
                "capability_state_counts": {"allow": 0, "readonly": 0, "deny": 0, "pending": 0, "coming_soon": 0},
            },
        )
        if cap.get("group_label"):
            bucket["label"] = str(cap.get("group_label"))
        if cap.get("group_icon"):
            bucket["icon"] = str(cap.get("group_icon"))
        cap_group_sequence = int(cap.get("group_sequence") or 0)
        if cap_group_sequence > 0:
            current_sequence = int(bucket.get("sequence") or 0)
            bucket["sequence"] = cap_group_sequence if current_sequence <= 0 else min(current_sequence, cap_group_sequence)
        cap_copy = dict(cap)
        cap_copy["group_key"] = group_key
        cap_copy["group_label"] = bucket["label"]
        cap_copy["group_sequence"] = idx + 1
        bucket["capabilities"].append(cap_copy)
        bucket["capability_count"] = int(bucket.get("capability_count") or 0) + 1
        state = str(cap_copy.get("state") or "").strip().upper()
        capability_state = str(cap_copy.get("capability_state") or "").strip().lower()
        if state in bucket["state_counts"]:
            bucket["state_counts"][state] = int(bucket["state_counts"].get(state) or 0) + 1
        if capability_state in bucket["capability_state_counts"]:
            bucket["capability_state_counts"][capability_state] = (
                int(bucket["capability_state_counts"].get(capability_state) or 0) + 1
            )

    order_map = default_group_order_map(DEFAULT_CAPABILITY_GROUPS)
    result = list(grouped.values())
    result.sort(
        key=lambda item: (
            int(item.get("sequence") or 0) if int(item.get("sequence") or 0) > 0 else order_map.get(item.get("key"), 999),
            order_map.get(item.get("key"), 999),
            str(item.get("label") or ""),
        )
    )
    for seq, item in enumerate(result, start=1):
        item["sequence"] = seq
    return result


def load_capabilities_for_user(env, user) -> List[dict]:
    extension_caps = call_extension_hook_first(env, "smart_core_list_capabilities_for_user", env, user)
    if isinstance(extension_caps, list) and extension_caps:
        return extension_caps

    try:
        extension_groups = call_extension_hook_first(env, "smart_core_capability_groups", env)
        if isinstance(extension_groups, list) and extension_groups:
            global DEFAULT_CAPABILITY_GROUPS
            DEFAULT_CAPABILITY_GROUPS = [dict(item) for item in extension_groups if isinstance(item, dict)]
    except Exception:
        pass

    try:
        cap_model = env["sc.capability"].sudo()
    except Exception:
        return []
    try:
        caps = cap_model.search([("active", "=", True)], order="sequence, id")
    except Exception:
        return []
    out: List[dict] = []
    for rec in caps:
        try:
            if rec._user_visible(user):
                out.append(rec.to_public_dict(user))
        except Exception:
            continue
    return out
