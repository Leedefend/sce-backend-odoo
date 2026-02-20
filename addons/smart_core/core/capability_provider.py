# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List


DEFAULT_CAPABILITY_GROUPS = [
    {"key": "project_management", "label": "项目管理", "icon": "briefcase"},
    {"key": "contract_management", "label": "合同管理", "icon": "file-text"},
    {"key": "cost_management", "label": "成本管理", "icon": "calculator"},
    {"key": "finance_management", "label": "财务管理", "icon": "wallet"},
    {"key": "material_management", "label": "物资管理", "icon": "boxes"},
    {"key": "governance", "label": "治理配置", "icon": "shield"},
    {"key": "analytics", "label": "经营分析", "icon": "chart"},
    {"key": "others", "label": "其他能力", "icon": "grid"},
]


def _default_group_meta(group_key: str) -> dict:
    for item in DEFAULT_CAPABILITY_GROUPS:
        if item["key"] == group_key:
            return dict(item)
    return {"key": group_key, "label": group_key, "icon": ""}


def _infer_group_key(capability_key: str) -> str:
    key = str(capability_key or "").strip().lower()
    if not key:
        return "others"
    if key.startswith(("project.", "scene.project", "wbs.", "progress.", "tender.")):
        return "project_management"
    if key.startswith(("contract.", "settlement.")):
        return "contract_management"
    if key.startswith(("cost.", "budget.", "boq.")):
        return "cost_management"
    if key.startswith(("finance.", "payment.", "treasury.")):
        return "finance_management"
    if key.startswith(("material.", "purchase.", "stock.")):
        return "material_management"
    if key.startswith(("usage.", "report.", "dashboard.", "analytics.")):
        return "analytics"
    if key.startswith(("scene.", "portal.", "config.", "permission.", "subscription.", "pack.")):
        return "governance"
    return "others"


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
                "icon": meta.get("icon") or "",
                "sequence": len(grouped) + 1,
                "capabilities": [],
            },
        )
        cap_copy = dict(cap)
        cap_copy["group_key"] = group_key
        cap_copy["group_label"] = bucket["label"]
        cap_copy["group_sequence"] = idx + 1
        bucket["capabilities"].append(cap_copy)

    order_map = {item["key"]: index for index, item in enumerate(DEFAULT_CAPABILITY_GROUPS, start=1)}
    result = list(grouped.values())
    result.sort(key=lambda item: (order_map.get(item.get("key"), 999), str(item.get("label") or "")))
    for seq, item in enumerate(result, start=1):
        item["sequence"] = seq
    return result


def load_capabilities_for_user(env, user) -> List[dict]:
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
