#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_duplication_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_init_duplication_guard.md"


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

        duplicate_top_keys = [
            key
            for key in (
                "scenes",
                "capabilities",
                "capability_groups",
                "page_contracts",
                "workspace_home",
                "scene_ready_contract_v1",
                "ext_facts",
            )
            if key in data
        ]
        if duplicate_top_keys:
            errors.append(f"top-level duplicate payload keys present: {', '.join(duplicate_top_keys)}")

        if "payload_keys_before" in init_meta:
            errors.append("init_meta must not expose payload_keys_before")

        if isinstance(data.get("capability_groups"), list):
            for index, group in enumerate(data.get("capability_groups") or []):
                if not isinstance(group, dict):
                    continue
                if isinstance(group.get("capabilities"), list) and group.get("capabilities"):
                    errors.append(f"capability_groups[{index}] must not inline capabilities objects")

        report = {
            "status": "PASS" if not errors else "FAIL",
            "payload_bytes": result.get("payload_bytes"),
            "duplicate_top_keys": duplicate_top_keys,
            "init_meta_keys": sorted(init_meta.keys()),
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# System Init Duplication Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- payload_bytes: {report.get('payload_bytes', '-')}",
        f"- duplicate_top_keys: {', '.join(report.get('duplicate_top_keys') or []) or '(none)'}",
        f"- init_meta_keys: {', '.join(report.get('init_meta_keys') or []) or '(none)'}",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {item}" for item in errors]])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[system_init_duplication_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_duplication_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
