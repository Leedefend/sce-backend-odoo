#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = ROOT / "docs" / "product" / "product_delivery_contract_v1.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_freshness_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_freshness_guard_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(v: object) -> str:
    return str(v or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    contract = _load(CONTRACT_JSON)
    if not contract:
        errors.append("missing product delivery contract")

    max_age_hours = int(os.getenv("PRODUCT_DELIVERY_MAX_AGE_HOURS") or 24)
    now = time.time()
    report_rows = contract.get("required_reports") if isinstance(contract.get("required_reports"), list) else []
    checked = []
    stale = []

    for row in report_rows:
        if not isinstance(row, dict):
            continue
        item_id = _norm(row.get("id"))
        rel_path = _norm(row.get("path"))
        p = ROOT / rel_path
        item = {"id": item_id, "path": rel_path, "exists": p.is_file(), "age_hours": None}
        if not p.is_file():
            stale.append({"id": item_id, "path": rel_path, "reason": "missing"})
            checked.append(item)
            continue
        age_hours = round((now - p.stat().st_mtime) / 3600.0, 2)
        item["age_hours"] = age_hours
        if age_hours > max_age_hours:
            stale.append({"id": item_id, "path": rel_path, "reason": f"stale>{max_age_hours}h", "age_hours": age_hours})
        checked.append(item)

    if stale:
        errors.append(f"stale_or_missing_artifact_count={len(stale)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "max_age_hours": max_age_hours,
            "checked_count": len(checked),
            "stale_or_missing_count": len(stale),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checked": checked,
        "stale_or_missing": stale,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Freshness Guard",
        "",
        f"- max_age_hours: {max_age_hours}",
        f"- checked_count: {len(checked)}",
        f"- stale_or_missing_count: {len(stale)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Stale Or Missing",
        "",
    ]
    if stale:
        for row in stale:
            lines.append(f"- {row['id']}: {row['reason']} ({row['path']})")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_delivery_freshness_guard] FAIL")
        return 2
    print("[product_delivery_freshness_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
