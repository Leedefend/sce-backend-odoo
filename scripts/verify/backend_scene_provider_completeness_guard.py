#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_CSV = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated" / "provider_completeness_current_v1.csv"
OUT_JSON = ROOT / "artifacts" / "backend" / "backend_scene_provider_completeness_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "backend_scene_provider_completeness_guard.md"


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _load_rows() -> list[dict[str, str]]:
    with SOURCE_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    try:
        rows = _load_rows()
        errors: list[str] = []
        incomplete: list[str] = []
        for row in rows:
            scene_key = str(row.get("scene_key") or "").strip()
            provider_registered = str(row.get("provider_registered") or "").strip().lower() == "true"
            fallback_present = str(row.get("explicit_fallback_present") or "").strip().lower() == "true"
            if not scene_key:
                continue
            if not provider_registered and not fallback_present:
                incomplete.append(scene_key)
                errors.append(f"{scene_key}: missing provider and explicit fallback")

        report = {
            "status": "PASS" if not errors else "FAIL",
            "source_csv": SOURCE_CSV.relative_to(ROOT).as_posix(),
            "checked_scene_count": len(rows),
            "incomplete_scene_count": len(incomplete),
            "incomplete_scenes": incomplete,
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Backend Scene Provider Completeness Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- source_csv: {report.get('source_csv', '') or '(unknown)'}",
        f"- checked_scene_count: {report.get('checked_scene_count', 0)}",
        f"- incomplete_scene_count: {report.get('incomplete_scene_count', 0)}",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[backend_scene_provider_completeness_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[backend_scene_provider_completeness_guard] PASS")
    print("incomplete_scene_count=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
