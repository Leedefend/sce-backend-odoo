#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_SOURCE_PATH = ROOT / "docs" / "product" / "delivery" / "v1" / "module_scene_capability_source_v1.json"
ROLE_SOURCE_PATH = ROOT / "docs" / "product" / "delivery" / "v1" / "role_package_source_v1.json"
STATE_PATH = ROOT / "artifacts" / "backend" / "scene_contract_v1_field_schema_state.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_module9_smoke_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_module9_smoke_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _norm(value: object) -> str:
    return str(value or "").strip()


def main() -> int:
    errors: list[str] = []

    module_source = _load_json(MODULE_SOURCE_PATH)
    role_source = _load_json(ROLE_SOURCE_PATH)
    state = _load_json(STATE_PATH)

    modules = [m for m in _as_list(module_source.get("modules")) if _as_dict(m).get("in_scope") is True]
    if len(modules) < 1:
        errors.append("in_scope_modules_empty")
    source_scope = _as_dict(module_source.get("delivery_scope"))
    source_scope_scenes = {
        _norm(item)
        for item in _as_list(source_scope.get("scene_keys"))
        if _norm(item)
    }

    contract = _as_dict(state.get("scene_ready_contract_v1"))
    scene_rows = _as_list(contract.get("scenes"))
    scene_keys = set()
    for row in scene_rows:
        scene = _as_dict(_as_dict(row).get("scene"))
        scene_key = _norm(scene.get("key"))
        if scene_key:
            scene_keys.add(scene_key)

    role_default_scenes = sorted(
        {
            _norm(role.get("default_scene"))
            for role in _as_list(role_source.get("roles"))
            if isinstance(role, dict) and _norm(role.get("default_scene"))
        }
    )

    checks: list[dict] = []
    for module in modules:
        mod = _as_dict(module)
        module_key = _norm(mod.get("module_key"))
        module_name = _norm(mod.get("module_name"))
        entry_scenes = [_norm(item) for item in _as_list(mod.get("entry_scenes")) if _norm(item)]

        missing: list[str] = []
        missing_out_of_scope: list[str] = []
        present: list[str] = []
        resolved_entry_scenes: dict[str, list[str]] = {}
        for item in entry_scenes:
            if item == "default":
                resolved_entry_scenes[item] = role_default_scenes
                missing_defaults = [scene for scene in role_default_scenes if scene not in scene_keys]
                if missing_defaults:
                    missing.append(f"default({','.join(missing_defaults)})")
                else:
                    present.append(item)
                continue
            if item in scene_keys:
                present.append(item)
            else:
                missing.append(item)
                if item not in source_scope_scenes:
                    missing_out_of_scope.append(item)

        checks.append(
            {
                "module_key": module_key,
                "module_name": module_name,
                "entry_scene_count": len(entry_scenes),
                "present_count": len(present),
                "missing_count": len(missing),
                "runtime_missing_count": len(missing),
                "missing_scenes": missing,
                "runtime_missing_scenes": missing,
                "missing_out_of_scope_scenes": missing_out_of_scope,
                "resolved_entry_scenes": resolved_entry_scenes,
                "runtime_ready": len(missing) == 0,
                "ok": len(missing_out_of_scope) == 0,
            }
        )

    failed = [item for item in checks if not bool(item.get("ok"))]
    if failed:
        errors.append(f"module_coverage_failed_count={len(failed)}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "module_count": len(checks),
            "pass_count": len(checks) - len(failed),
            "failed_count": len(failed),
            "runtime_ready_count": len([item for item in checks if item.get("runtime_ready")]),
            "runtime_pending_count": len([item for item in checks if not item.get("runtime_ready")]),
            "error_count": len(errors),
        },
        "checks": checks,
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Module Capability Smoke",
        "",
        f"- module_count: {report['summary']['module_count']}",
        f"- pass_count: {report['summary']['pass_count']}",
        f"- failed_count: {report['summary']['failed_count']}",
        f"- runtime_ready_count: {report['summary']['runtime_ready_count']}",
        f"- runtime_pending_count: {report['summary']['runtime_pending_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "| module | status | runtime_status | runtime_missing_scenes |",
        "|---|---|---|---|",
    ]
    for item in checks:
        status = "PASS" if item.get("ok") else "FAIL"
        runtime_status = "READY" if item.get("runtime_ready") else "PENDING_RUNTIME_SCENE"
        missing = ",".join(item.get("runtime_missing_scenes") or []) or "-"
        lines.append(f"| {item.get('module_name')} ({item.get('module_key')}) | {status} | {runtime_status} | {missing} |")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(REPORT_JSON)
    print(REPORT_MD)
    if errors:
        print("[product_delivery_module_capability_smoke] FAIL")
        return 2
    print("[product_delivery_module_capability_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
