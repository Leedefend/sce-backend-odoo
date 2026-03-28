# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

from .scene_nav_node_defaults import build_scene_nav_group_node


def resolve_scene_nav_group_key(scene_key: str, aliases: Dict[str, str] | None = None) -> str:
    key = str(scene_key or "").strip().lower()
    if not key:
        return "others"
    raw_group = key.split(".", 1)[0]
    alias_map = aliases if isinstance(aliases, dict) else {}
    return alias_map.get(raw_group, raw_group)


def build_scene_nav_grouped_nodes(
    leaves: List[dict],
    *,
    group_labels: Dict[str, str] | None = None,
    group_order: Dict[str, int] | None = None,
    group_aliases: Dict[str, str] | None = None,
) -> List[dict]:
    labels = group_labels if isinstance(group_labels, dict) else {}
    order_map = group_order if isinstance(group_order, dict) else {}
    aliases = group_aliases if isinstance(group_aliases, dict) else {}
    configured_groups = set(labels.keys()) | set(order_map.keys()) | {"others"}
    grouped: Dict[str, List[dict]] = {}
    for leaf in leaves:
        group = resolve_scene_nav_group_key(leaf.get("scene_key") or "", aliases=aliases)
        if group not in configured_groups:
            group = "others"
        grouped.setdefault(group, []).append(leaf)

    out: list[tuple[int, str, dict]] = []
    for group, items in grouped.items():
        items_sorted = sorted(items, key=lambda x: str(x.get("label") or ""))
        label = str(labels.get(group) or "其他场景")
        order = int(order_map.get(group) or 999)
        out.append((order, label, build_scene_nav_group_node(group, label, items_sorted)))
    out.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in out]
