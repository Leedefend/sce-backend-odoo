#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_base_contract_source_mix_guard.json"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


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


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[scene_base_contract_source_mix_guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    state_path = ROOT / _text(baseline.get("state_file") or "artifacts/backend/scene_registry_asset_snapshot_state.json")
    report_json_path = ROOT / _text(baseline.get("report_json") or "artifacts/backend/scene_base_contract_source_mix_report.json")
    report_md_path = ROOT / _text(baseline.get("report_md") or "artifacts/backend/scene_base_contract_source_mix_report.md")
    state = _load_json(state_path)

    scene_count = _safe_int(state.get("scene_count"), 0)
    kind_counts = _as_dict(state.get("source_kind_counts"))
    kind_ratios = _as_dict(state.get("source_kind_ratios"))

    if not kind_counts:
        per_scene = _as_dict(state.get("per_scene"))
        derived_counts = {
            "asset": 0,
            "runtime_fallback": 0,
            "runtime_minimal": 0,
            "inline": 0,
            "none": 0,
            "other": 0,
        }
        for row in per_scene.values():
            payload = _as_dict(row)
            kind = _text(payload.get("source_kind")) or "none"
            if kind not in derived_counts:
                kind = "other"
            derived_counts[kind] = _safe_int(derived_counts.get(kind), 0) + 1
        kind_counts = derived_counts

    if not kind_ratios:
        denom = float(scene_count) if scene_count > 0 else 1.0
        kind_ratios = {key: float(_safe_int(value, 0)) / denom for key, value in kind_counts.items()}

    asset_ratio = _safe_float(kind_ratios.get("asset"), 0.0)
    runtime_fallback_ratio = _safe_float(kind_ratios.get("runtime_fallback"), 0.0)
    runtime_minimal_ratio = _safe_float(kind_ratios.get("runtime_minimal"), 0.0)
    none_ratio = _safe_float(kind_ratios.get("none"), 0.0)

    min_scene_count = _safe_int(baseline.get("min_scene_count"), 1)
    min_asset_ratio = _safe_float(baseline.get("min_asset_ratio"), 0.0)
    max_runtime_fallback_ratio = _safe_float(baseline.get("max_runtime_fallback_ratio"), 1.0)
    max_runtime_minimal_ratio = _safe_float(baseline.get("max_runtime_minimal_ratio"), 1.0)
    max_none_ratio = _safe_float(baseline.get("max_none_ratio"), 1.0)

    errors: list[str] = []
    if scene_count < min_scene_count:
        errors.append(f"scene_count below threshold: {scene_count} < {min_scene_count}")
    if asset_ratio < min_asset_ratio:
        errors.append(f"asset_ratio below threshold: {asset_ratio:.4f} < {min_asset_ratio:.4f}")
    if runtime_fallback_ratio > max_runtime_fallback_ratio:
        errors.append(
            "runtime_fallback_ratio above threshold: "
            f"{runtime_fallback_ratio:.4f} > {max_runtime_fallback_ratio:.4f}"
        )
    if runtime_minimal_ratio > max_runtime_minimal_ratio:
        errors.append(
            "runtime_minimal_ratio above threshold: "
            f"{runtime_minimal_ratio:.4f} > {max_runtime_minimal_ratio:.4f}"
        )
    if none_ratio > max_none_ratio:
        errors.append(f"none_ratio above threshold: {none_ratio:.4f} > {max_none_ratio:.4f}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "scene_count": scene_count,
            "source_kind_counts": kind_counts,
            "source_kind_ratios": kind_ratios,
            "asset_ratio": asset_ratio,
            "runtime_fallback_ratio": runtime_fallback_ratio,
            "runtime_minimal_ratio": runtime_minimal_ratio,
            "none_ratio": none_ratio,
        },
        "thresholds": {
            "min_scene_count": min_scene_count,
            "min_asset_ratio": min_asset_ratio,
            "max_runtime_fallback_ratio": max_runtime_fallback_ratio,
            "max_runtime_minimal_ratio": max_runtime_minimal_ratio,
            "max_none_ratio": max_none_ratio,
        },
        "sources": {
            "baseline": BASELINE_PATH.relative_to(ROOT).as_posix(),
            "state": state_path.relative_to(ROOT).as_posix(),
        },
        "errors": errors,
        "report": {
            "json": report_json_path.relative_to(ROOT).as_posix(),
            "md": report_md_path.relative_to(ROOT).as_posix(),
        },
    }

    lines = [
        "# Scene Base Contract Source Mix Report",
        "",
        f"- scene_count: `{scene_count}`",
        f"- asset_ratio: `{asset_ratio:.4f}`",
        f"- runtime_fallback_ratio: `{runtime_fallback_ratio:.4f}`",
        f"- runtime_minimal_ratio: `{runtime_minimal_ratio:.4f}`",
        f"- none_ratio: `{none_ratio:.4f}`",
    ]
    if errors:
        lines.extend(["", "## Errors"] + [f"- {item}" for item in errors])

    _write(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))
    _write(report_md_path, "\n".join(lines) + "\n")

    if errors:
        print("[scene_base_contract_source_mix_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        print(report_json_path)
        print(report_md_path)
        return 1

    print(report_json_path)
    print(report_md_path)
    print("[scene_base_contract_source_mix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

