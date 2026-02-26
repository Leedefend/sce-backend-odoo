#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_menu_tree_source_v1.json"
MODULE_SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "module_scene_capability_source_v1.json"
SCENE_MAP_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "delivery_menu_tree_v1.json"
ENTRY_MODULE_INDEX_JSON = ROOT / "artifacts" / "product" / "menu_entry_module_index.json"
REPORT_MD = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_menu_tree_v1.md"
POLICY_MD = ROOT / "docs" / "product" / "delivery" / "v1" / "entry_visibility_policy.md"
GUARD_JSON = ROOT / "artifacts" / "backend" / "delivery_menu_tree_guard_report.json"
GUARD_MD = ROOT / "docs" / "ops" / "audit" / "delivery_menu_tree_guard_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    src = _load(SOURCE_JSON)
    module_src = _load(MODULE_SOURCE_JSON)
    scene_map = _load(SCENE_MAP_JSON)

    menu_tree = src.get("menu_tree") if isinstance(src.get("menu_tree"), list) else []
    delivery_role_keys = sorted({_norm(x) for x in (src.get("delivery_role_keys") if isinstance(src.get("delivery_role_keys"), list) else []) if _norm(x)})
    visibility_mechanism = (
        src.get("visibility_mechanism") if isinstance(src.get("visibility_mechanism"), dict) else {}
    )
    hidden = sorted({_norm(x) for x in (src.get("hidden_for_delivery_roles") if isinstance(src.get("hidden_for_delivery_roles"), list) else []) if _norm(x)})
    delivery_scope = sorted({_norm(x) for x in ((module_src.get("delivery_scope") or {}).get("scene_keys") if isinstance((module_src.get("delivery_scope") or {}).get("scene_keys"), list) else []) if _norm(x)})
    modules = module_src.get("modules") if isinstance(module_src.get("modules"), list) else []

    scene_rows = scene_map.get("scene_to_domain") if isinstance(scene_map.get("scene_to_domain"), list) else []
    valid_scenes = {
        _norm(r.get("canonical_scene"))
        for r in scene_rows
        if isinstance(r, dict) and _norm(r.get("canonical_scene"))
    }

    first_level_count = len(menu_tree)
    all_entries = []
    for row in menu_tree:
        if not isinstance(row, dict):
            continue
        entries = [_norm(x) for x in (row.get("entries") if isinstance(row.get("entries"), list) else []) if _norm(x)]
        all_entries.extend(entries)

    unique_entries = sorted(set(all_entries))
    total_entries = len(unique_entries)

    if first_level_count > 8:
        errors.append(f"first_level_count_exceeds_8={first_level_count}")
    if total_entries > 30:
        errors.append(f"total_entry_count_exceeds_30={total_entries}")

    duplicate_entries = sorted({e for e in all_entries if all_entries.count(e) > 1})
    if duplicate_entries:
        errors.append(f"duplicate_entry_count={len(duplicate_entries)}")

    invalid_scene = [s for s in unique_entries if s not in valid_scenes]
    if invalid_scene:
        errors.append(f"invalid_scene_ref_count={len(invalid_scene)}")

    missing_scope_scene = [s for s in delivery_scope if s not in unique_entries and s not in hidden]
    if missing_scope_scene:
        errors.append(f"scope_scene_not_explained_count={len(missing_scope_scene)}")

    scene_to_module: dict[str, str] = {}
    module_index_rows = []
    for m in modules:
        if not isinstance(m, dict):
            continue
        module_key = _norm(m.get("module_key"))
        module_name = _norm(m.get("module_name"))
        for s in sorted({_norm(x) for x in (m.get("entry_scenes") if isinstance(m.get("entry_scenes"), list) else []) if _norm(x)}):
            owner = scene_to_module.get(s)
            if owner and owner != module_key:
                errors.append(f"entry_scene_multi_module={s} ({owner},{module_key})")
                continue
            scene_to_module[s] = module_key
            module_index_rows.append(
                {"scene_key": s, "module_key": module_key, "module_name": module_name}
            )
    module_index_rows = sorted(module_index_rows, key=lambda x: (x["scene_key"], x["module_key"]))
    unmapped_entries = [s for s in unique_entries if s not in scene_to_module]
    if unmapped_entries:
        errors.append(f"menu_entry_unmapped_module_count={len(unmapped_entries)}")

    missing_mechanism_fields = []
    for k in ("scene_tag_field", "role_resolution_source", "filter_layer", "frontend_behavior"):
        if not _norm(visibility_mechanism.get(k)):
            missing_mechanism_fields.append(k)
    tag_values = visibility_mechanism.get("tag_values") if isinstance(visibility_mechanism.get("tag_values"), dict) else {}
    if not _norm(tag_values.get("delivery_visible")) or not _norm(tag_values.get("internal_only")):
        missing_mechanism_fields.append("tag_values.delivery_visible/internal_only")
    if not delivery_role_keys:
        missing_mechanism_fields.append("delivery_role_keys")
    if missing_mechanism_fields:
        errors.append(f"missing_visibility_mechanism_field_count={len(missing_mechanism_fields)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "version": _norm(src.get("version") or "unknown"),
            "first_level_count": first_level_count,
            "total_entry_count": total_entries,
            "hidden_count": len(hidden),
            "delivery_role_count": len(delivery_role_keys),
            "delivery_scope_scene_count": len(delivery_scope),
            "scope_scene_not_explained_count": len(missing_scope_scene),
            "invalid_scene_ref_count": len(invalid_scene),
            "menu_entry_unmapped_module_count": len(unmapped_entries),
            "error_count": len(errors),
            "warning_count": len(warnings)
        },
        "menu_tree": menu_tree,
        "entries": unique_entries,
        "entry_module_index": module_index_rows,
        "delivery_role_keys": delivery_role_keys,
        "hidden_for_delivery_roles": hidden,
        "missing_scope_scene": missing_scope_scene,
        "invalid_scene_ref": invalid_scene,
        "unmapped_entries": unmapped_entries,
        "visibility_mechanism": visibility_mechanism,
        "errors": errors,
        "warnings": warnings
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ENTRY_MODULE_INDEX_JSON.parent.mkdir(parents=True, exist_ok=True)
    ENTRY_MODULE_INDEX_JSON.write_text(
        json.dumps(
            {
                "ok": len(unmapped_entries) == 0,
                "summary": {
                    "entry_count": len(unique_entries),
                    "mapped_entry_count": len(module_index_rows),
                    "unmapped_entry_count": len(unmapped_entries),
                },
                "rows": module_index_rows,
                "unmapped_entries": unmapped_entries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    GUARD_JSON.parent.mkdir(parents=True, exist_ok=True)
    GUARD_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Delivery Menu Tree V1",
        "",
        f"- version: {payload['summary']['version']}",
        f"- first_level_count: {first_level_count}",
        f"- total_entry_count: {total_entries}",
        f"- hidden_count: {len(hidden)}",
        f"- delivery_role_count: {len(delivery_role_keys)}",
        f"- menu_entry_unmapped_module_count: {len(unmapped_entries)}",
        f"- error_count: {len(errors)}",
        "",
        "## Menu Tree",
        ""
    ]
    for row in menu_tree:
        name = _norm(row.get("menu_name"))
        entries = row.get("entries") if isinstance(row.get("entries"), list) else []
        lines.append(f"- {name} ({_norm(row.get('menu_key'))})")
        lines.append(f"  - entries: {', '.join(entries)}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    policy_lines = [
        "# Entry Visibility Policy",
        "",
        "## Objective",
        "- Keep delivery roles focused on <=30 business-facing entries without deleting internal/debug paths.",
        "",
        "## Policy",
        "- delivery roles: only entries listed in `delivery_menu_tree_v1` are visible.",
        "- internal/admin roles: can still access entries tagged `internal_only`.",
        "- non-delivery entries are hidden by visibility tag, not removed.",
        "",
        "## Mechanism",
        f"- scene tag field: `{_norm(visibility_mechanism.get('scene_tag_field')) or '-'}`",
        f"- delivery roles source: `{_norm(visibility_mechanism.get('role_resolution_source')) or '-'}`",
        f"- filter layer: `{_norm(visibility_mechanism.get('filter_layer')) or '-'}`",
        f"- frontend behavior: `{_norm(visibility_mechanism.get('frontend_behavior')) or '-'}`",
        f"- delivery role keys: {', '.join(delivery_role_keys) if delivery_role_keys else '-'}",
        "",
        "## Hidden Entries (V1)",
    ]
    for item in hidden:
        policy_lines.append(f"- {item}: internal_only")
    POLICY_MD.parent.mkdir(parents=True, exist_ok=True)
    POLICY_MD.write_text("\n".join(policy_lines) + "\n", encoding="utf-8")

    guard_lines = [
        "# Delivery Menu Tree Guard Report",
        "",
        f"- first_level_count: {first_level_count}",
        f"- total_entry_count: {total_entries}",
        f"- invalid_scene_ref_count: {len(invalid_scene)}",
        f"- scope_scene_not_explained_count: {len(missing_scope_scene)}",
        f"- menu_entry_unmapped_module_count: {len(unmapped_entries)}",
        f"- delivery_role_count: {len(delivery_role_keys)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
    ]
    GUARD_MD.parent.mkdir(parents=True, exist_ok=True)
    GUARD_MD.write_text("\n".join(guard_lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print(str(ENTRY_MODULE_INDEX_JSON))
    print(str(POLICY_MD))
    print(str(GUARD_MD))
    print(str(GUARD_JSON))
    if errors:
        print("[delivery_menu_tree_report] FAIL")
        return 2
    print("[delivery_menu_tree_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
