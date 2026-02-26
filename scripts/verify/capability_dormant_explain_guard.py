#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAP_USAGE_JSON = ROOT / "artifacts" / "backend" / "capability_usage_matrix.json"
EXPLAIN_JSON = ROOT / "docs" / "product" / "capability_dormant_explanations_v1.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "capability_dormant_explain_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "capability_dormant_explain_guard_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_key(value: object) -> str:
    return str(value or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    cap_usage = _load(CAP_USAGE_JSON)
    explain = _load(EXPLAIN_JSON)

    isolated = {
        _normalize_key(item)
        for item in (cap_usage.get("isolated_capabilities") if isinstance(cap_usage.get("isolated_capabilities"), list) else [])
        if _normalize_key(item)
    }
    structural_only = {
        _normalize_key(item)
        for item in (
            cap_usage.get("structural_only_capabilities")
            if isinstance(cap_usage.get("structural_only_capabilities"), list)
            else []
        )
        if _normalize_key(item)
    }
    dormant_all = sorted(isolated | structural_only)

    entries = explain.get("entries") if isinstance(explain.get("entries"), list) else []
    explain_map: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = _normalize_key(entry.get("capability_key"))
        if key:
            explain_map[key] = entry

    missing_explanations = [key for key in dormant_all if key not in explain_map]
    stale_explanations = [key for key in explain_map if key not in dormant_all]

    if missing_explanations:
        errors.append(f"missing_dormant_explanation_count={len(missing_explanations)}")
    if stale_explanations:
        warnings.append(f"stale_explanation_count={len(stale_explanations)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "dormant_capability_count": len(dormant_all),
            "isolated_count": len(isolated),
            "structural_only_count": len(structural_only),
            "explanation_entry_count": len(explain_map),
            "missing_explanation_count": len(missing_explanations),
            "stale_explanation_count": len(stale_explanations),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "acceptance": {
            "all_dormant_explained": len(missing_explanations) == 0,
        },
        "dormant_capabilities": dormant_all,
        "missing_explanations": missing_explanations,
        "stale_explanations": stale_explanations,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Capability Dormant Explain Guard",
        "",
        f"- dormant_capability_count: {len(dormant_all)}",
        f"- isolated_count: {len(isolated)}",
        f"- structural_only_count: {len(structural_only)}",
        f"- explanation_entry_count: {len(explain_map)}",
        f"- missing_explanation_count: {len(missing_explanations)}",
        f"- stale_explanation_count: {len(stale_explanations)}",
        "",
        "## Acceptance",
        "",
        f"- all_dormant_explained: {'PASS' if len(missing_explanations) == 0 else 'FAIL'}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[capability_dormant_explain_guard] FAIL")
        return 2
    print("[capability_dormant_explain_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
