#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_engine_migration_matrix_guard.json"
DEFAULT_FIELD_SCHEMA_STATE_PATH = ROOT / "artifacts" / "backend" / "scene_contract_v1_field_schema_state.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _text(value).lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _derive_runtime_state_from_scene_ready(payload: dict) -> dict:
    ready = _as_dict(payload.get("scene_ready_contract_v1")) if isinstance(payload.get("scene_ready_contract_v1"), dict) else payload
    if not ready:
        return {}
    scene_meta = _as_dict(ready.get("meta"))
    scenes = _as_list(ready.get("scenes"))
    if not scenes:
        return {}

    per_scene: dict[str, dict[str, Any]] = {}
    source_kind_counts = {
        "asset": 0,
        "runtime_fallback": 0,
        "runtime_minimal": 0,
        "inline": 0,
        "none": 0,
        "other": 0,
    }
    scene_keys: list[str] = []
    for row in scenes:
        item = _as_dict(row)
        scene_key = _text(_as_dict(item.get("scene")).get("key"))
        if not scene_key:
            continue
        scene_keys.append(scene_key)
        meta = _as_dict(item.get("meta"))
        verdict = _as_dict(meta.get("compile_verdict"))
        source_meta = _as_dict(meta.get("ui_base_contract_source"))
        source_kind = _text(source_meta.get("kind")) or "none"
        if source_kind not in source_kind_counts:
            source_kind = "other"
        source_kind_counts[source_kind] = _safe_int(source_kind_counts.get(source_kind), 0) + 1
        action_total = _safe_int(_as_dict(_as_dict(item.get("action_surface")).get("counts")).get("total"), 0)
        per_scene[scene_key] = {
            "base_contract_bound": bool(verdict.get("base_contract_bound")),
            "compile_ok": bool(verdict.get("ok")),
            "source_kind": source_kind,
            "action_total": action_total,
        }

    total_scene_count = _safe_int(scene_meta.get("scene_count"), len(scene_keys))
    denom = float(total_scene_count) if total_scene_count > 0 else 1.0
    source_kind_ratios = {
        key: float(_safe_int(value, 0)) / denom
        for key, value in source_kind_counts.items()
    }
    return {
        "scene_count": total_scene_count,
        "base_contract_bound_scene_count": _safe_int(scene_meta.get("base_contract_bound_scene_count"), 0),
        "compile_issue_scene_count": _safe_int(scene_meta.get("compile_issue_scene_count"), 0),
        "scene_keys": sorted(set(scene_keys)),
        "source_kind_counts": source_kind_counts,
        "source_kind_ratios": source_kind_ratios,
        "per_scene": per_scene,
    }


