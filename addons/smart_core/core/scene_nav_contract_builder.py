# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib
from typing import Dict, List, Tuple


GROUP_LABELS = {
    "portal": "工作台",
    "projects": "项目管理",
    "project": "项目管理",
    "cost": "成本管理",
    "contract": "合同管理",
    "finance": "资金财务",
    "risk": "风险管理",
    "task": "任务管理",
    "data": "数据与字典",
    "config": "配置中心",
}

GROUP_ORDER = {
    "portal": 10,
    "projects": 20,
    "project": 20,
    "task": 30,
    "risk": 40,
    "cost": 50,
    "contract": 60,
    "finance": 70,
    "data": 80,
    "config": 90,
}

GROUP_ALIASES = {
    "project": "projects",
}

EXCLUDED_REASON_NO_CODE = "no_code"
EXCLUDED_REASON_IMPORTED_PKG = "imported_pkg_variant"
EXCLUDED_REASON_SMOKE_CODE = "smoke_code"
EXCLUDED_REASON_INTERNAL_TAG = "internal_or_smoke_tag"
EXCLUDED_REASON_NO_TARGET = "missing_target"
EXCLUDED_REASON_DEFAULT_PLACEHOLDER = "default_placeholder"
EXCLUDED_REASON_SHOWCASE = "showcase_or_demo"
EXCLUDED_REASON_PORTAL_LEGACY = "portal_legacy"
EXCLUDED_REASON_NOT_SPA_READY = "portal_only_not_spa_ready"
EXCLUDED_REASON_DEMO_TARGET = "demo_target"
EXCLUDED_REASON_NO_NAV_TARGET = "target_fields_empty"
EXCLUDED_REASON_ACCESS_DENIED = "access_denied"
EXCLUDED_REASON_DEPRECATED_ALIAS = "deprecated_alias"

NAV_HIDDEN_SCENE_CODES = {
    "projects.dashboard",
}


