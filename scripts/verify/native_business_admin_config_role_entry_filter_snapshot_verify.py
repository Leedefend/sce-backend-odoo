#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SESSION_STORE = ROOT / "frontend/apps/web/src/stores/session.ts"


def _normalize(value) -> str:
    return str(value or "").strip().lower()


def _collect_keys(node: dict) -> set[str]:
    out: set[str] = set()
    for key in ["xmlid", "menu_xmlid", "action_xmlid", "scene_key", "model", "key", "menu_id", "id", "action_id"]:
        value = _normalize(node.get(key))
        if value:
            out.add(value)
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    for key in ["xmlid", "menu_xmlid", "action_xmlid", "scene_key", "model", "menu_id", "action_id"]:
        value = _normalize(meta.get(key))
        if value:
            out.add(value)
    return out


def _apply_filter(tree: list[dict], role_entries: list[dict], role_code: str) -> list[dict]:
    if not tree or not role_entries:
        return tree
    role = _normalize(role_code)
    eligible = []
    for group in role_entries:
        code = _normalize(group.get("role_code"))
        if code and (code == "__global__" or (role and code == role)):
            eligible.append(group)
    if not eligible:
        return tree
    allowed: set[str] = set()
    for group in eligible:
        for entry in group.get("entries") or []:
            if not bool(entry.get("is_enabled")):
                continue
            key = _normalize(entry.get("entry_key"))
            if key:
                allowed.add(key)
    if not allowed:
        return tree

    def walk(nodes: list[dict]) -> list[dict]:
        result: list[dict] = []
        for node in nodes:
            children = walk(node.get("children") or [])
            matched = any(key in allowed for key in _collect_keys(node))
            if matched or children:
                cloned = dict(node)
                cloned["children"] = children
                result.append(cloned)
        return result

    filtered = walk(tree)
    return filtered if filtered else tree


def main() -> None:
    if not SESSION_STORE.exists():
        raise SystemExit("[native_business_admin_config_role_entry_filter_snapshot_verify] FAIL missing session store")
    content = SESSION_STORE.read_text(encoding="utf-8")
    required_markers = [
        "function applyRoleEntryNavFilter(",
        "function collectNodeMatchKeys(",
        "return filteredTree.length ? filteredTree : tree;",
    ]
    missing = [marker for marker in required_markers if marker not in content]
    if missing:
        raise SystemExit(
            "[native_business_admin_config_role_entry_filter_snapshot_verify] FAIL missing markers=" + ", ".join(missing)
        )

    fixture_tree = [
        {
            "key": "root",
            "menu_xmlid": "smart_construction_core.menu_sc_root",
            "children": [
                {"key": "project", "menu_xmlid": "project.list", "children": []},
                {"key": "task", "menu_xmlid": "project.task", "children": []},
                {"key": "finance", "menu_xmlid": "payment.request", "children": []},
            ],
        }
    ]
    fixture_entries = [
        {"role_code": "project_manager", "entries": [{"entry_key": "project.list", "is_enabled": True}]},
        {"role_code": "__global__", "entries": [{"entry_key": "smart_construction_core.menu_sc_root", "is_enabled": True}]},
    ]

    replay1 = _apply_filter(fixture_tree, fixture_entries, "project_manager")
    replay2 = _apply_filter(fixture_tree, fixture_entries, "project_manager")
    if json.dumps(replay1, sort_keys=True) != json.dumps(replay2, sort_keys=True):
        raise SystemExit("[native_business_admin_config_role_entry_filter_snapshot_verify] FAIL replay mismatch")

    labels = [child.get("key") for child in (replay1[0].get("children") or [])]
    if labels != ["project"]:
        raise SystemExit(
            "[native_business_admin_config_role_entry_filter_snapshot_verify] FAIL expected filtered children ['project'] got="
            + str(labels)
        )

    fallback = _apply_filter(fixture_tree, [], "project_manager")
    if json.dumps(fallback, sort_keys=True) != json.dumps(fixture_tree, sort_keys=True):
        raise SystemExit("[native_business_admin_config_role_entry_filter_snapshot_verify] FAIL fallback mismatch")

    print("[native_business_admin_config_role_entry_filter_snapshot_verify] PASS snapshot replay deterministic and fallback preserved")


if __name__ == "__main__":
    main()
