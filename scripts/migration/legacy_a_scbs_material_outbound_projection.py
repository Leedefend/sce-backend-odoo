"""Project legacy A_SCBS material outbound facts into sc.material.outbound.

Dry-run by default. Set MIGRATION_APPLY=1 or APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


SOURCE_MODEL = "legacy.main.A_SCBS_CLCKD"
SOURCE_HEADER_TABLE = "A_SCBS_CLCKD"
SOURCE_LINE_TABLE = "A_SCBS_CLCKD_CB"


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


def partner_by_name(cache: dict[str, int | bool], name: str):
    key = clean(name)
    if not key:
        return False
    if key in cache:
        return cache[key]
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.search([("name", "=", key)], limit=1)
    if not partner:
        partner = Partner.create({"name": key})
    cache[key] = partner.id
    return cache[key]


def catalog_for_line(cache: dict[str, int], payload: dict[str, object], project_id: int | bool, *, create_missing: bool):
    name = clean(payload.get("CLMC")) or "历史材料（未命名）"
    spec = clean(payload.get("GGXH"))
    uom_text = clean(payload.get("DW"))
    key = "|".join([name, spec, uom_text, str(project_id or "")])
    if key in cache:
        return cache[key]
    Catalog = env["sc.material.catalog"].sudo().with_context(active_test=False)  # noqa: F821
    domain = [
        ("name", "=", name),
        ("spec_model", "=", spec),
        ("uom_text", "=", uom_text),
        ("company_id", "=", env.company.id),  # noqa: F821
    ]
    catalog = Catalog.search(domain + [("project_id", "=", project_id or False)], limit=1)
    if not catalog:
        catalog = Catalog.search(domain, limit=1)
    if not catalog and not create_missing:
        cache[key] = -1
        return cache[key]
    if not catalog:
        project = env["project.project"].sudo().browse(project_id) if project_id else False  # noqa: F821
        company_id = project.company_id.id if project and project.company_id else env.company.id  # noqa: F821
        catalog_project_id = project.id if project and project.company_id else False
        catalog = Catalog.create(
            {
                "name": name,
                "spec_model": spec,
                "uom_text": uom_text,
                "company_id": company_id,
                "project_id": catalog_project_id,
                "source_origin": "legacy",
                "legacy_material_id": "A_SCBS_CLCKD_CB:%s|%s|%s" % (name, spec, uom_text),
            }
        )
    cache[key] = catalog.id
    return cache[key]


def uom_id(cache: dict[str, int | bool], uom_text: str):
    key = clean(uom_text)
    if not key:
        return False
    if key not in cache:
        uom = env["uom.uom"].sudo().search([("name", "=", key)], limit=1)  # noqa: F821
        cache[key] = uom.id if uom else False
    return cache[key]


def line_values(record, project_id: int | bool, catalog_cache: dict[str, int], uom_cache: dict[str, int | bool], *, create_missing_catalog: bool):
    payload = raw_json(record)
    qty = to_float(payload.get("SL"))
    amount = to_float(payload.get("JE"))
    unit_price = amount / qty if qty else 0.0
    return {
        "material_catalog_id": catalog_for_line(catalog_cache, payload, project_id, create_missing=create_missing_catalog),
        "material_spec": clean(payload.get("GGXH")),
        "product_uom_id": uom_id(uom_cache, clean(payload.get("DW"))),
        "qty": qty,
        "note": "历史明细%s; 原单位=%s; 原单价=%s; 原金额=%s; 折算单价=%s"
        % (
            record.legacy_record_id,
            clean(payload.get("DW")),
            clean(payload.get("DJ")),
            clean(payload.get("JE")),
            unit_price,
        ),
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "legacy_a_scbs_material_outbound_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_a_scbs_material_outbound_projection_residual_v1.csv"
    result_json = artifacts / "legacy_a_scbs_material_outbound_projection_result_v1.json"

    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Outbound = env["sc.material.outbound"].sudo().with_context(active_test=False)  # noqa: F821
    headers = Residual.search([("source_table", "=", SOURCE_HEADER_TABLE)], order="document_date, id")
    line_records = Residual.search([("source_table", "=", SOURCE_LINE_TABLE)], order="legacy_parent_id, id")
    lines_by_header = defaultdict(list)
    for line in line_records:
        lines_by_header[line.legacy_parent_id].append(line)

    existing = Outbound.search_read([("legacy_fact_model", "=", SOURCE_MODEL)], ["legacy_fact_id"])
    existing_ids = {row["legacy_fact_id"] for row in existing}
    project_cache: dict[str, int | bool] = {}
    partner_cache: dict[str, int | bool] = {}
    catalog_cache: dict[str, int] = {}
    uom_cache: dict[str, int | bool] = {}

    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    created = 0
    skipped_existing = 0
    repaired_existing = 0
    blocked_headers = 0
    planned_headers = 0
    planned_lines = 0
    planned_amount = 0.0

    for header in headers:
        payload = raw_json(header)
        header_id = clean(payload.get("Id")) or header.legacy_record_id.split("#", 1)[0]
        header_lines = [line for line in lines_by_header.get(header_id, []) if line.active]
        project_id = project_by_legacy_id(project_cache, header.project_legacy_id, header.project_name)
        projectable_lines = []
        reason = ""
        if not header.active:
            reason = "inactive_legacy_header"
        elif not project_id:
            reason = "missing_project_anchor"
        elif not header_lines:
            reason = "missing_legacy_lines"
        else:
            for line in header_lines:
                values = line_values(line, project_id, catalog_cache, uom_cache, create_missing_catalog=apply)
                if to_float(values["qty"]) <= 0:
                    reason = "non_positive_qty"
                    break
                projectable_lines.append(values)

        line_amount = sum(to_float(raw_json(line).get("JE")) for line in header_lines)
        if header.id in existing_ids:
            action = "skip_existing"
            skipped_existing += 1
            if apply and projectable_lines:
                outbound = Outbound.search([("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", header.id)], limit=1)
                for target_line, values in zip(outbound.line_ids.sorted("id"), projectable_lines):
                    target_line.write(values)
                repaired_existing += 1 if outbound else 0
        elif reason:
            action = "blocked"
            blocked_headers += 1
            residual_rows.append(
                {
                    "legacy_header_id": header_id,
                    "document_no": header.document_no,
                    "project_legacy_id": header.project_legacy_id,
                    "project_name": header.project_name,
                    "header_amount": header.amount_total,
                    "line_rows": len(header_lines),
                    "line_amount": round(line_amount, 2),
                    "reason": reason,
                }
            )
        else:
            action = "create_material_outbound"
            planned_headers += 1
            planned_lines += len(projectable_lines)
            planned_amount += line_amount
            if apply:
                outbound = Outbound.create(
                    {
                        "name": header.document_no or "A_SCBS出库单-%s" % header_id,
                        "project_id": project_id,
                        "outbound_date": to_date(str(payload.get("YLRQ") or header.document_date or "")),
                        "receiver_id": partner_by_name(partner_cache, clean(payload.get("LWBG"))),
                        "state": "issued",
                        "purpose": clean(payload.get("SGBW")),
                        "legacy_fact_model": SOURCE_MODEL,
                        "legacy_fact_id": header.id,
                        "legacy_fact_type": "material_outbound",
                        "note": "\n".join(
                            [
                                "旧系统保盛材料出库事实迁入。",
                                "source_table=%s/%s" % (SOURCE_HEADER_TABLE, SOURCE_LINE_TABLE),
                                "legacy_header_id=%s" % header_id,
                                "legacy_pid=%s" % (header.legacy_pid or ""),
                                "legacy_header_amount=%s" % (header.amount_total or 0),
                                "legacy_line_amount=%.2f" % line_amount,
                                "legacy_receiver=%s" % clean(payload.get("LWBG")),
                                "legacy_creator=%s(%s)" % (clean(payload.get("LRR")), clean(payload.get("LRRID"))),
                            ]
                        ),
                        "line_ids": [(0, 0, values) for values in projectable_lines],
                    }
                )
                created += 1 if outbound else 0

        plan_rows.append(
            {
                "legacy_header_id": header_id,
                "legacy_fact_id": header.id,
                "document_no": header.document_no,
                "project_legacy_id": header.project_legacy_id,
                "project_name": header.project_name,
                "header_amount": header.amount_total,
                "line_rows": len(header_lines),
                "line_amount": round(line_amount, 2),
                "target_model": "sc.material.outbound",
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
        "header_amount",
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
        "mode": "legacy_a_scbs_material_outbound_projection",
        "apply": apply,
        "header_rows": len(headers),
        "line_rows": len(line_records),
        "planned_headers": planned_headers,
        "planned_lines": planned_lines,
        "planned_amount": round(planned_amount, 2),
        "created": created,
        "skipped_existing": skipped_existing,
        "repaired_existing": repaired_existing,
        "blocked_headers": blocked_headers,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, result)
    print("LEGACY_A_SCBS_MATERIAL_OUTBOUND_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
