#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from system_init_minimal_surface_probe import fetch_system_init_payload

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "edition_runtime_routing_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "edition_runtime_routing_guard.md"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def runtime_contract(payload: dict) -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    runtime = data.get("edition_runtime_v1") if isinstance(data.get("edition_runtime_v1"), dict) else {}
    if not runtime:
        raise RuntimeError("system.init missing edition_runtime_v1")
    return runtime


def assert_runtime(runtime: dict, *, requested: str, effective: str, fallback_reason: str = "") -> dict:
    requested_row = runtime.get("requested") if isinstance(runtime.get("requested"), dict) else {}
    effective_row = runtime.get("effective") if isinstance(runtime.get("effective"), dict) else {}
    diagnostics = runtime.get("diagnostics") if isinstance(runtime.get("diagnostics"), dict) else {}
    actual_requested = str(requested_row.get("edition_key") or "").strip()
    actual_effective = str(effective_row.get("edition_key") or "").strip()
    if actual_requested != requested:
        raise RuntimeError(f"requested edition drift: expected={requested} actual={actual_requested}")
    if actual_effective != effective:
        raise RuntimeError(f"effective edition drift: expected={effective} actual={actual_effective}")
    actual_fallback_reason = str(diagnostics.get("fallback_reason") or "").strip()
    if actual_fallback_reason != fallback_reason:
        raise RuntimeError(
            f"fallback reason drift: expected={fallback_reason or '<empty>'} actual={actual_fallback_reason or '<empty>'}"
        )
    return {
        "requested": requested_row,
        "effective": effective_row,
        "diagnostics": diagnostics,
    }


def main() -> int:
    report = {"status": "PASS", "standard": {}, "preview": {}}
    try:
        standard_payload = fetch_system_init_payload(extra_params={"edition_key": "standard"})
        preview_payload = fetch_system_init_payload(extra_params={"edition_key": "preview"})
        report["standard"] = assert_runtime(runtime_contract(standard_payload), requested="standard", effective="standard")
        report["preview"] = assert_runtime(runtime_contract(preview_payload), requested="preview", effective="preview")
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        write_json(OUT_JSON, report)
        write(
            OUT_MD,
            "# Edition Runtime Routing Guard\n\n"
            "- status: `FAIL`\n"
            f"- error: `{str(exc)}`\n",
        )
        print("[edition_runtime_routing_guard] FAIL")
        print(f" - {exc}")
        return 1

    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Edition Runtime Routing Guard\n\n"
        "- status: `PASS`\n"
        f"- standard_effective: `{report['standard']['effective'].get('edition_key', '')}`\n"
        f"- preview_effective: `{report['preview']['effective'].get('edition_key', '')}`\n",
    )
    print("[edition_runtime_routing_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
