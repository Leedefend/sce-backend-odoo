#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "module_scene_capability_source_v1.json"
SCENE_MAP_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
CAP_USAGE_JSON = ROOT / "artifacts" / "backend" / "capability_usage_matrix.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "module_scene_capability_map.json"
REPORT_MD = ROOT / "docs" / "product" / "delivery" / "v1" / "module_scene_capability_map.md"


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

    source = _load(SOURCE_JSON)
    scene_map = _load(SCENE_MAP_JSON)
    cap_usage = _load(CAP_USAGE_JSON)

    modules = source.get("modules") if isinstance(source.get("modules"), list) else []
    scope = source.get("delivery_scope") if isinstance(source.get("delivery_scope"), dict) else {}
    scope_scenes = sorted({_norm(x) for x in (scope.get("scene_keys") if isinstance(scope.get("scene_keys"), list) else []) if _norm(x)})

    if not modules:
        errors.append("modules empty")
    if len(modules) > 10:
        errors.append(f"module_count_exceeds_10={len(modules)}")
    if not scope_scenes:
        errors.append("delivery scope scenes empty")

    canonical_rows = scene_map.get("scene_to_domain") if isinstance(scene_map.get("scene_to_domain"), list) else []
    canonical_scene_set = {
        _norm(row.get("canonical_scene"))
        for row in canonical_rows
        if isinstance(row, dict) and _norm(row.get("canonical_scene"))
    }

    cap_rows = cap_usage.get("rows") if isinstance(cap_usage.get("rows"), list) else []
    capability_set = {
        _norm(row.get("capability_key"))
        for row in cap_rows
        if isinstance(row, dict) and _norm(row.get("capability_key"))
    }

    scene_owner: dict[str, str] = {}
    module_rows: list[dict] = []
    unknown_scene_refs: list[str] = []
    unknown_capability_refs: list[str] = []

    for item in modules:
        if not isinstance(item, dict):
            continue
        module_key = _norm(item.get("module_key"))
        module_name = _norm(item.get("module_name"))
        entry_scenes = sorted({_norm(x) for x in (item.get("entry_scenes") if isinstance(item.get("entry_scenes"), list) else []) if _norm(x)})
        capabilities = sorted({_norm(x) for x in (item.get("capabilities") if isinstance(item.get("capabilities"), list) else []) if _norm(x)})

        if not module_key or not module_name:
            errors.append(f"invalid module identity: {module_key or module_name or 'unknown'}")
            continue
        if not entry_scenes:
            errors.append(f"{module_key}: entry_scenes empty")
        if not capabilities:
            warnings.append(f"{module_key}: capabilities empty")

        for s in entry_scenes:
            if s not in canonical_scene_set:
                unknown_scene_refs.append(f"{module_key}:{s}")
            owner = scene_owner.get(s)
            if owner and owner != module_key:
                errors.append(f"scene_multi_owner={s} ({owner},{module_key})")
            else:
                scene_owner[s] = module_key

        for c in capabilities:
            if c not in capability_set:
                unknown_capability_refs.append(f"{module_key}:{c}")

        module_rows.append(
            {
                "module_key": module_key,
                "module_name": module_name,
                "target_roles": item.get("target_roles") if isinstance(item.get("target_roles"), list) else [],
                "core_value": _norm(item.get("core_value")),
                "entry_scenes": entry_scenes,
                "menu_hints": item.get("menu_hints") if isinstance(item.get("menu_hints"), list) else [],
                "models": item.get("models") if isinstance(item.get("models"), list) else [],
                "capabilities": capabilities,
                "in_scope": bool(item.get("in_scope", True)),
            }
        )

    unassigned_scope_scenes = [s for s in scope_scenes if s not in scene_owner]
    if unassigned_scope_scenes:
        errors.append(f"unassigned_scope_scene_count={len(unassigned_scope_scenes)}")
    if unknown_scene_refs:
        errors.append(f"unknown_scene_ref_count={len(unknown_scene_refs)}")
    if unknown_capability_refs:
        errors.append(f"unknown_capability_ref_count={len(unknown_capability_refs)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "version": _norm(source.get("version") or "unknown"),
            "module_count": len(module_rows),
            "delivery_scope_scene_count": len(scope_scenes),
            "assigned_scope_scene_count": len(scope_scenes) - len(unassigned_scope_scenes),
            "unassigned_scope_scene_count": len(unassigned_scope_scenes),
            "unknown_scene_ref_count": len(unknown_scene_refs),
            "unknown_capability_ref_count": len(unknown_capability_refs),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "modules": module_rows,
        "delivery_scope_scenes": scope_scenes,
        "unassigned_scope_scenes": unassigned_scope_scenes,
        "unknown_scene_refs": unknown_scene_refs,
        "unknown_capability_refs": unknown_capability_refs,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Module Scene Capability Map V1",
        "",
        f"- version: {payload['summary']['version']}",
        f"- module_count: {payload['summary']['module_count']}",
        f"- delivery_scope_scene_count: {payload['summary']['delivery_scope_scene_count']}",
        f"- assigned_scope_scene_count: {payload['summary']['assigned_scope_scene_count']}",
        f"- unassigned_scope_scene_count: {payload['summary']['unassigned_scope_scene_count']}",
        f"- unknown_scene_ref_count: {payload['summary']['unknown_scene_ref_count']}",
        f"- unknown_capability_ref_count: {payload['summary']['unknown_capability_ref_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "## Acceptance",
        "",
        f"- module_count_le_10: {'PASS' if len(module_rows) <= 10 else 'FAIL'}",
        f"- each_module_has_scene: {'PASS' if all(m.get('entry_scenes') for m in module_rows) else 'FAIL'}",
        f"- scope_scene_unassigned_eq_0: {'PASS' if len(unassigned_scope_scenes) == 0 else 'FAIL'}",
        f"- unknown_scene_ref_eq_0: {'PASS' if len(unknown_scene_refs) == 0 else 'FAIL'}",
        f"- unknown_capability_ref_eq_0: {'PASS' if len(unknown_capability_refs) == 0 else 'FAIL'}",
        "",
        "| module_key | module_name | target_roles | entry_scenes | capabilities |",
        "|---|---|---|---|---|",
    ]
    for m in module_rows:
        lines.append(
            f"| {m['module_key']} | {m['module_name']} | {','.join(m['target_roles']) if m['target_roles'] else '-'} | "
            f"{','.join(m['entry_scenes']) if m['entry_scenes'] else '-'} | {','.join(m['capabilities']) if m['capabilities'] else '-'} |"
        )

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[module_scene_capability_map_report] FAIL")
        return 2
    print("[module_scene_capability_map_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