def _load_runtime_state(state_path: Path) -> tuple[dict, str]:
    field_schema_state = _load_json(DEFAULT_FIELD_SCHEMA_STATE_PATH)
    derived_state = _derive_runtime_state_from_scene_ready(field_schema_state)
    if derived_state:
        return derived_state, DEFAULT_FIELD_SCHEMA_STATE_PATH.relative_to(ROOT).as_posix()
    fallback_state = _load_json(state_path)
    if fallback_state:
        return fallback_state, state_path.relative_to(ROOT).as_posix()
    return {}, state_path.relative_to(ROOT).as_posix()


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_engine_migration_matrix_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    module_map_path = ROOT / _text(
        baseline.get("module_map_file") or "artifacts/product/module_scene_capability_map.json"
    )
    state_path = ROOT / _text(
        baseline.get("state_file") or "artifacts/backend/scene_registry_asset_snapshot_state.json"
    )
    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_engine_migration_matrix_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_engine_migration_matrix_report.md"
    )

    max_non_asset_entry_scene_count = _safe_int(baseline.get("max_non_asset_entry_scene_count"), 0)
    min_action_total = _safe_int(baseline.get("min_action_total"), 2)
    require_in_scope_only = _safe_bool(baseline.get("require_in_scope_only"), True)
    allowed_non_asset_entry_scenes = {
        _text(item) for item in _as_list(baseline.get("allowed_non_asset_entry_scenes")) if _text(item)
    }
    allowed_missing_scene_state = {
        _text(item) for item in _as_list(baseline.get("allowed_missing_scene_state")) if _text(item)
    }

    module_map = _load_json(module_map_path)
    state, effective_state_source = _load_runtime_state(state_path)
    if not module_map:
        print("[scene_engine_migration_matrix_guard] FAIL")
        print(f" - missing module map: {module_map_path.relative_to(ROOT).as_posix()}")
        return 1
    if not state:
        print("[scene_engine_migration_matrix_guard] FAIL")
        print(f" - missing runtime state: {state_path.relative_to(ROOT).as_posix()}")
        return 1

    per_scene = _as_dict(state.get("per_scene"))
    modules = _as_list(module_map.get("modules"))

    errors: list[str] = []
    non_asset_entry_scenes: list[str] = []
    module_reports: list[dict[str, Any]] = []

    for module in modules:
        row = _as_dict(module)
        module_key = _text(row.get("module_key"))
        in_scope = bool(row.get("in_scope"))
        if require_in_scope_only and not in_scope:
            continue
        entry_scenes = [_text(item) for item in _as_list(row.get("entry_scenes")) if _text(item)]
        entry_rows = []
        for scene_key in entry_scenes:
            scene_state = _as_dict(per_scene.get(scene_key))
            source_kind = _text(scene_state.get("source_kind"))
            action_total = _safe_int(scene_state.get("action_total"), 0)
            base_contract_bound = bool(scene_state.get("base_contract_bound"))
            compile_ok = bool(scene_state.get("compile_ok"))
            exists = scene_key in per_scene
            if not exists and scene_key not in allowed_missing_scene_state:
                errors.append(f"{module_key}: missing scene state for {scene_key}")
            if source_kind != "asset" and scene_key not in allowed_non_asset_entry_scenes:
                non_asset_entry_scenes.append(scene_key)
            # Runtime startup-subset payloads may expose non-asset rows without compile/bound facts.
            # Keep strict checks for asset-backed rows only.
            if exists and source_kind == "asset":
                if action_total < min_action_total:
                    errors.append(f"{module_key}:{scene_key} action_total {action_total} < {min_action_total}")
                if not base_contract_bound:
                    errors.append(f"{module_key}:{scene_key} base_contract_bound is false")
                if not compile_ok:
                    errors.append(f"{module_key}:{scene_key} compile_ok is false")
            entry_rows.append(
                {
                    "scene_key": scene_key,
                    "exists": exists,
                    "source_kind": source_kind,
                    "action_total": action_total,
                    "base_contract_bound": base_contract_bound,
                    "compile_ok": compile_ok,
                }
            )

        module_reports.append(
            {
                "module_key": module_key,
                "module_name": _text(row.get("module_name")),
                "in_scope": in_scope,
                "entry_scene_count": len(entry_scenes),
                "entry_rows": entry_rows,
            }
        )

    unique_non_asset = sorted(set(non_asset_entry_scenes))
    if len(unique_non_asset) > max_non_asset_entry_scene_count:
        errors.append(
            f"non-asset entry scene count {len(unique_non_asset)} > {max_non_asset_entry_scene_count}; "
            f"scenes={unique_non_asset}"
        )

    report = {
        "ok": len(errors) == 0,
        "errors": errors,
        "module_count": len(module_reports),
        "non_asset_entry_scene_count": len(unique_non_asset),
        "non_asset_entry_scenes": unique_non_asset,
        "modules": module_reports,
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "module_map_file": module_map_path.relative_to(ROOT).as_posix(),
            "state_file": effective_state_source,
        },
    }

    lines = ["# Scene Engine Migration Matrix Report", ""]
    lines.append(f"- module_count: `{len(module_reports)}`")
    lines.append(f"- non_asset_entry_scene_count: `{len(unique_non_asset)}`")
    if unique_non_asset:
        lines.append(f"- non_asset_entry_scenes: `{unique_non_asset}`")
    lines.append("")
    for module in module_reports:
        lines.append(f"## {module['module_key']} ({module['module_name']})")
        for item in _as_list(module.get("entry_rows")):
            row = _as_dict(item)
            lines.append(
                f"- {row.get('scene_key')}: source={row.get('source_kind')} action_total={row.get('action_total')} "
                f"bound={row.get('base_contract_bound')} compile_ok={row.get('compile_ok')}"
            )
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_engine_migration_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_engine_migration_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
