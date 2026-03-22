#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_no_page_contract_payload_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_init_no_page_contract_payload_guard.md"


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

        forbidden_keys = [
            key
            for key in (
                "page_contracts",
                "workspace_home",
                "scene_ready_contract_v1",
                "workspace_home_ref",
            )
            if key in data
        ]
        if forbidden_keys:
            errors.append(f"system.init must not include page contract payload keys: {', '.join(forbidden_keys)}")

        page_contract_meta = init_meta.get("page_contract_meta") if isinstance(init_meta.get("page_contract_meta"), dict) else {}
        if not page_contract_meta:
            errors.append("init_meta.page_contract_meta missing")
        else:
            intent = str(page_contract_meta.get("intent") or "").strip()
            if intent not in {"scene.page_contract", "page.contract"}:
                errors.append("init_meta.page_contract_meta.intent must be scene.page_contract or page.contract")

        preload_hint = init_meta.get("workspace_home_preload_hint") if isinstance(init_meta.get("workspace_home_preload_hint"), dict) else {}
        if not preload_hint:
            errors.append("init_meta.workspace_home_preload_hint missing")

        report = {
            "status": "PASS" if not errors else "FAIL",
            "payload_bytes": result.get("payload_bytes"),
            "forbidden_keys": forbidden_keys,
            "page_contract_meta": page_contract_meta,
            "workspace_home_preload_hint": preload_hint,
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# System Init No Page Contract Payload Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- payload_bytes: {report.get('payload_bytes', '-')}",
        f"- forbidden_keys: {', '.join(report.get('forbidden_keys') or []) or '(none)'}",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {item}" for item in errors]])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[system_init_no_page_contract_payload_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_no_page_contract_payload_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

