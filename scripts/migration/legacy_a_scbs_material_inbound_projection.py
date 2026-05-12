"""Project legacy A_SCBS material inbound facts into sc.material.inbound.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


SOURCE_MODEL = "legacy.main.A_SCBS_CLRKD"
SOURCE_HEADER_TABLE = "A_SCBS_CLRKD"
SOURCE_LINE_TABLE = "A_SCBS_CLRKD_CB"


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt/artifacts/migration"), Path.cwd() / "artifacts/migration", Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("/tmp")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError({"missing_legacy_a_scbs_material_inbound_header_csv": str(path)})
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


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_date(value: str):
    if not value:
        return False
    return value[:10]


def raw_json(record) -> dict[str, object]:
    try:
        return json.loads(record.raw_payload or "{}")
    except json.JSONDecodeError:
        return {}


def clean(value) -> str:
    return str(value or "").strip()


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
        partner = Partner.create({"name": key, "supplier_rank": 1})
    elif partner.supplier_rank <= 0:
        partner.write({"supplier_rank": 1})
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
                "legacy_material_id": "A_SCBS_CLRKD_CB:%s|%s|%s" % (name, spec, uom_text),
            }
        )
    cache[key] = catalog.id
    return catalog.id


def uom_id(cache: dict[str, int | bool], uom_text: str):
    key = clean(uom_text)
    if not key:
        return False
    if key not in cache:
        uom = env["uom.uom"].sudo().search([("name", "=", key)], limit=1)  # noqa: F821
        cache[key] = uom.id if uom else False
    return cache[key]


def line_values(
    record,
    project_id: int | bool,
    catalog_cache: dict[str, int],
    uom_cache: dict[str, int | bool],
    *,
    create_missing_catalog: bool,
) -> dict[str, object]:
    payload = raw_json(record)
    qty = to_float(payload.get("SL"))
    amount = to_float(payload.get("JE"))
    unit_price = amount / qty if qty else 0.0
    return {
        "material_catalog_id": catalog_for_line(
            catalog_cache,
            payload,
            project_id,
            create_missing=create_missing_catalog,
        ),
        "material_spec": clean(payload.get("GGXH")),
        "product_uom_id": uom_id(uom_cache, clean(payload.get("DW"))),
        "qty": qty,
        "unit_price": unit_price,
        "note": "历史明细%s; 原单位=%s; 原单价=%s; 原金额=%s"
        % (record.legacy_record_id, clean(payload.get("DW")), clean(payload.get("DJ")), clean(payload.get("JE"))),
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1" or os.getenv("MIGRATION_APPLY") == "1"
    artifacts = artifact_root()
    header_csv = Path(os.getenv("LEGACY_A_SCBS_MATERIAL_INBOUND_HEADER_CSV") or artifacts / "legacy_a_scbs_material_inbound_headers_v1.csv")
    plan_csv = artifacts / "legacy_a_scbs_material_inbound_projection_plan_v1.csv"
    residual_csv = artifacts / "legacy_a_scbs_material_inbound_projection_residual_v1.csv"
    result_json = artifacts / "legacy_a_scbs_material_inbound_projection_result_v1.json"

    headers = read_csv(header_csv)
    Residual = env["sc.legacy.business.fact.residual"].sudo().with_context(active_test=False)  # noqa: F821
    Inbound = env["sc.material.inbound"].sudo().with_context(active_test=False)  # noqa: F821
    line_records = Residual.search([("source_table", "=", SOURCE_LINE_TABLE)], order="legacy_parent_id, id")
    lines_by_header = defaultdict(list)
    for line in line_records:
        lines_by_header[line.legacy_parent_id].append(line)

    existing = Inbound.search_read([("legacy_fact_model", "=", SOURCE_MODEL)], ["legacy_fact_id"])
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
    planned_headers = 0
    planned_lines = 0
    planned_amount = 0.0
    blocked_headers = 0

    for header in headers:
        header_id = clean(header.get("legacy_header_id"))
        if header.get("active") != "1":
            action = "blocked"
            reason = "inactive_legacy_header"
            header_lines = lines_by_header.get(header_id, [])
            fact_id = header_lines[0].id if header_lines else 0
        else:
            header_lines = [line for line in lines_by_header.get(header_id, []) if line.active]
            fact_id = header_lines[0].id if header_lines else 0
            project_id = project_by_legacy_id(project_cache, header.get("project_legacy_id") or "", header.get("project_name") or "")
            projectable_lines = []
            reason = ""
            if not project_id:
                reason = "missing_project_anchor"
            elif not header_lines:
                reason = "missing_legacy_lines"
            else:
                for line in header_lines:
                    values = line_values(
                        line,
                        project_id,
                        catalog_cache,
                        uom_cache,
                        create_missing_catalog=apply,
                    )
                    if to_float(values["qty"]) <= 0:
                        reason = "non_positive_qty"
                        break
                    projectable_lines.append(values)
            if fact_id in existing_ids:
                action = "skip_existing"
                skipped_existing += 1
                reason = ""
                if apply and projectable_lines:
                    inbound = Inbound.search(
                        [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_id", "=", fact_id)],
                        limit=1,
                    )
                    for target_line, values in zip(inbound.line_ids.sorted("id"), projectable_lines):
                        target_line.write(
                            {
                                "material_catalog_id": values["material_catalog_id"],
                                "material_spec": values["material_spec"],
                                "product_uom_id": values["product_uom_id"],
                                "qty": values["qty"],
                                "unit_price": values["unit_price"],
                                "note": values["note"],
                            }
                        )
                    repaired_existing += 1 if inbound else 0
            elif reason:
                action = "blocked"
            else:
                action = "create_material_inbound"

        line_amount = sum(to_float(raw_json(line).get("JE")) for line in lines_by_header.get(header_id, []))
        if action == "blocked":
            blocked_headers += 1
            residual_rows.append(
                {
                    "legacy_header_id": header_id,
                    "document_no": header.get("document_no") or "",
                    "project_legacy_id": header.get("project_legacy_id") or "",
                    "project_name": header.get("project_name") or "",
                    "supplier_name": header.get("supplier_name") or "",
                    "header_amount": header.get("amount_total") or "",
                    "line_rows": len(lines_by_header.get(header_id, [])),
                    "line_amount": round(line_amount, 2),
                    "reason": reason,
                }
            )
        elif action == "create_material_inbound":
            planned_headers += 1
            planned_lines += len(projectable_lines)
            planned_amount += line_amount
            if apply:
                supplier_id = partner_by_name(partner_cache, header.get("supplier_name") or "")
                inbound = Inbound.create(
                    {
                        "name": header.get("document_no") or "A_SCBS入库单-%s" % header_id,
                        "project_id": project_id,
                        "inbound_date": to_date(header.get("document_date") or header.get("created_at") or ""),
                        "supplier_id": supplier_id or False,
                        "state": "received",
                        "legacy_fact_model": SOURCE_MODEL,
                        "legacy_fact_id": fact_id,
                        "legacy_fact_type": "material_inbound",
                        "note": "\n".join(
                            [
                                "旧系统保盛材料入库事实迁入。",
                                "source_table=%s/%s" % (SOURCE_HEADER_TABLE, SOURCE_LINE_TABLE),
                                "legacy_header_id=%s" % header_id,
                                "legacy_pid=%s" % (header.get("legacy_pid") or ""),
                                "legacy_header_amount=%s" % (header.get("amount_total") or ""),
                                "legacy_line_amount=%.2f" % line_amount,
                                "legacy_supplier_name=%s" % (header.get("supplier_name") or ""),
                                "legacy_creator=%s(%s)" % (header.get("creator_name") or "", header.get("creator_legacy_user_id") or ""),
                            ]
                        ),
                        "line_ids": [(0, 0, values) for values in projectable_lines],
                    }
                )
                created += 1 if inbound else 0

        plan_rows.append(
            {
                "legacy_header_id": header_id,
                "legacy_fact_id": fact_id,
                "document_no": header.get("document_no") or "",
                "project_legacy_id": header.get("project_legacy_id") or "",
                "project_name": header.get("project_name") or "",
                "supplier_name": header.get("supplier_name") or "",
                "header_amount": header.get("amount_total") or "",
                "line_rows": len(lines_by_header.get(header_id, [])),
                "line_amount": round(line_amount, 2),
                "target_model": "sc.material.inbound",
                "action": action,
                "reason": reason,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    write_csv(
        plan_csv,
        plan_rows,
        [
            "legacy_header_id",
            "legacy_fact_id",
            "document_no",
            "project_legacy_id",
            "project_name",
            "supplier_name",
            "header_amount",
            "line_rows",
            "line_amount",
            "target_model",
            "action",
            "reason",
        ],
    )
    write_csv(
        residual_csv,
        residual_rows,
        [
            "legacy_header_id",
            "document_no",
            "project_legacy_id",
            "project_name",
            "supplier_name",
            "header_amount",
            "line_rows",
            "line_amount",
            "reason",
        ],
    )
    result = {
        "status": "PASS",
        "mode": "legacy_a_scbs_material_inbound_projection",
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
    print("LEGACY_A_SCBS_MATERIAL_INBOUND_PROJECTION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
