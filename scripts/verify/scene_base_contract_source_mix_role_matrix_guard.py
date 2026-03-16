#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_base_contract_source_mix_role_matrix_guard.json"


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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
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


def _merge_threshold(default_policy: dict, role_policy: dict) -> dict:
    merged = dict(default_policy)
    for key in ("min_scene_count", "min_asset_ratio", "max_runtime_minimal_ratio", "max_none_ratio"):
        if key in role_policy:
            merged[key] = role_policy.get(key)
    return merged


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_base_contract_source_mix_role_matrix_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    roles = [_text(item) for item in _as_list(baseline.get("roles")) if _text(item)]
    if not roles:
        print("[scene_base_contract_source_mix_role_matrix_guard] FAIL")
        print(" - roles is empty")
        return 1

    state_files = _as_dict(baseline.get("state_files"))
    role_thresholds = _as_dict(baseline.get("role_thresholds"))
    default_threshold = _as_dict(role_thresholds.get("default"))

    report_json_path = ROOT / _text(
        baseline.get("report_json") or "artifacts/backend/scene_base_contract_source_mix_role_matrix_report.json"
    )
    report_md_path = ROOT / _text(
        baseline.get("report_md") or "artifacts/backend/scene_base_contract_source_mix_role_matrix_report.md"
    )

    errors: list[str] = []
    role_reports: dict[str, dict[str, Any]] = {}
    for role in roles:
        state_rel = _text(state_files.get(role))
        if not state_rel:
            errors.append(f"missing state file mapping for role: {role}")
            continue
        state_path = ROOT / state_rel
        state = _load_json(state_path)
        if not state:
            errors.append(f"missing or invalid state for role {role}: {state_rel}")
            continue

        role_policy = _as_dict(role_thresholds.get(role))
        threshold = _merge_threshold(default_threshold, role_policy)
        scene_count = _safe_int(state.get("scene_count"), 0)

        kind_ratios = _as_dict(state.get("source_kind_ratios"))
        if not kind_ratios:
            kind_counts = _as_dict(state.get("source_kind_counts"))
            denom = float(scene_count) if scene_count > 0 else 1.0
            kind_ratios = {key: float(_safe_int(value, 0)) / denom for key, value in kind_counts.items()}

        asset_ratio = _safe_float(kind_ratios.get("asset"), 0.0)
        runtime_minimal_ratio = _safe_float(kind_ratios.get("runtime_minimal"), 0.0)
        none_ratio = _safe_float(kind_ratios.get("none"), 0.0)

        min_scene_count = _safe_int(threshold.get("min_scene_count"), 1)
        min_asset_ratio = _safe_float(threshold.get("min_asset_ratio"), 0.0)
        max_runtime_minimal_ratio = _safe_float(threshold.get("max_runtime_minimal_ratio"), 1.0)
        max_none_ratio = _safe_float(threshold.get("max_none_ratio"), 1.0)

        role_error: list[str] = []
        if scene_count < min_scene_count:
            role_error.append(f"scene_count {scene_count} < {min_scene_count}")
        if asset_ratio < min_asset_ratio:
            role_error.append(f"asset_ratio {asset_ratio:.4f} < {min_asset_ratio:.4f}")
        if runtime_minimal_ratio > max_runtime_minimal_ratio:
            role_error.append(
                f"runtime_minimal_ratio {runtime_minimal_ratio:.4f} > {max_runtime_minimal_ratio:.4f}"
            )
        if none_ratio > max_none_ratio:
            role_error.append(f"none_ratio {none_ratio:.4f} > {max_none_ratio:.4f}")

        if role_error:
            errors.extend([f"{role}: {item}" for item in role_error])

        role_reports[role] = {
            "state_file": state_rel,
            "threshold": threshold,
            "scene_count": scene_count,
            "asset_ratio": asset_ratio,
            "runtime_minimal_ratio": runtime_minimal_ratio,
            "none_ratio": none_ratio,
            "errors": role_error,
        }

    report = {
        "ok": len(errors) == 0,
        "roles": roles,
        "role_reports": role_reports,
        "errors": errors,
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
        },
        "report": {
            "json": report_json_path.relative_to(ROOT).as_posix(),
            "md": report_md_path.relative_to(ROOT).as_posix(),
        },
    }

    lines = ["# Scene Base Contract Source Mix Role Matrix Report", ""]
    for role in roles:
        item = _as_dict(role_reports.get(role))
        lines.append(f"- {role}: scene_count=`{_safe_int(item.get('scene_count'), 0)}`")
        lines.append(f"  asset_ratio=`{_safe_float(item.get('asset_ratio'), 0.0):.4f}`")
        lines.append(
            f"  runtime_minimal_ratio=`{_safe_float(item.get('runtime_minimal_ratio'), 0.0):.4f}`"
        )
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_base_contract_source_mix_role_matrix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_base_contract_source_mix_role_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

