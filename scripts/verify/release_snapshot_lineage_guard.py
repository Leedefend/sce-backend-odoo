#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from system_init_minimal_surface_probe import fetch_system_init_payload

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "release_snapshot_lineage_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "release_snapshot_lineage_guard.md"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def assert_lineage(payload: dict, *, requested_edition: str, expected_effective_edition: str) -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    runtime = data.get("edition_runtime_v1") if isinstance(data.get("edition_runtime_v1"), dict) else {}
    diagnostics = runtime.get("diagnostics") if isinstance(runtime.get("diagnostics"), dict) else {}
    requested = runtime.get("requested") if isinstance(runtime.get("requested"), dict) else {}
    effective = runtime.get("effective") if isinstance(runtime.get("effective"), dict) else {}
    lineage = diagnostics.get("released_snapshot_lineage") if isinstance(diagnostics.get("released_snapshot_lineage"), dict) else {}
    if str(requested.get("edition_key") or "").strip() != requested_edition:
        raise RuntimeError(f"{requested_edition}: requested edition drift")
    if str(effective.get("edition_key") or "").strip() != expected_effective_edition:
        raise RuntimeError(f"{requested_edition}: effective edition drift")
    if not lineage:
        raise RuntimeError(f"{requested_edition}: released_snapshot_lineage missing")
    if str(lineage.get("state") or "").strip() != "released":
        raise RuntimeError(f"{requested_edition}: lineage state drift")
    if lineage.get("is_active") is not True:
        raise RuntimeError(f"{requested_edition}: lineage active flag drift")
    effective_runtime = lineage.get("effective_runtime") if isinstance(lineage.get("effective_runtime"), dict) else {}
    if str(effective_runtime.get("edition_key") or "").strip() != expected_effective_edition:
        raise RuntimeError(f"{requested_edition}: lineage effective runtime drift")
    return {
        "requested": requested,
        "effective": effective,
        "lineage": lineage,
    }


def main() -> int:
    report = {"status": "PASS", "standard": {}, "preview": {}}
    try:
        standard_payload = fetch_system_init_payload(extra_params={"edition_key": "standard"})
        preview_payload = fetch_system_init_payload(extra_params={"edition_key": "preview"})
        report["standard"] = assert_lineage(standard_payload, requested_edition="standard", expected_effective_edition="standard")
        report["preview"] = assert_lineage(preview_payload, requested_edition="preview", expected_effective_edition="preview")
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        write_json(OUT_JSON, report)
        write(
            OUT_MD,
            "# Release Snapshot Lineage Guard\n\n"
            "- status: `FAIL`\n"
            f"- error: `{str(exc)}`\n",
        )
        print("[release_snapshot_lineage_guard] FAIL")
        print(f" - {exc}")
        return 1

    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Snapshot Lineage Guard\n\n"
        "- status: `PASS`\n"
        f"- standard_lineage: `{report['standard']['lineage'].get('product_key', '')}@{report['standard']['lineage'].get('version', '')}`\n"
        f"- preview_lineage: `{report['preview']['lineage'].get('product_key', '')}@{report['preview']['lineage'].get('version', '')}`\n",
    )
    print("[release_snapshot_lineage_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
