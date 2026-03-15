#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_sample_registry_diff_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _text(value) -> str:
    return str(value or "").strip()


def _as_list(value):
    return value if isinstance(value, list) else []


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_sample_registry_diff_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    sample_baseline_path = ROOT / _text(baseline.get("sample_baseline"))
    snapshot_state_path = ROOT / _text(baseline.get("snapshot_state"))
    report_json_path = ROOT / _text(baseline.get("report_json") or "artifacts/backend/scene_sample_registry_diff_report.json")
    report_md_path = ROOT / _text(baseline.get("report_md") or "artifacts/backend/scene_sample_registry_diff_report.md")

    sample_baseline = _load_json(sample_baseline_path)
    snapshot_state = _load_json(snapshot_state_path)
    errors: list[str] = []
    warnings: list[str] = []
    if not sample_baseline:
        errors.append(f"missing or invalid sample baseline: {sample_baseline_path.relative_to(ROOT).as_posix()}")
    if not snapshot_state:
        errors.append(f"missing or invalid snapshot state: {snapshot_state_path.relative_to(ROOT).as_posix()}")
    if errors:
        print("[scene_sample_registry_diff_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    required_scene_keys = sorted({_text(item) for item in _as_list(sample_baseline.get("required_scene_keys")) if _text(item)})
    snapshot_scene_keys = sorted({_text(item) for item in _as_list(snapshot_state.get("scene_keys")) if _text(item)})
    per_scene = _as_dict(snapshot_state.get("per_scene"))

    missing_required_scene_keys = [key for key in required_scene_keys if key not in snapshot_scene_keys]
    unexpected_scene_keys = [key for key in snapshot_scene_keys if key not in required_scene_keys]
    matched_scene_keys = [key for key in required_scene_keys if key in snapshot_scene_keys]

    require_bound_when_matched = bool(baseline.get("require_base_contract_bound_when_matched", True))
    unbound_matched_scene_keys: list[str] = []
    for key in matched_scene_keys:
        scene_row = _as_dict(per_scene.get(key))
        if require_bound_when_matched and not bool(scene_row.get("base_contract_bound")):
            unbound_matched_scene_keys.append(key)

    scene_count = _safe_int(snapshot_state.get("scene_count"), len(snapshot_scene_keys))
    base_contract_bound_scene_count = _safe_int(snapshot_state.get("base_contract_bound_scene_count"), 0)
    max_missing_required_scene_count = _safe_int(baseline.get("max_missing_required_scene_count"), 0)
    max_unexpected_scene_count = _safe_int(baseline.get("max_unexpected_scene_count"), 200)

    strict_snapshot = _text(os.getenv("SC_SCENE_SAMPLE_REGISTRY_DIFF_REQUIRE_SCENES")).lower() in {"1", "true", "yes"}
    if scene_count <= 0 and not strict_snapshot:
        warnings.append("snapshot scene_count is 0; diff checks downgraded to warn")
    else:
        if len(missing_required_scene_keys) > max_missing_required_scene_count:
            errors.append(
                "missing required scene count exceeds threshold: "
                f"{len(missing_required_scene_keys)} > {max_missing_required_scene_count}; "
                f"missing={missing_required_scene_keys}"
            )
        if len(unexpected_scene_keys) > max_unexpected_scene_count:
            errors.append(
                "unexpected scene count exceeds threshold: "
                f"{len(unexpected_scene_keys)} > {max_unexpected_scene_count}"
            )
        if unbound_matched_scene_keys:
            errors.append(f"matched scenes not base-contract bound: {unbound_matched_scene_keys}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "scene_count": scene_count,
            "base_contract_bound_scene_count": base_contract_bound_scene_count,
            "required_scene_count": len(required_scene_keys),
            "matched_scene_count": len(matched_scene_keys),
            "missing_required_scene_count": len(missing_required_scene_keys),
            "unexpected_scene_count": len(unexpected_scene_keys),
            "unbound_matched_scene_count": len(unbound_matched_scene_keys),
        },
        "diff": {
            "required_scene_keys": required_scene_keys,
            "snapshot_scene_keys": snapshot_scene_keys,
            "matched_scene_keys": matched_scene_keys,
            "missing_required_scene_keys": missing_required_scene_keys,
            "unexpected_scene_keys": unexpected_scene_keys,
            "unbound_matched_scene_keys": unbound_matched_scene_keys,
        },
        "sources": {
            "sample_baseline": sample_baseline_path.relative_to(ROOT).as_posix(),
            "snapshot_state": snapshot_state_path.relative_to(ROOT).as_posix(),
            "guard_baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
        },
        "warnings": warnings,
        "errors": errors,
        "report": {
            "json": report_json_path.relative_to(ROOT).as_posix(),
            "md": report_md_path.relative_to(ROOT).as_posix(),
        },
    }

    markdown_lines = [
        "# Scene Sample vs Registry Diff Report",
        "",
        f"- scene_count: `{scene_count}`",
        f"- base_contract_bound_scene_count: `{base_contract_bound_scene_count}`",
        f"- required_scene_count: `{len(required_scene_keys)}`",
        f"- matched_scene_count: `{len(matched_scene_keys)}`",
        f"- missing_required_scene_count: `{len(missing_required_scene_keys)}`",
        f"- unexpected_scene_count: `{len(unexpected_scene_keys)}`",
        f"- unbound_matched_scene_count: `{len(unbound_matched_scene_keys)}`",
    ]
    if warnings:
        markdown_lines.extend(["", "## Warnings"] + [f"- {item}" for item in warnings])
    if errors:
        markdown_lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(markdown_lines) + "\n")

    if errors:
        print(report_json_path)
        print(report_md_path)
        print("[scene_sample_registry_diff_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    for warning in warnings:
        print(f"[scene_sample_registry_diff_guard] WARN {warning}")
    print(report_json_path)
    print(report_md_path)
    print("[scene_sample_registry_diff_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

