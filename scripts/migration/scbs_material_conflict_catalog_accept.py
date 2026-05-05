"""Accept SCBS missing-ID material text as material-catalog facts.

This does not promote materials into product.template/product.product. It only
creates sc.material.catalog rows for SCBS material text groups that have no
legacy material ID but are now accepted as business facts.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


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


def catalog_code(material_map) -> str:
    return "SCBS-GROUP-%s" % (material_map.material_key or str(material_map.id)).replace("|", "-")[:32]


def find_or_create_catalog(material_map, apply: bool):
    Catalog = env["sc.material.catalog"].sudo()  # noqa: F821
    domain = [
        ("company_id", "=", material_map.company_id.id),
        ("name", "=", material_map.material_name),
        ("spec_model", "=", material_map.spec_model or False),
        ("uom_text", "=", material_map.uom_text or False),
    ]
    existing = Catalog.search(domain, limit=1)
    if existing or not apply:
        return existing, bool(existing), False
    vals = {
        "company_id": material_map.company_id.id,
        "name": material_map.material_name,
        "code": catalog_code(material_map),
        "spec_model": material_map.spec_model or False,
        "uom_text": material_map.uom_text or False,
        "source_origin": "legacy",
        "remark": "SCBS缺少材料ID的历史材料文本组按业务事实创建。source_table=%s; material_key=%s"
        % (material_map.source_table or "", material_map.material_key or ""),
    }
    return Catalog.create(vals), False, True


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_material_conflict_catalog_accept_plan_v1.csv"
    result_json = artifacts / "scbs_material_conflict_catalog_accept_result_v1.json"

    MaterialMap = env["sc.legacy.scbs.material.map"].sudo()  # noqa: F821
    records = MaterialMap.search(
        [
            ("source_domain", "=", "SCBS"),
            ("source_table", "=", "T_RK_RKDCB"),
            ("mapping_state", "=", "conflict"),
            ("material_catalog_id", "=", False),
            ("material_name", "!=", False),
        ],
        order="amount_total desc, id",
    )
    rows: list[dict[str, object]] = []
    created = 0
    linked_existing = 0
    confirmed = 0
    for record in records:
        catalog, existed, was_created = find_or_create_catalog(record, apply)
        action = "create_material_catalog"
        if existed:
            action = "link_existing_catalog"
        if apply and catalog:
            record.write({"material_catalog_id": catalog.id, "mapping_state": "confirmed"})
            confirmed += 1
            created += 1 if was_created else 0
            linked_existing += 1 if existed else 0
        rows.append(
            {
                "map_id": record.id,
                "material_key": record.material_key,
                "material_name": record.material_name,
                "spec_model": record.spec_model or "",
                "uom_text": record.uom_text or "",
                "amount_total": record.amount_total,
                "line_rows": record.line_rows,
                "target_catalog_id": catalog.id if catalog else "",
                "target_catalog_name": catalog.display_name if catalog else "",
                "action": action,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    write_csv(
        plan_csv,
        rows,
        [
            "map_id",
            "material_key",
            "material_name",
            "spec_model",
            "uom_text",
            "amount_total",
            "line_rows",
            "target_catalog_id",
            "target_catalog_name",
            "action",
        ],
    )
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "planned_rows": len(rows),
        "created_catalogs": created,
        "linked_existing_catalogs": linked_existing,
        "confirmed_maps": confirmed,
        "plan_csv": str(plan_csv),
        "business_policy": "accept_scbs_material_text_as_catalog_fact_without_product_promotion",
    }
    write_json(result_json, payload)
    print("SCBS_MATERIAL_CONFLICT_CATALOG_ACCEPT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
