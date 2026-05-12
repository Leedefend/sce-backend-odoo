"""Project legacy A_SCBS labor wage facts into sc.labor.settlement.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


SOURCE_MODEL = "legacy.main.A_SCBS_RYGZD"
SOURCE_HEADER_TABLE = "A_SCBS_RYGZD"
SOURCE_LINE_TABLE = "A_SCBS_RYGZD_CB"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path.cwd() / "artifacts/migration", Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/tmp")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value) -> str:
    return str(value or "").strip()


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_date(value: str):
    return value[:10] if value else False


def raw_json(record) -> dict[str, object]:
    try:
        return json.loads(record.raw_payload or "{}")
    except json.JSONDecodeError:
        return {}


def project_by_legacy_id(cache: dict[str, int | bool], legacy_id: str, name: str):
    key = clean(legacy_id) or "__name__:" + clean(name)
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if clean(legacy_id):
        project = Project.search([("legacy_project_id", "=", clean(legacy_id))], limit=1)
    if not project and clean(name):
        project = Project.search([("name", "=", clean(name))], limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def contractor_by_name(cache: dict[str, int], name: str):
    key = clean(name)
    if key in cache:
        return cache[key]
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.search([("name", "=", key)], limit=1)
    if not partner:
        partner = Partner.create({"name": key, "supplier_rank": 1})
    elif partner.supplier_rank <= 0:
        partner.write({"supplier_rank": 1})
    cache[key] = partner.id
    return cache[key]


def line_values(line) -> dict[str, object]:
    payload = raw_json(line)
    qty = to_float(payload.get("SL"))
    amount = to_float(payload.get("JE"))
    unit_price = amount / qty if qty else 0.0
    work_content = clean(payload.get("ZYMC")) or clean(payload.get("BZ")) or "历史劳务"
    unit_name = clean(payload.get("DW")) or clean(payload.get("GGDW"))
    return {
        "work_content": work_content,
        "labor_team": clean(payload.get("GGDW")),
        "qty": qty,
        "unit_name": unit_name,
        "unit_price": unit_price,
        "tax_rate": 0.0,
        "note": "历史明细%s; 原单位=%s; 原单价=%s; 原金额=%s; 原备注=%s"
        % (
            line.legacy_record_id,
            unit_name,
            clean(payload.get("DJ")),
            clean(payload.get("JE")),
            clean(payload.get("BZ")),
        ),
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "legacy_a_scbs_labor_settlement_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_a_scbs_labor_settlement_projection_residual_v1.csv"
    result_json = artifacts / "legacy_a_scbs_labor_settlement_projection_result_v1.json"

    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.labor.settlement"].sudo().with_context(active_test=False)  # noqa: F821
    headers = Residual.search([("source_table", "=", SOURCE_HEADER_TABLE)], order="document_date, id")
    lines = Residual.search([("source_table", "=", SOURCE_LINE_TABLE)], order="legacy_parent_id, id")
    lines_by_header = defaultdict(list)
    for line in lines:
        lines_by_header[line.legacy_parent_id].append(line)

    existing = Settlement.search_read([("legacy_fact_model", "=", SOURCE_MODEL)], ["legacy_fact_id"])
    existing_ids = {row["legacy_fact_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    contractor_cache: dict[str, int] = {}
    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    planned_headers = 0
    planned_lines = 0
    planned_amount = 0.0
    created = 0
    skipped_existing = 0
    blocked_headers = 0

    for header in headers:
        payload = raw_json(header)
        header_id = clean(payload.get("Id")) or header.legacy_record_id.split("#", 1)[0]
        header_lines = [line for line in lines_by_header.get(header_id, []) if line.active]
        project_id = project_by_legacy_id(project_cache, header.project_legacy_id, header.project_name)
        contractor_name = clean(payload.get("LWBG"))
        line_amount = sum(to_float(raw_json(line).get("JE")) for line in header_lines)
        reason = ""
        if not header.active:
            reason = "inactive_legacy_header"
        elif not project_id:
            reason = "missing_project_anchor"
        elif not contractor_name:
            reason = "missing_labor_contractor"
        elif not header_lines:
            reason = "missing_legacy_lines"
        else:
            for line in header_lines:
                if to_float(raw_json(line).get("SL")) <= 0:
                    reason = "non_positive_qty"
                    break

        if header.id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
        elif reason:
            action = "blocked"
            blocked_headers += 1
            residual_rows.append(
                {
                    "legacy_header_id": header_id,
                    "document_no": header.document_no,
                    "project_legacy_id": header.project_legacy_id,
                    "project_name": header.project_name,
                    "contractor_name": contractor_name,
                    "line_rows": len(header_lines),
                    "line_amount": round(line_amount, 2),
                    "reason": reason,
                }
            )
        else:
            action = "create_labor_settlement"
            planned_headers += 1
            planned_lines += len(header_lines)
            planned_amount += line_amount
            if apply:
                settlement = Settlement.create(
                    {
                        "name": header.document_no or "A_SCBS工资单-%s" % header_id,
                        "project_id": project_id,
                        "contractor_id": contractor_by_name(contractor_cache, contractor_name),
                        "settlement_date": to_date(str(payload.get("DJRQ") or header.document_date or "")),
                        "state": "confirmed",
                        "legacy_fact_model": SOURCE_MODEL,
                        "legacy_fact_id": header.id,
                        "legacy_fact_type": "labor_wage_settlement",
                        "note": "\n".join(
                            [
                                "旧系统保盛人员工资单迁入。",
                                "source_table=%s/%s" % (SOURCE_HEADER_TABLE, SOURCE_LINE_TABLE),
                                "legacy_header_id=%s" % header_id,
                                "legacy_pid=%s" % (header.legacy_pid or ""),
                                "legacy_header_amount=%s" % (header.amount_total or 0),
                                "legacy_line_amount=%.2f" % line_amount,
                                "legacy_contractor=%s" % contractor_name,
                                "legacy_creator=%s(%s)" % (clean(payload.get("LRR")), clean(payload.get("LRRID"))),
                            ]
                        ),
                        "line_ids": [(0, 0, line_values(line)) for line in header_lines],
                    }
                )
                created += 1 if settlement else 0

        plan_rows.append(
            {
                "legacy_header_id": header_id,
                "legacy_fact_id": header.id,
                "document_no": header.document_no,
                "project_legacy_id": header.project_legacy_id,
                "project_name": header.project_name,
                "contractor_name": contractor_name,
                "line_rows": len(header_lines),
                "line_amount": round(line_amount, 2),
                "target_model": "sc.labor.settlement",
                "action": action,
                "reason": reason,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fieldnames = [
        "legacy_header_id",
        "legacy_fact_id",
        "document_no",
        "project_legacy_id",
        "project_name",
        "contractor_name",
        "line_rows",
        "line_amount",
        "target_model",
        "action",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)
    write_csv(residual_csv, residual_rows, [key for key in fieldnames if key not in {"legacy_fact_id", "target_model", "action"}])
    result = {
        "status": "PASS",
        "mode": "legacy_a_scbs_labor_settlement_projection",
        "apply": apply,
        "header_rows": len(headers),
        "line_rows": len(lines),
        "planned_headers": planned_headers,
        "planned_lines": planned_lines,
        "planned_amount": round(planned_amount, 2),
        "created": created,
        "skipped_existing": skipped_existing,
        "blocked_headers": blocked_headers,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_A_SCBS_LABOR_SETTLEMENT_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
