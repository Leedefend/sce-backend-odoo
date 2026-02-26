#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = ROOT / "docs" / "product" / "product_delivery_contract_v1.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_gap_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_gap_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _norm(value: object) -> str:
    return str(value or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    gaps: list[dict] = []

    contract = _load(CONTRACT_JSON)
    if not contract:
        errors.append("missing product delivery contract")

    report_rows = contract.get("required_reports") if isinstance(contract.get("required_reports"), list) else []
    doc_rows = contract.get("required_docs") if isinstance(contract.get("required_docs"), list) else []
    if not report_rows:
        errors.append("required_reports empty")
    if not doc_rows:
        warnings.append("required_docs empty")

    checked_reports = []
    for row in report_rows:
        if not isinstance(row, dict):
            continue
        item_id = _norm(row.get("id"))
        rel_path = _norm(row.get("path"))
        require_ok = bool(row.get("require_ok", True))
        p = ROOT / rel_path
        item = {
            "id": item_id,
            "path": rel_path,
            "exists": p.is_file(),
            "require_ok": require_ok,
            "ok": None,
            "error_count": None,
            "warning_count": None,
        }
        if not p.is_file():
            gaps.append({"type": "missing_report", "id": item_id, "path": rel_path})
            checked_reports.append(item)
            continue
        payload = _load(p)
        if not payload:
            gaps.append({"type": "invalid_report_payload", "id": item_id, "path": rel_path})
            checked_reports.append(item)
            continue
        ok = bool(payload.get("ok"))
        item["ok"] = ok
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        item["error_count"] = int(summary.get("error_count") or 0)
        item["warning_count"] = int(summary.get("warning_count") or 0)
        if require_ok and not ok:
            gaps.append({"type": "report_not_ok", "id": item_id, "path": rel_path})
        checked_reports.append(item)

    checked_docs = []
    for row in doc_rows:
        if not isinstance(row, dict):
            continue
        item_id = _norm(row.get("id"))
        rel_path = _norm(row.get("path"))
        p = ROOT / rel_path
        exists = p.is_file()
        checked_docs.append({"id": item_id, "path": rel_path, "exists": exists})
        if not exists:
            gaps.append({"type": "missing_doc", "id": item_id, "path": rel_path})

    if gaps:
        errors.append(f"delivery_gap_count={len(gaps)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "contract_version": _norm(contract.get("version") or "unknown"),
            "required_report_count": len(report_rows),
            "required_doc_count": len(doc_rows),
            "gap_count": len(gaps),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checked_reports": checked_reports,
        "checked_docs": checked_docs,
        "gaps": gaps,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Gap Report",
        "",
        f"- contract_version: {payload['summary']['contract_version']}",
        f"- required_report_count: {payload['summary']['required_report_count']}",
        f"- required_doc_count: {payload['summary']['required_doc_count']}",
        f"- gap_count: {payload['summary']['gap_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "## Gap List",
        "",
    ]
    if gaps:
        for gap in gaps:
            lines.append(f"- {gap['type']}: {gap['id']} ({gap['path']})")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_delivery_gap_report] FAIL")
        return 2
    print("[product_delivery_gap_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
