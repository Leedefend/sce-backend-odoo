#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACL_CSV = ROOT / "addons" / "smart_construction_core" / "security" / "ir.model.access.csv"
OUT_JSON = ROOT / "artifacts" / "backend" / "role_acl_minimum_set_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "role_acl_minimum_set_guard.md"

REQUIRED_MODELS = {
    "project.project": ["model_project_project"],
    "construction.contract": ["model_construction_contract"],
    "project.cost": ["model_project_cost_ledger", "model_project_cost_period", "model_project_budget"],
    "payment.request": ["model_payment_request"],
}


def _to_bool(raw: str) -> bool:
    return str(raw or "").strip() in {"1", "true", "True"}


def main() -> int:
    errors: list[str] = []
    summary: dict[str, dict] = {}
    if not ACL_CSV.is_file():
        errors.append(f"missing ACL file: {ACL_CSV.as_posix()}")
        report = {"ok": False, "summary": summary, "errors": errors}
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUT_MD.write_text("# Role ACL Minimum Set Guard\n\n- status: FAIL\n", encoding="utf-8")
        print(str(OUT_JSON))
        print(str(OUT_MD))
        print("[role_acl_minimum_set_guard] FAIL")
        return 1

    with ACL_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    for business_model, model_refs in REQUIRED_MODELS.items():
        model_rows = [row for row in rows if str(row.get("model_id:id") or "").strip() in set(model_refs)]
        group_ids = sorted({str(row.get("group_id:id") or "").strip() for row in model_rows if str(row.get("group_id:id") or "").strip()})
        read_rows = [row for row in model_rows if _to_bool(str(row.get("perm_read") or "0"))]
        write_rows = [row for row in model_rows if _to_bool(str(row.get("perm_write") or "0"))]
        create_rows = [row for row in model_rows if _to_bool(str(row.get("perm_create") or "0"))]
        unlink_rows = [row for row in model_rows if _to_bool(str(row.get("perm_unlink") or "0"))]

        write_without_read = []
        for row in model_rows:
            can_read = _to_bool(str(row.get("perm_read") or "0"))
            can_write = _to_bool(str(row.get("perm_write") or "0"))
            can_create = _to_bool(str(row.get("perm_create") or "0"))
            can_unlink = _to_bool(str(row.get("perm_unlink") or "0"))
            if (can_write or can_create or can_unlink) and not can_read:
                write_without_read.append(str(row.get("id") or "<unknown>"))

        summary[business_model] = {
            "model_refs": model_refs,
            "acl_row_count": len(model_rows),
            "group_count": len(group_ids),
            "groups": group_ids,
            "read_row_count": len(read_rows),
            "write_row_count": len(write_rows),
            "create_row_count": len(create_rows),
            "unlink_row_count": len(unlink_rows),
            "write_without_read_row_ids": write_without_read,
        }

        if len(model_rows) == 0:
            errors.append(f"{business_model}: no ACL rows found for {model_refs}")
        if len(read_rows) == 0:
            errors.append(f"{business_model}: no readable ACL rows")
        if write_without_read:
            errors.append(f"{business_model}: write/create/unlink without read in rows {write_without_read}")

    report = {
        "ok": len(errors) == 0,
        "summary": summary,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Role ACL Minimum Set Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- model_count: {len(summary)}",
        f"- error_count: {len(errors)}",
        "",
        "## Models",
        "",
    ]
    for model, detail in summary.items():
        lines.append(
            f"- {model}: rows={detail['acl_row_count']} read={detail['read_row_count']} "
            f"write={detail['write_row_count']} create={detail['create_row_count']} "
            f"unlink={detail['unlink_row_count']} groups={detail['group_count']}"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if errors:
        print("[role_acl_minimum_set_guard] FAIL")
        return 1
    print("[role_acl_minimum_set_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

