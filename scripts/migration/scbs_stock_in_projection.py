"""Project SCBS stock-in facts into sc.material.inbound.

Policy:
- write only headers whose project is confirmed and whose all legacy lines have
  confirmed sc.material.catalog mapping;
- keep product_id as the hidden technical fallback supplied by the material
  default mixin;
- use legacy line amount / quantity as unit_price so formal line totals follow
  SCBS line facts instead of mismatching header totals.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"
SOURCE_TABLE = "T_RK_RKD"
SOURCE_LINE_TABLE = "T_RK_RKDCB"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


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


def to_float(value: str | float | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def material_key(row: dict[str, str]) -> str:
    return "|".join(
        [
            (row.get("legacy_material_id") or "").strip(),
            (row.get("material_name") or "").strip(),
            (row.get("spec_model") or "").strip(),
            (row.get("uom_text") or "").strip(),
        ]
    )


def read_lines(path: Path) -> dict[str, list[dict[str, str]]]:
    if not path.exists():
        raise RuntimeError({"missing_stock_in_line_csv": str(path)})
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            grouped[row["legacy_record_id"]].append(row)
    return grouped


def uom_id(uom_text: str, cache: dict[str, int | bool]):
    key = (uom_text or "").strip()
    if not key:
        return False
    if key not in cache:
        uom = env["uom.uom"].sudo().search([("name", "=", key)], limit=1)  # noqa: F821
        cache[key] = uom.id if uom else False
    return cache[key]


def line_values(line: dict[str, str], material_map, uom_cache: dict[str, int | bool]) -> dict[str, object]:
    qty = to_float(line.get("qty"))
    amount = to_float(line.get("amount"))
    unit_price = amount / qty if qty else 0.0
    return {
        "material_catalog_id": material_map.material_catalog_id.id,
        "material_spec": line.get("spec_model") or material_map.spec_model or "",
        "product_uom_id": uom_id(line.get("uom_text") or material_map.uom_text or "", uom_cache),
        "qty": qty,
        "unit_price": unit_price,
        "note": "SCBS明细%s; 原单位=%s; 原单价=%s; 原金额=%s"
        % (
            line.get("legacy_line_id") or "",
            line.get("uom_text") or "",
            line.get("unit_price") or "",
            line.get("amount") or "",
        ),
    }


def is_zero_placeholder_line(line: dict[str, str]) -> bool:
    qty = to_float(line.get("qty"))
    amount = to_float(line.get("amount"))
    material_name = (line.get("material_name") or "").strip()
    return qty == 0 and amount == 0 and material_name in ("", "-", "NULL")


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    line_csv = Path(os.getenv("SCBS_STOCK_IN_LINE_CSV") or (repo_root() / "artifacts/migration/scbs_stock_in_legacy_lines_v1.csv"))
    plan_csv = artifacts / "scbs_stock_in_projection_plan_v1.csv"
    residual_csv = artifacts / "scbs_stock_in_projection_residual_v1.csv"
    result_json = artifacts / "scbs_stock_in_projection_result_v1.json"

    lines_by_header = read_lines(line_csv)
    Fact = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    Inbound = env["sc.material.inbound"].sudo().with_context(active_test=False)  # noqa: F821
    MaterialMap = env["sc.legacy.scbs.material.map"].sudo().with_context(active_test=False)  # noqa: F821

    material_maps = MaterialMap.search([("source_domain", "=", "SCBS"), ("source_table", "=", SOURCE_LINE_TABLE)])
    material_by_key = {record.material_key: record for record in material_maps}
    existing = Inbound.search_read(
        [("legacy_fact_model", "=", SOURCE_MODEL), ("legacy_fact_type", "=", "stock_in")],
        ["legacy_fact_id"],
    )
    existing_ids = {row["legacy_fact_id"] for row in existing}
    facts = Fact.search(
        [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", True),
            ("mapping_gate_state", "=", "projection_ready"),
            ("fact_family", "=", "stock_in"),
            ("project_id", "!=", False),
        ],
        order="document_date, id",
    )

    plan_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    created = 0
    skipped_existing = 0
    blocked_headers = 0
    blocked_amount = 0.0
    planned_line_rows = 0
    planned_line_amount = 0.0
    skipped_zero_placeholder_lines = 0
    uom_cache: dict[str, int | bool] = {}

    for fact in facts:
        header_lines = lines_by_header.get(fact.legacy_record_id, [])
        projectable_lines = [line for line in header_lines if not is_zero_placeholder_line(line)]
        skipped_zero_placeholder_lines += len(header_lines) - len(projectable_lines)
        line_amount = sum(to_float(line.get("amount")) for line in header_lines)
        if fact.id in existing_ids:
            skipped_existing += 1
            action = "skip_existing"
            reason = ""
        else:
            action = "create_material_inbound"
            reason = ""
            if not projectable_lines:
                reason = "missing_legacy_lines"
            for line in projectable_lines:
                qty = to_float(line.get("qty"))
                key = material_key(line)
                material_map = material_by_key.get(key)
                if qty <= 0:
                    reason = "non_positive_qty"
                    break
                if not material_map:
                    reason = "missing_material_map"
                    break
                if material_map.mapping_state != "confirmed" or not material_map.material_catalog_id:
                    reason = "unconfirmed_material_catalog"
                    break
        if reason:
            blocked_headers += 1
            blocked_amount += line_amount
            action = "blocked"
            residual_rows.append(
                {
                    "staging_id": fact.id,
                    "legacy_record_id": fact.legacy_record_id,
                    "document_no": fact.document_no,
                    "project_id": fact.project_id.id,
                    "project_name": fact.project_id.display_name,
                    "header_amount": fact.amount_total,
                    "line_rows": len(header_lines),
                    "line_amount": line_amount,
                    "reason": reason,
                }
            )
        elif apply and action == "create_material_inbound":
            inbound = Inbound.create(
                {
                    "name": fact.document_no or "SCBS入库单-%s" % fact.legacy_record_id,
                    "project_id": fact.project_id.id,
                    "inbound_date": fact.document_date,
                    "supplier_id": fact.partner_id.id or False,
                    "state": "received",
                    "legacy_fact_model": SOURCE_MODEL,
                    "legacy_fact_id": fact.id,
                    "legacy_fact_type": "stock_in",
                    "note": "\n".join(
                        [
                            "SCBS历史入库事实迁入。",
                            "legacy_record_id=%s" % fact.legacy_record_id,
                            "source_table=%s/%s" % (SOURCE_TABLE, SOURCE_LINE_TABLE),
                            "legacy_header_amount=%s" % (fact.amount_total or 0),
                            "legacy_line_amount=%s" % line_amount,
                            "legacy_supplier_name=%s" % (fact.legacy_partner_name or ""),
                            "legacy_gcmc=%s" % (fact.legacy_gcmc or ""),
                        ]
                    ),
                    "line_ids": [
                        (0, 0, line_values(line, material_by_key[material_key(line)], uom_cache))
                        for line in projectable_lines
                    ],
                }
            )
            created += 1 if inbound else 0

        if action == "create_material_inbound":
            planned_line_rows += len(projectable_lines)
            planned_line_amount += line_amount
        plan_rows.append(
            {
                "staging_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "document_no": fact.document_no,
                "project_id": fact.project_id.id,
                "project_name": fact.project_id.display_name,
                "header_amount": fact.amount_total,
                "line_rows": len(projectable_lines),
                "line_amount": line_amount,
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
            "staging_id",
            "legacy_record_id",
            "document_no",
            "project_id",
            "project_name",
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
            "staging_id",
            "legacy_record_id",
            "document_no",
            "project_id",
            "project_name",
            "header_amount",
            "line_rows",
            "line_amount",
            "reason",
        ],
    )
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "line_csv": str(line_csv),
        "eligible_headers": len(facts),
        "planned_headers": len([row for row in plan_rows if row["action"] == "create_material_inbound"]),
        "planned_line_rows": planned_line_rows,
        "planned_line_amount": planned_line_amount,
        "skipped_zero_placeholder_lines": skipped_zero_placeholder_lines,
        "created_headers": created,
        "skipped_existing": skipped_existing,
        "blocked_headers": blocked_headers,
        "blocked_line_amount": blocked_amount,
        "plan_csv": str(plan_csv),
        "residual_csv": str(residual_csv),
    }
    write_json(result_json, payload)
    print("SCBS_STOCK_IN_PROJECTION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
