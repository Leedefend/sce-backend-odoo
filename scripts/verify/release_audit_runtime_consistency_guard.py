#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from system_init_minimal_surface_probe import fetch_system_init_payload

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "release_audit_runtime_consistency_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "release_audit_runtime_consistency_guard.md"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def assert_runtime(payload: dict, *, requested_edition: str, expected_effective: str) -> dict:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    runtime = data.get("edition_runtime_v1") if isinstance(data.get("edition_runtime_v1"), dict) else {}
    requested = runtime.get("requested") if isinstance(runtime.get("requested"), dict) else {}
    effective = runtime.get("effective") if isinstance(runtime.get("effective"), dict) else {}
    diagnostics = runtime.get("diagnostics") if isinstance(runtime.get("diagnostics"), dict) else {}
    lineage = diagnostics.get("released_snapshot_lineage") if isinstance(diagnostics.get("released_snapshot_lineage"), dict) else {}
    summary = diagnostics.get("release_audit_trail_summary") if isinstance(diagnostics.get("release_audit_trail_summary"), dict) else {}
    if str(requested.get("edition_key") or "").strip() != requested_edition:
        raise RuntimeError(f"{requested_edition}: requested edition drift")
    if str(effective.get("edition_key") or "").strip() != expected_effective:
        raise RuntimeError(f"{requested_edition}: effective edition drift")
    if not lineage:
        raise RuntimeError(f"{requested_edition}: released snapshot lineage missing")
    if not summary:
        raise RuntimeError(f"{requested_edition}: release audit trail summary missing")
    if str(summary.get("contract_version") or "").strip() != "release_audit_trail_surface_v1":
        raise RuntimeError(f"{requested_edition}: audit summary contract drift")
    if int(summary.get("active_snapshot_id") or 0) != int(lineage.get("snapshot_id") or 0):
        raise RuntimeError(f"{requested_edition}: audit summary snapshot drift")
    if str(summary.get("active_snapshot_version") or "").strip() != str(lineage.get("version") or "").strip():
        raise RuntimeError(f"{requested_edition}: audit summary version drift")
    if str(summary.get("edition_key") or "").strip() != expected_effective:
        raise RuntimeError(f"{requested_edition}: audit summary edition drift")
    if summary.get("audit_exportable") is not True:
        raise RuntimeError(f"{requested_edition}: audit exportable drift")
    if summary.get("active_released_uniqueness_ok") is not True:
        raise RuntimeError(f"{requested_edition}: active released uniqueness drift")
    return {
        "requested": requested,
        "effective": effective,
        "lineage": lineage,
        "summary": summary,
    }


def main() -> int:
    report = {"status": "PASS", "standard": {}, "preview": {}}
    try:
        report["standard"] = assert_runtime(
            fetch_system_init_payload(extra_params={"edition_key": "standard"}),
            requested_edition="standard",
            expected_effective="standard",
        )
        report["preview"] = assert_runtime(
            fetch_system_init_payload(extra_params={"edition_key": "preview"}),
            requested_edition="preview",
            expected_effective="preview",
        )
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        write_json(OUT_JSON, report)
        write(
            OUT_MD,
            "# Release Audit Runtime Consistency Guard\n\n"
            "- status: `FAIL`\n"
            f"- error: `{str(exc)}`\n",
        )
        print("[release_audit_runtime_consistency_guard] FAIL")
        print(f" - {exc}")
        return 1

    write_json(OUT_JSON, report)
    write(
        OUT_MD,
        "# Release Audit Runtime Consistency Guard\n\n"
        "- status: `PASS`\n"
        f"- standard: `{report['standard']['summary'].get('active_snapshot_id')}@{report['standard']['summary'].get('active_snapshot_version')}`\n"
        f"- preview: `{report['preview']['summary'].get('active_snapshot_id')}@{report['preview']['summary'].get('active_snapshot_version')}`\n",
    )
    print("[release_audit_runtime_consistency_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
