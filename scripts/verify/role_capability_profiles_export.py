#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "role_package_source_v1.json"
MODULE_SOURCE_JSON = ROOT / "docs" / "product" / "delivery" / "v1" / "module_scene_capability_source_v1.json"
SCENE_MAP_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
CAP_USAGE_JSON = ROOT / "artifacts" / "backend" / "capability_usage_matrix.json"
REPORT_JSON = ROOT / "artifacts" / "product" / "role_capability_profiles.json"
REPORT_MD = ROOT / "docs" / "product" / "delivery" / "v1" / "role_capability_profiles.md"
GUARD_JSON = ROOT / "artifacts" / "backend" / "role_capability_profiles_guard_report.json"
GUARD_MD = ROOT / "docs" / "ops" / "audit" / "role_capability_profiles_guard_report.md"


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

    role_src = _load(ROLE_SOURCE_JSON)
    module_src = _load(MODULE_SOURCE_JSON)
    scene_map = _load(SCENE_MAP_JSON)
    cap_usage = _load(CAP_USAGE_JSON)

    roles = role_src.get("roles") if isinstance(role_src.get("roles"), list) else []
    modules = module_src.get("modules") if isinstance(module_src.get("modules"), list) else []
    if not roles:
        errors.append("roles empty")
    if len(roles) > 6:
        errors.append(f"role_count_exceeds_6={len(roles)}")

    scene_rows = scene_map.get("scene_to_domain") if isinstance(scene_map.get("scene_to_domain"), list) else []
    valid_scene = {
        _norm(r.get("canonical_scene"))
        for r in scene_rows
        if isinstance(r, dict) and _norm(r.get("canonical_scene"))
    }
    cap_rows = cap_usage.get("rows") if isinstance(cap_usage.get("rows"), list) else []
    valid_caps = {
        _norm(r.get("capability_key"))
        for r in cap_rows
        if isinstance(r, dict) and _norm(r.get("capability_key"))
    }

    module_index = {}
    for m in modules:
        if not isinstance(m, dict):
            continue
        key = _norm(m.get("module_key"))
        if not key:
            continue
        module_index[key] = {
            "module_name": _norm(m.get("module_name")),
            "capabilities": sorted({_norm(x) for x in (m.get("capabilities") if isinstance(m.get("capabilities"), list) else []) if _norm(x)}),
            "entry_scenes": sorted({_norm(x) for x in (m.get("entry_scenes") if isinstance(m.get("entry_scenes"), list) else []) if _norm(x)}),
        }

    profile_rows = []
    unresolved_modules = []
    unresolved_caps = []
    unresolved_default_scenes = []

    for role in roles:
        if not isinstance(role, dict):
            continue
        role_key = _norm(role.get("role_key"))
        role_name = _norm(role.get("role_name"))
        default_scene = _norm(role.get("default_scene"))
        visible_modules = [_norm(x) for x in (role.get("visible_modules") if isinstance(role.get("visible_modules"), list) else []) if _norm(x)]
        hidden_modules = [_norm(x) for x in (role.get("hidden_modules") if isinstance(role.get("hidden_modules"), list) else []) if _norm(x)]

        if not role_key or not role_name:
            errors.append("invalid role identity")
            continue
        if not default_scene:
            errors.append(f"{role_key}: default_scene missing")
        elif default_scene not in valid_scene:
            unresolved_default_scenes.append(f"{role_key}:{default_scene}")

        module_caps = set()
        module_entries = set()
        for mk in visible_modules:
            m = module_index.get(mk)
            if not m:
                unresolved_modules.append(f"{role_key}:{mk}")
                continue
            module_caps.update(m["capabilities"])
            module_entries.update(m["entry_scenes"])

        for c in sorted(module_caps):
            if c not in valid_caps:
                unresolved_caps.append(f"{role_key}:{c}")

        profile_rows.append(
            {
                "role_key": role_key,
                "role_name": role_name,
                "responsibility": _norm(role.get("responsibility")),
                "default_scene": default_scene,
                "visible_modules": sorted(visible_modules),
                "hidden_modules": sorted(hidden_modules),
                "entry_scenes": sorted(module_entries),
                "capability_keys": sorted(module_caps),
                "capability_count": len(module_caps),
            }
        )

    if unresolved_modules:
        errors.append(f"unresolved_module_ref_count={len(unresolved_modules)}")
    if unresolved_caps:
        errors.append(f"unresolved_capability_ref_count={len(unresolved_caps)}")
    if unresolved_default_scenes:
        errors.append(f"unresolved_default_scene_count={len(unresolved_default_scenes)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "version": _norm(role_src.get("version") or "unknown"),
            "role_count": len(profile_rows),
            "unresolved_module_ref_count": len(unresolved_modules),
            "unresolved_capability_ref_count": len(unresolved_caps),
            "unresolved_default_scene_count": len(unresolved_default_scenes),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "profiles": profile_rows,
        "unresolved_modules": unresolved_modules,
        "unresolved_capabilities": unresolved_caps,
        "unresolved_default_scenes": unresolved_default_scenes,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    GUARD_JSON.parent.mkdir(parents=True, exist_ok=True)
    GUARD_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Role Capability Profiles V1",
        "",
        f"- version: {payload['summary']['version']}",
        f"- role_count: {payload['summary']['role_count']}",
        f"- unresolved_module_ref_count: {payload['summary']['unresolved_module_ref_count']}",
        f"- unresolved_capability_ref_count: {payload['summary']['unresolved_capability_ref_count']}",
        f"- unresolved_default_scene_count: {payload['summary']['unresolved_default_scene_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        "",
        "| role | default_scene | visible_modules | capability_count |",
        "|---|---|---|---:|",
    ]
    for row in profile_rows:
        lines.append(
            f"| {row['role_name']} ({row['role_key']}) | {row['default_scene']} | "
            f"{','.join(row['visible_modules']) if row['visible_modules'] else '-'} | {row['capability_count']} |"
        )

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    guard_lines = [
        "# Role Capability Profiles Guard Report",
        "",
        f"- role_count: {payload['summary']['role_count']}",
        f"- unresolved_module_ref_count: {payload['summary']['unresolved_module_ref_count']}",
        f"- unresolved_capability_ref_count: {payload['summary']['unresolved_capability_ref_count']}",
        f"- unresolved_default_scene_count: {payload['summary']['unresolved_default_scene_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
    ]
    GUARD_MD.parent.mkdir(parents=True, exist_ok=True)
    GUARD_MD.write_text("\n".join(guard_lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print(str(GUARD_MD))
    print(str(GUARD_JSON))
    if errors:
        print("[role_capability_profiles_export] FAIL")
        return 2
    print("[role_capability_profiles_export] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
