"""Import SCBS source facts into staging with mapping-state snapshots.

Run through Odoo shell:

    odoo shell -c /var/lib/odoo/odoo.conf -d sc_prod_sim \\
      < scripts/migration/scbs_fact_staging_import.py

Default mode is dry-run. To write, set:

    SCBS_FACT_STAGING_IMPORT_MODE=write

The script consumes ``artifacts/migration/scbs_fact_staging_v1.csv``.
It writes only ``sc.legacy.scbs.fact.staging`` rows. It does not create or
modify formal contracts, payments, stock documents, projects, partners, or
companies.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def clean(value) -> str:
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def null_clean(value) -> str:
    text = clean(value)
    return "" if text.upper() == "NULL" else text


def as_float(value) -> float:
    text = clean(value)
    if text in {"", "."}:
        return 0.0
    if text.startswith("."):
        text = "0" + text
    return float(text)


def as_datetime(value) -> str | bool:
    text = null_clean(value)
    if not text:
        return False
    if "." in text:
        text = text.split(".", 1)[0]
    return text[:19]


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/scbs_fact_staging_v1.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root(root: Path) -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([root / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821 - Odoo shell global
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def source_creator_evidence(root: Path) -> dict[tuple[str, str], dict[str, str]]:
    candidates = []
    env_path = os.getenv("SCBS_SOURCE_CREATOR_CSV")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(root / "artifacts/migration/scbs_source_creator_supplement_v1.csv")
    evidence: dict[tuple[str, str], dict[str, str]] = {}
    for path in candidates:
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                source_table = clean(row.get("source_table"))
                legacy_record_id = clean(row.get("legacy_record_id"))
                if not source_table or not legacy_record_id:
                    continue
                evidence[(source_table, legacy_record_id)] = row
    return evidence


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def partner_key(name: str, tax_code: str, suggested_state: str) -> str:
    return "|".join([name.casefold(), tax_code.casefold(), suggested_state])


def business_entity_map(legacy_xmid: str):
    Mapping = env["sc.legacy.business.entity.map"]  # noqa: F821
    if not legacy_xmid:
        return Mapping.browse()
    return Mapping.search([("source_domain", "=", "SCBS"), ("legacy_xmid", "=", legacy_xmid)], limit=1)


def project_map(legacy_gcmc: str):
    Mapping = env["sc.legacy.project.map"]  # noqa: F821
    if not legacy_gcmc:
        return Mapping.browse()
    return Mapping.search([("source_domain", "=", "SCBS"), ("legacy_gcmc", "=", legacy_gcmc)], limit=1)


def partner_map(name: str, tax_code: str):
    Mapping = env["sc.legacy.partner.map"]  # noqa: F821
    if not name:
        return Mapping.browse()
    candidates = Mapping.search(
        [
            ("source_domain", "=", "SCBS"),
            ("legacy_partner_name", "=", name),
        ]
    )
    if not candidates:
        return Mapping.browse()
    if tax_code:
        exact_tax = candidates.filtered(lambda rec: (rec.legacy_tax_code or "").casefold() == tax_code.casefold())
        if len(exact_tax) == 1:
            return exact_tax
    if len(candidates) == 1:
        return candidates
    non_conflict = candidates.filtered(lambda rec: rec.suggested_state != "tax_code_conflict")
    return non_conflict if len(non_conflict) == 1 else Mapping.browse()


def main() -> None:
    ensure_allowed_db()
    mode = os.getenv("SCBS_FACT_STAGING_IMPORT_MODE", "dry-run")
    write_mode = mode == "write"
    if mode not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_mode": mode, "expected": ["dry-run", "write"]})

    root = repo_root()
    artifacts = artifact_root(root)
    input_csv = root / "artifacts/migration/scbs_fact_staging_v1.csv"
    result_json = artifacts / "scbs_fact_staging_import_result_v1.json"
    rollback_csv = artifacts / "scbs_fact_staging_import_rollback_targets_v1.csv"
    preview_csv = artifacts / "scbs_fact_staging_import_preview_v1.csv"

    rows = read_rows(input_csv)
    creator_evidence = source_creator_evidence(root)
    Staging = env["sc.legacy.scbs.fact.staging"]  # noqa: F821
    allowed_families = {"payment", "supplier_contract", "stock_in", "fund_daily"}

    preview_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    created = 0
    updated = 0

    for index, row in enumerate(rows, start=2):
        source_table = clean(row.get("source_table"))
        legacy_record_id = clean(row.get("legacy_record_id"))
        source_creator_row = creator_evidence.get((source_table, legacy_record_id), {})
        fact_family = clean(row.get("fact_family"))
        if not source_table or not legacy_record_id:
            errors.append({"line": index, "error": "missing_source_identity"})
            continue
        if fact_family not in allowed_families:
            errors.append({"line": index, "source_table": source_table, "legacy_record_id": legacy_record_id, "error": "unexpected_fact_family"})
            continue

        legacy_xmid = null_clean(row.get("legacy_xmid"))
        legacy_gcmc = null_clean(row.get("legacy_gcmc"))
        legacy_partner_name = null_clean(row.get("legacy_partner_name"))
        legacy_partner_tax_code = null_clean(row.get("legacy_partner_tax_code"))
        entity_mapping = business_entity_map(legacy_xmid)
        project_mapping = project_map(legacy_gcmc)
        partner_mapping = partner_map(legacy_partner_name, legacy_partner_tax_code)
        existing = Staging.search([("source_table", "=", source_table), ("legacy_record_id", "=", legacy_record_id)], limit=1)

        vals = {
            "source_domain": "SCBS",
            "source_table": source_table,
            "legacy_record_id": legacy_record_id,
            "legacy_pid": null_clean(row.get("legacy_pid")),
            "fact_family": fact_family,
            "document_no": null_clean(row.get("document_no")),
            "document_date": null_clean(row.get("document_date")) or False,
            "document_state": null_clean(row.get("document_state")),
            "deleted_flag": null_clean(row.get("deleted_flag")),
            "amount_total": as_float(row.get("amount_total")),
            "creator_legacy_user_id": null_clean(row.get("creator_legacy_user_id"))
            or null_clean(source_creator_row.get("creator_legacy_user_id")),
            "creator_name": null_clean(row.get("creator_name")) or null_clean(source_creator_row.get("creator_name")),
            "created_time": as_datetime(row.get("created_time")) or as_datetime(source_creator_row.get("created_time")),
            "legacy_xmid": legacy_xmid,
            "legacy_xmmc": null_clean(row.get("legacy_xmmc")),
            "business_entity_map_id": entity_mapping.id if entity_mapping else False,
            "legacy_gcmc": legacy_gcmc,
            "project_map_id": project_mapping.id if project_mapping else False,
            "legacy_partner_id": null_clean(row.get("legacy_partner_id")),
            "legacy_partner_name": legacy_partner_name,
            "legacy_partner_tax_code": legacy_partner_tax_code,
            "partner_map_id": partner_mapping.id if partner_mapping else False,
            "import_batch": "scbs_fact_staging_v1",
            "note": null_clean(row.get("note")),
        }
        preview_rows.append(
            {
                "source_table": source_table,
                "legacy_record_id": legacy_record_id,
                "fact_family": fact_family,
                "action": "update" if existing else "create",
                "business_entity_map_id": entity_mapping.id if entity_mapping else "",
                "project_map_id": project_mapping.id if project_mapping else "",
                "partner_map_id": partner_mapping.id if partner_mapping else "",
                "amount_total": vals["amount_total"],
                "creator_name": vals["creator_name"],
                "created_time": vals["created_time"] or "",
            }
        )

        if not write_mode:
            continue
        if existing:
            existing.write(vals)
            staging = existing
            updated += 1
        else:
            staging = Staging.create(vals)
            created += 1
        rollback_rows.append(
            {
                "model": "sc.legacy.scbs.fact.staging",
                "id": staging.id,
                "source_table": source_table,
                "legacy_record_id": legacy_record_id,
            }
        )

    write_csv(
        preview_csv,
        [
            "source_table",
            "legacy_record_id",
            "fact_family",
            "action",
            "business_entity_map_id",
            "project_map_id",
            "partner_map_id",
            "amount_total",
            "creator_name",
            "created_time",
        ],
        preview_rows,
    )
    write_csv(rollback_csv, ["model", "id", "source_table", "legacy_record_id"], rollback_rows)

    if errors:
        payload = {
            "status": "FAIL",
            "mode": mode,
            "database": env.cr.dbname,  # noqa: F821
            "input_csv": str(input_csv),
            "errors": errors[:100],
            "error_count": len(errors),
        }
        write_json(result_json, payload)
        raise RuntimeError(payload)

    if write_mode:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "input_csv": str(input_csv),
        "source_rows": len(rows),
        "source_creator_evidence_rows": len(creator_evidence),
        "preview_rows": len(preview_rows),
        "created": created,
        "updated": updated,
        "staging_count": Staging.search_count([("import_batch", "=", "scbs_fact_staging_v1")]),
        "preview_csv": str(preview_csv),
        "rollback_csv": str(rollback_csv),
    }
    write_json(result_json, payload)
    print("SCBS_FACT_STAGING_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