def _to_bool(value, default=False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def _delivery_gate_reason(scene: dict, code: str, target: dict) -> str | None:
    if code == "default":
        return EXCLUDED_REASON_DEFAULT_PLACEHOLDER
    lowered = code.lower()
    if "showcase" in lowered or ".demo" in lowered or lowered.endswith(".demo"):
        return EXCLUDED_REASON_SHOWCASE
    portal_only = _to_bool(scene.get("portal_only"), False)
    spa_ready = _to_bool(scene.get("spa_ready"), True)
    if portal_only and not spa_ready:
        return EXCLUDED_REASON_NOT_SPA_READY
    route = str(target.get("route") or "").strip().lower()
    if route.startswith("/portal/") or route.startswith("/workbench"):
        return EXCLUDED_REASON_PORTAL_LEGACY
    target_text = " ".join(
        [
            str(target.get("action_xmlid") or ""),
            str(target.get("menu_xmlid") or ""),
            str(target.get("route") or ""),
        ]
    ).lower()
    if "smart_construction_demo" in target_text:
        return EXCLUDED_REASON_DEMO_TARGET
    return None


def _synthetic_menu_id(key: str, base: int = 700_000_000, span: int = 200_000_000) -> int:
    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def _scene_allowed(scene: dict) -> bool:
    access = scene.get("access")
    if isinstance(access, dict):
        allowed = access.get("allowed")
        if isinstance(allowed, bool):
            return allowed
    return True


def _scene_valid(scene: dict) -> tuple[bool, str | None]:
    code = str(scene.get("code") or scene.get("key") or "").strip()
    if not code:
        return False, EXCLUDED_REASON_NO_CODE
    if code in NAV_HIDDEN_SCENE_CODES:
        return False, EXCLUDED_REASON_DEPRECATED_ALIAS
    if "__pkg" in code:
        return False, EXCLUDED_REASON_IMPORTED_PKG
    if code.startswith("scene_smoke_"):
        return False, EXCLUDED_REASON_SMOKE_CODE
    tags = scene.get("tags")
    if isinstance(tags, list):
        tags_norm = {str(t or "").strip().lower() for t in tags}
        if "internal" in tags_norm or "smoke" in tags_norm:
            return False, EXCLUDED_REASON_INTERNAL_TAG
    target = scene.get("target")
    if not isinstance(target, dict):
        return False, EXCLUDED_REASON_NO_TARGET
    gate_reason = _delivery_gate_reason(scene, code, target)
    if gate_reason:
        return False, gate_reason
    has_target = any(
        bool(target.get(k))
        for k in ("route", "action_id", "action_xmlid", "menu_id", "menu_xmlid", "model")
    )
    if not has_target:
        return False, EXCLUDED_REASON_NO_NAV_TARGET
    if not _scene_allowed(scene):
        return False, EXCLUDED_REASON_ACCESS_DENIED
    return True, None


def _scene_structurally_valid(scene: dict) -> tuple[bool, str | None]:
    code = str(scene.get("code") or scene.get("key") or "").strip()
    if not code:
        return False, EXCLUDED_REASON_NO_CODE
    if code in NAV_HIDDEN_SCENE_CODES:
        return False, EXCLUDED_REASON_DEPRECATED_ALIAS
    target = scene.get("target")
    if not isinstance(target, dict):
        return False, EXCLUDED_REASON_NO_TARGET
    has_target = any(
        bool(target.get(k))
        for k in ("route", "action_id", "action_xmlid", "menu_id", "menu_xmlid", "model")
    )
    if not has_target:
        return False, EXCLUDED_REASON_NO_NAV_TARGET
    return True, None


def build_scene_delivery_report(scenes: list[dict] | None, *, policy_applied: bool = False) -> dict:
    input_items = [item for item in (scenes or []) if isinstance(item, dict)]
    ready_codes: List[str] = []
    excluded: List[dict] = []
    reason_counts: Dict[str, int] = {}

    for item in input_items:
        code = str(item.get("code") or item.get("key") or "").strip()
        valid, reason = _scene_structurally_valid(item) if policy_applied else _scene_valid(item)
        if code and valid:
            ready_codes.append(code)
            continue
        safe_reason = str(reason or "unknown").strip() or "unknown"
        safe_code = code
        reason_counts[safe_reason] = int(reason_counts.get(safe_reason, 0)) + 1
        excluded.append({"code": safe_code, "reason": safe_reason})

    return {
        "scene_input_count": len(input_items),
        "scene_count": len(ready_codes),
        "excluded_scene_count": len(excluded),
        "excluded_reason_counts": reason_counts,
        "excluded_scenes": excluded,
        "delivery_ready_scene_codes": sorted(set(ready_codes)),
    }


def _group_key(scene_key: str) -> str:
    key = str(scene_key or "").strip().lower()
    if not key:
        return "others"
    raw_group = key.split(".", 1)[0]
    return GROUP_ALIASES.get(raw_group, raw_group)


def _to_leaf(scene: dict) -> dict:
    scene_key = str(scene.get("code") or scene.get("key") or "").strip()
    scene_name = str(scene.get("name") or scene_key).strip() or scene_key
    menu_id = _synthetic_menu_id(f"scene:{scene_key}")
    return {
        "key": f"scene:{scene_key}",
        "label": scene_name,
        "title": scene_name,
        "menu_id": menu_id,
        "children": [],
        "scene_key": scene_key,
        "meta": {
            "scene_key": scene_key,
            "action_type": "scene.contract",
            "menu_xmlid": f"scene.contract.{scene_key.replace('.', '_')}",
            "scene_source": "scene_contract",
        },
    }


def _build_group_nodes(leaves: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = {}
    for leaf in leaves:
        group = _group_key(leaf.get("scene_key") or "")
        grouped.setdefault(group, []).append(leaf)

    out: List[Tuple[int, str, dict]] = []
    for group, items in grouped.items():
        items_sorted = sorted(items, key=lambda x: str(x.get("label") or ""))
        label = GROUP_LABELS.get(group, "其他场景")
        order = GROUP_ORDER.get(group, 999)
        node = {
            "key": f"group:{group}",
            "label": label,
            "title": label,
            "menu_id": _synthetic_menu_id(f"group:{group}", base=640_000_000, span=40_000_000),
            "children": items_sorted,
            "meta": {
                "scene_source": "scene_contract",
                "group_key": group,
            },
        }
        out.append((order, label, node))
    out.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in out]


def build_scene_nav_contract(data: dict) -> dict:
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_candidates = [
        str(x or "").strip()
        for x in (role_surface.get("scene_candidates") or [])
        if str(x or "").strip()
    ]
    policy_applied = bool(data.get("delivery_policy_applied"))
    delivery_report = build_scene_delivery_report(scenes, policy_applied=policy_applied)
    ready_codes = set(delivery_report.get("delivery_ready_scene_codes") or [])
    scene_map: Dict[str, dict] = {}
    for item in scenes:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or item.get("key") or "").strip()
        if code and code in ready_codes:
            scene_map[code] = item

    candidate_leaves = [_to_leaf(scene_map[key]) for key in role_candidates if key in scene_map]
    remaining = [v for k, v in scene_map.items() if k not in set(role_candidates)]
    remaining_leaves = [_to_leaf(v) for v in remaining]
    grouped = _build_group_nodes(remaining_leaves)

    primary_children = []
    if candidate_leaves:
        primary_children.append({
            "key": "group:role_primary",
            "label": "我的场景",
            "title": "我的场景",
            "menu_id": _synthetic_menu_id("group:role_primary", base=640_000_000, span=40_000_000),
            "children": candidate_leaves,
            "meta": {
                "scene_source": "scene_contract",
                "group_key": "role_primary",
            },
        })
    primary_children.extend(grouped)

    root = {
        "key": "root:scene_contract",
        "label": "场景导航",
        "title": "场景导航",
        "menu_id": _synthetic_menu_id("root:scene_contract", base=600_000_000, span=20_000_000),
        "children": primary_children,
        "meta": {
            "scene_source": "scene_contract",
            "menu_xmlid": "scene.contract.root",
        },
    }

    first_leaf = None
    for group in primary_children:
        for child in group.get("children") or []:
            first_leaf = child
            break
        if first_leaf:
            break

    return {
        "source": "scene_contract_v1",
        "nav": [root],
        "default_route": {"menu_id": (first_leaf or {}).get("menu_id")},
        "meta": {
            "scene_input_count": int(delivery_report.get("scene_input_count") or 0),
            "scene_count": int(delivery_report.get("scene_count") or 0),
            "excluded_scene_count": int(delivery_report.get("excluded_scene_count") or 0),
            "excluded_reason_counts": delivery_report.get("excluded_reason_counts") or {},
            "excluded_scenes_sample": (delivery_report.get("excluded_scenes") or [])[:20],
            "candidate_count": len(candidate_leaves),
            "group_count": len(primary_children),
            "policy_applied": policy_applied,
        },
    }
