#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "runtime_surface_dashboard_report.json"
SCENE_CATALOG_JSON = ROOT / "docs" / "contract" / "exports" / "scene_catalog.json"
ALIGNMENT_JSON = ROOT / "artifacts" / "scene_catalog_runtime_alignment_guard.json"


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[runtime_surface_dashboard_report] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "runtime_surface_dashboard_report.json"
    artifact_md = artifacts_dir / "runtime_surface_dashboard_report.md"
    role_prod_like_json = artifacts_dir / "role_capability_floor_prod_like.json"
    if not role_prod_like_json.is_file():
        role_prod_like_json = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"

    scene_catalog = _load_json(SCENE_CATALOG_JSON)
    alignment = _load_json(ALIGNMENT_JSON)
    prod_like = _load_json(role_prod_like_json)

    catalog_count = int(scene_catalog.get("scene_count") or 0)
    runtime_scene_count = int(((alignment.get("summary") or {}).get("runtime_scene_count")) or 0)
    ratio = _safe_float((alignment.get("summary") or {}).get("catalog_runtime_ratio"), 0.0)
    if runtime_scene_count > 0 and ratio <= 0:
        ratio = round(catalog_count / runtime_scene_count, 6)
    runtime_capability_max = 0
    runtime_capability_min = 0
    runtime_capability_avg = 0.0
    role_rows = prod_like.get("roles") if isinstance(prod_like.get("roles"), list) else []
    if role_rows:
        caps = [int(row.get("capability_count") or 0) for row in role_rows if isinstance(row, dict)]
        if caps:
            runtime_capability_max = max(caps)
            runtime_capability_min = min(caps)
            runtime_capability_avg = round(sum(caps) / len(caps), 3)

    warnings: list[str] = []
    ratio_min_warn = _safe_float(baseline.get("ratio_min_warn"), 0.0)
    ratio_max_warn = _safe_float(baseline.get("ratio_max_warn"), 1.0)
    scene_delta_warn_abs = int(baseline.get("scene_delta_warn_abs") or 0)
    cap_min_warn = int(baseline.get("capability_min_warn") or 0)
    cap_max_warn = int(baseline.get("capability_max_warn") or 9999)
    scene_delta = runtime_scene_count - catalog_count

    if ratio < ratio_min_warn:
        warnings.append(f"catalog/runtime ratio below warning threshold: {ratio} < {ratio_min_warn}")
    if ratio > ratio_max_warn:
        warnings.append(f"catalog/runtime ratio above warning threshold: {ratio} > {ratio_max_warn}")
    if abs(scene_delta) > scene_delta_warn_abs:
        warnings.append(f"scene delta above warning threshold: |{scene_delta}| > {scene_delta_warn_abs}")
    if runtime_capability_max and runtime_capability_max < cap_min_warn:
        warnings.append(f"runtime capability max below warning threshold: {runtime_capability_max} < {cap_min_warn}")
    if runtime_capability_max > cap_max_warn:
        warnings.append(f"runtime capability max above warning threshold: {runtime_capability_max} > {cap_max_warn}")

    report = {
        "ok": True,
        "summary": {
            "catalog_scene_count": catalog_count,
            "runtime_scene_count": runtime_scene_count,
            "scene_delta": scene_delta,
            "catalog_runtime_ratio": ratio,
            "runtime_capability_min": runtime_capability_min,
            "runtime_capability_avg": runtime_capability_avg,
            "runtime_capability_max": runtime_capability_max,
            "warning_count": len(warnings),
            "artifacts_dir": str(artifacts_dir),
        },
        "baseline": baseline,
        "warnings": warnings,
    }
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Runtime Surface Dashboard Report",
        "",
        "- status: PASS (warning-only gate)",
        f"- catalog_scene_count: {catalog_count}",
        f"- runtime_scene_count: {runtime_scene_count}",
        f"- scene_delta: {scene_delta}",
        f"- catalog_runtime_ratio: {ratio}",
        f"- runtime_capability_min/avg/max: {runtime_capability_min}/{runtime_capability_avg}/{runtime_capability_max}",
        f"- warning_count: {len(warnings)}",
    ]
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for item in warnings[:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if warnings:
        print("[runtime_surface_dashboard_report] PASS_WITH_WARNINGS")
    else:
        print("[runtime_surface_dashboard_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
