"""Project legacy A_SCBS equipment usage facts into sc.equipment.usage.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


SOURCE_MODEL = "legacy.main.A_SCBS_JXD_CB"
SOURCE_HEADER_TABLE = "A_SCBS_JXD"
SOURCE_LINE_TABLE = "A_SCBS_JXD_CB"


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


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "legacy_a_scbs_equipment_usage_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_a_scbs_equipment_usage_projection_residual_v1.csv"
    result_json = artifacts / "legacy_a_scbs_equipment_usage_projection_result_v1.json"

    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Usage = env["sc.equipment.usage"].sudo().with_context(active_test=False)  # noqa: F821
    headers = Residual.search([("source_table", "=", SOURCE_HEADER_TABLE)], order="document_date, id")
    lines = Residual.search([("source_table", "=", SOURCE_LINE_TABLE)], order="legacy_parent_id, id")
    headers_by_id = {}
    for header in headers:
        payload = raw_json(header)
        header_id = clean(payload.get("Id")) or header.legacy_record_id.split("#", 1)[0]
        headers_by_id[header_id] = header

    lines_by_header = defaultdict(list)
    for line in lines:
        lines_by_header[line.legacy_parent_id].append(line)

    existing = Usage.search_read([("legacy_fact_model", "=", SOURCE_MODEL)], ["legacy_fact_id"])
    existing_ids = {row["legacy_fact_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    planned = 0
    created = 0
    skipped_existing = 0
    blocked = 0
    planned_amount = 0.0

    for line in lines:
        line_payload = raw_json(line)
        header = headers_by_id.get(line.legacy_parent_id)
        header_payload = raw_json(header) if header else {}
        project_id = project_by_legacy_id(project_cache, header.project_legacy_id if header else "", header.project_name if header else "")
        equipment_name = clean(line_payload.get("CLMC"))
        qty = to_float(line_payload.get("SL"))
        amount = to_float(line_payload.get("JE"))
        unit_price = to_float(line_payload.get("DJ"))
        unit_name = clean(line_payload.get("DW")) or clean(line_payload.get("GGDW"))
        reason = ""
        if not header:
            reason = "missing_legacy_header"
        elif not header.active or not line.active:
            reason = "inactive_legacy_record"
        elif not project_id:
            reason = "missing_project_anchor"
        elif not equipment_name:
            reason = "missing_equipment_name"
        elif qty <= 0:
            reason = "non_positive_usage_qty"

        if line.id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
        elif reason:
            action = "blocked"
            blocked += 1
            residual_rows.append(
                {
                    "legacy_line_id": line.legacy_record_id,
                    "legacy_header_id": line.legacy_parent_id,
                    "document_no": header.document_no if header else "",
                    "project_legacy_id": header.project_legacy_id if header else "",
                    "project_name": header.project_name if header else "",
                    "equipment_name": equipment_name,
                    "qty": qty,
                    "unit_name": unit_name,
                    "amount": amount,
                    "reason": reason,
                }
            )
        else:
            action = "create_equipment_usage"
            planned += 1
            planned_amount += amount
            if apply:
                usage = Usage.create(
                    {
                        "name": header.document_no or "A_SCBS机械单-%s" % line.legacy_parent_id,
                        "project_id": project_id,
                        "usage_date": to_date(str(header_payload.get("DJRQ") or header.document_date or "")),
                        "equipment_name": equipment_name,
                        "usage_location": clean(header_payload.get("SGBW")) or clean(line_payload.get("GGDW")) or "历史机械使用",
                        "operator_name": clean(header_payload.get("JXLB")) or clean(header_payload.get("TXR")) or "历史操作人",
                        "usage_qty": 1.0,
                        "usage_hours": qty,
                        "state": "confirmed",
                        "legacy_fact_model": SOURCE_MODEL,
                        "legacy_fact_id": line.id,
                        "legacy_fact_type": "equipment_usage",
                        "note": "\n".join(
                            [
                                "旧系统保盛机械单明细迁入。",
                                "source_table=%s/%s" % (SOURCE_HEADER_TABLE, SOURCE_LINE_TABLE),
                                "legacy_header_id=%s" % line.legacy_parent_id,
                                "legacy_line_id=%s" % line.legacy_record_id,
                                "legacy_document_no=%s" % (header.document_no or ""),
                                "legacy_unit=%s" % unit_name,
                                "legacy_qty=%s" % qty,
                                "legacy_unit_price=%s" % unit_price,
                                "legacy_amount=%s" % amount,
                                "legacy_line_note=%s" % clean(line_payload.get("BZ")),
                                "legacy_creator=%s(%s)" % (clean(header_payload.get("LRR")), clean(header_payload.get("LRRID"))),
                            ]
                        ),
                    }
                )
                created += 1 if usage else 0

        plan_rows.append(
            {
                "legacy_line_id": line.legacy_record_id,
                "legacy_fact_id": line.id,
                "legacy_header_id": line.legacy_parent_id,
                "document_no": header.document_no if header else "",
                "project_legacy_id": header.project_legacy_id if header else "",
                "project_name": header.project_name if header else "",
                "equipment_name": equipment_name,
                "qty": qty,
                "unit_name": unit_name,
                "amount": amount,
                "target_model": "sc.equipment.usage",
                "action": action,
                "reason": reason,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fieldnames = [
        "legacy_line_id",
        "legacy_fact_id",
        "legacy_header_id",
        "document_no",
        "project_legacy_id",
        "project_name",
        "equipment_name",
        "qty",
        "unit_name",
        "amount",
        "target_model",
        "action",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)
    write_csv(residual_csv, residual_rows, [key for key in fieldnames if key not in {"legacy_fact_id", "target_model", "action"}])
    result = {
        "status": "PASS",
        "mode": "legacy_a_scbs_equipment_usage_projection",
        "apply": apply,
        "header_rows": len(headers),
        "line_rows": len(lines),
        "planned_usage_rows": planned,
        "planned_amount": round(planned_amount, 2),
        "created": created,
        "skipped_existing": skipped_existing,
        "blocked_rows": blocked,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_A_SCBS_EQUIPMENT_USAGE_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
