#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_scene_subset_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_init_scene_subset_guard.md"


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {}
    try:
        result = fetch_system_init_payload()
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        init_meta = data.get("init_meta") if isinstance(data.get("init_meta"), dict) else {}
        default_route = data.get("default_route") if isinstance(data.get("default_route"), dict) else {}

        scene_subset = init_meta.get("scene_subset") if isinstance(init_meta.get("scene_subset"), list) else []
        scene_subset = [str(item).strip() for item in scene_subset if str(item).strip()]
        unique_subset = list(dict.fromkeys(scene_subset))
        scene_subset_count = int(init_meta.get("scene_subset_count") or 0)

        if not scene_subset:
            errors.append("init_meta.scene_subset missing or empty")
        if "workspace.home" not in unique_subset:
            errors.append("init_meta.scene_subset must include workspace.home")

        landing_scene = str(default_route.get("scene_key") or "").strip()
        if landing_scene and landing_scene not in unique_subset:
            errors.append(f"landing scene_key missing from scene_subset: {landing_scene}")

        if scene_subset_count != len(unique_subset):
            errors.append(
                f"scene_subset_count mismatch: expected {len(unique_subset)}, got {scene_subset_count}"
            )

        for forbidden in ("scenes", "scene_catalog", "scene_details"):
            if forbidden in data:
                errors.append(f"data must not include full scene payload key: {forbidden}")

        report = {
            "status": "PASS" if not errors else "FAIL",
            "payload_bytes": result.get("payload_bytes"),
            "scene_subset": unique_subset,
            "scene_subset_count": scene_subset_count,
            "landing_scene": landing_scene,
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# System Init Scene Subset Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- payload_bytes: {report.get('payload_bytes', '-')}",
        f"- scene_subset_count: {report.get('scene_subset_count', 0)}",
        f"- landing_scene: {report.get('landing_scene', '') or '(none)'}",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {item}" for item in errors]])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[system_init_scene_subset_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_scene_subset_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

