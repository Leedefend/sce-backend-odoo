"""Carry legacy T_ZL_MachineShift headers and project lines into equipment settlements.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


SOURCE_MODEL = "legacy.main.T_ZL_MachineShift"
SOURCE_HEADER_TABLE = "T_ZL_MachineShift"
SOURCE_LINE_TABLE = "T_ZL_MachineShift_CB"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path.cwd() / "artifacts/migration", Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/tmp")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError({"missing_legacy_t_zl_machine_shift_header_csv": str(path)})
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def to_datetime(value: str):
    if not value:
        return False
    return value[:19].replace("T", " ")


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


def supplier_by_name(cache: dict[str, int | bool], name: str):
    key = clean(name)
    if not key:
        return False
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


def existing_header_fact_ids() -> dict[str, int]:
    Fact = env["sc.legacy.equipment.lease.fact"].sudo().with_context(active_test=False)  # noqa: F821
    rows = Fact.search_read([("source_table", "=", SOURCE_HEADER_TABLE)], ["legacy_record_id"])
    return {row["legacy_record_id"]: row["id"] for row in rows}


def header_fact_values(header: dict[str, str], project_id: int | bool) -> dict[str, object]:
    return {
        "legacy_record_id": clean(header.get("legacy_header_id")),
        "legacy_parent_id": "",
        "legacy_pid": clean(header.get("legacy_pid")),
        "source_table": SOURCE_HEADER_TABLE,
        "source_dataset": "LegacyDb.dbo.T_ZL_MachineShift",
        "fact_type": "equipment_shift",
        "document_no": clean(header.get("document_no")),
        "document_state": clean(header.get("document_state")),
        "state": "legacy_confirmed" if header.get("active") == "1" else "cancel",
        "project_legacy_id": clean(header.get("project_legacy_id")),
        "project_name": clean(header.get("project_name")),
        "project_id": project_id or False,
        "partner_legacy_id": clean(header.get("supplier_legacy_id")),
        "partner_name": clean(header.get("supplier_name")),
        "equipment_name": clean(header.get("title")),
        "work_part": clean(header.get("work_part")),
        "document_date": to_datetime(clean(header.get("document_date"))),
        "created_time": to_datetime(clean(header.get("created_at"))),
        "creator_name": clean(header.get("creator_name")),
        "creator_legacy_user_id": clean(header.get("creator_legacy_user_id")),
        "amount_total": to_float(header.get("amount_total")),
        "note": clean(header.get("raw_payload")),
        "active": header.get("active") == "1",
    }


def line_values(line) -> dict[str, object]:
    payload = raw_json(line)
    qty = to_float(payload.get("GZSJ"))
    amount = to_float(payload.get("JE"))
    unit_price = amount / qty if qty else 0.0
    equipment_name = clean(payload.get("JXMC")) or clean(payload.get("GZNR")) or "历史机械台班"
    unit_name = clean(payload.get("DW")) or "台时"
    return {
        "equipment_name": equipment_name,
        "equipment_code": clean(payload.get("JXID")),
        "qty": qty,
        "unit_name": unit_name,
        "unit_price": unit_price,
        "tax_rate": 0.0,
        "note": "历史明细%s; 规格=%s; 工作内容=%s; 原单位=%s; 原单价=%s; 原金额=%s; 时间=%s-%s; 备注=%s"
        % (
            line.legacy_record_id,
            clean(payload.get("GGXH")),
            clean(payload.get("GZNR")),
            unit_name,
            clean(payload.get("DJ")),
            clean(payload.get("JE")),
            clean(payload.get("KSSJ")),
            clean(payload.get("JSSJ")),
            clean(payload.get("BZ")),
        ),
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    header_csv = Path(os.getenv("LEGACY_T_ZL_MACHINE_SHIFT_HEADER_CSV") or artifacts / "legacy_t_zl_machine_shift_headers_v1.csv")
    plan_csv = artifacts / "legacy_t_zl_machine_shift_settlement_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_t_zl_machine_shift_settlement_projection_residual_v1.csv"
    result_json = artifacts / "legacy_t_zl_machine_shift_settlement_projection_result_v1.json"

    headers = read_csv(header_csv)
    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Fact = env["sc.legacy.equipment.lease.fact"].sudo().with_context(active_test=False)  # noqa: F821
    Settlement = env["sc.equipment.settlement"].sudo().with_context(active_test=False)  # noqa: F821

    lines = Residual.search([("source_table", "=", SOURCE_LINE_TABLE)], order="legacy_parent_id, id")
    lines_by_header = defaultdict(list)
    for line in lines:
        lines_by_header[line.legacy_parent_id].append(line)

    header_fact_ids = existing_header_fact_ids()
    existing = Settlement.search_read([("legacy_fact_model", "=", SOURCE_MODEL)], ["legacy_fact_id"])
    existing_ids = {row["legacy_fact_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    supplier_cache: dict[str, int | bool] = {}
    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []

    planned_headers = 0
    planned_lines = 0
    planned_amount = 0.0
    carried_headers = 0
    created = 0
    skipped_existing = 0
    blocked_headers = 0

    for header in headers:
        header_id = clean(header.get("legacy_header_id"))
        header_lines = [line for line in lines_by_header.get(header_id, []) if line.active]
        project_id = project_by_legacy_id(project_cache, header.get("project_legacy_id") or "", header.get("project_name") or "")
        fact_id = header_fact_ids.get(header_id)

        if apply and not fact_id and header_id:
            fact = Fact.create(header_fact_values(header, project_id))
            fact_id = fact.id
            header_fact_ids[header_id] = fact_id
            carried_headers += 1

        supplier_name = clean(header.get("supplier_name"))
        settlement_date = to_date(clean(header.get("document_date")))
        if not settlement_date and header_lines:
            settlement_date = to_date(str(header_lines[0].document_date))
        line_amount = sum(to_float(raw_json(line).get("JE")) for line in header_lines)
        reason = ""
        if header.get("active") != "1":
            reason = "inactive_legacy_header"
        elif not header_id:
            reason = "missing_legacy_header_id"
        elif not project_id:
            reason = "missing_project_anchor"
        elif not supplier_name:
            reason = "missing_supplier_name"
        elif not header_lines:
            reason = "missing_legacy_lines"
        elif not settlement_date:
            reason = "missing_settlement_date"
        else:
            for line in header_lines:
                payload = raw_json(line)
                if not clean(payload.get("JXMC")) and not clean(payload.get("GZNR")):
                    reason = "missing_equipment_name"
                    break
                if to_float(payload.get("GZSJ")) <= 0:
                    reason = "non_positive_qty"
                    break

        if fact_id and fact_id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
        elif reason:
            action = "blocked"
            blocked_headers += 1
            residual_rows.append(
                {
                    "legacy_header_id": header_id,
                    "document_no": header.get("document_no") or "",
                    "project_legacy_id": header.get("project_legacy_id") or "",
                    "project_name": header.get("project_name") or "",
                    "supplier_name": supplier_name,
                    "line_rows": len(header_lines),
                    "line_amount": round(line_amount, 2),
                    "reason": reason,
                }
            )
        else:
            action = "create_equipment_settlement"
            planned_headers += 1
            planned_lines += len(header_lines)
            planned_amount += line_amount
            if apply:
                settlement = Settlement.create(
                    {
                        "name": clean(header.get("document_no")) or "机械台班-%s" % header_id,
                        "project_id": project_id,
                        "supplier_id": supplier_by_name(supplier_cache, supplier_name),
                        "settlement_date": settlement_date,
                        "state": "confirmed",
                        "legacy_fact_model": SOURCE_MODEL,
                        "legacy_fact_id": fact_id,
                        "legacy_fact_type": "equipment_shift_settlement",
                        "note": "\n".join(
                            [
                                "旧系统机械台班迁入设备结算。",
                                "source_table=%s/%s" % (SOURCE_HEADER_TABLE, SOURCE_LINE_TABLE),
                                "legacy_header_id=%s" % header_id,
                                "legacy_pid=%s" % clean(header.get("legacy_pid")),
                                "legacy_header_amount=%s" % clean(header.get("amount_total")),
                                "legacy_line_amount=%.2f" % line_amount,
                                "legacy_supplier=%s" % supplier_name,
                                "legacy_use_org=%s" % clean(header.get("use_org_name")),
                                "legacy_work_part=%s" % clean(header.get("work_part")),
                                "legacy_title=%s" % clean(header.get("title")),
                                "legacy_creator=%s(%s)" % (clean(header.get("creator_name")), clean(header.get("creator_legacy_user_id"))),
                            ]
                        ),
                        "line_ids": [(0, 0, line_values(line)) for line in header_lines],
                    }
                )
                created += 1 if settlement else 0

        plan_rows.append(
            {
                "legacy_header_id": header_id,
                "legacy_fact_id": fact_id or "",
                "document_no": header.get("document_no") or "",
                "project_legacy_id": header.get("project_legacy_id") or "",
                "project_name": header.get("project_name") or "",
                "supplier_name": supplier_name,
                "line_rows": len(header_lines),
                "line_amount": round(line_amount, 2),
                "target_model": "sc.equipment.settlement",
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
        "supplier_name",
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
        "mode": "legacy_t_zl_machine_shift_settlement_projection",
        "apply": apply,
        "header_rows": len(headers),
        "line_rows": len(lines),
        "planned_headers": planned_headers,
        "planned_lines": planned_lines,
        "planned_amount": round(planned_amount, 2),
        "carried_headers": carried_headers,
        "created": created,
        "skipped_existing": skipped_existing,
        "blocked_headers": blocked_headers,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_T_ZL_MACHINE_SHIFT_SETTLEMENT_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
