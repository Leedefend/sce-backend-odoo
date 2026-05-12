"""Project SCBS no-project payment/contract facts into enterprise carriers.

These rows are confirmed business facts, but the restored source has no
project ID/name clue. They must not be forced into project documents; they are
kept as company-scoped historical enterprise facts.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"
IMPORT_BATCH = "scbs_enterprise_no_project_fact_v1"


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


def clean(value) -> str:
    normalized = str(value or "").strip()
    if normalized.upper() == "NULL":
        return ""
    return normalized


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_enterprise_no_project_fact_projection_plan_v1.csv"
    result_json = artifacts / "scbs_enterprise_no_project_fact_projection_result_v1.json"

    Fact = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    Target = env["sc.legacy.enterprise.business.fact"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Fact.search(
        [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", True),
            ("mapping_gate_state", "=", "projection_ready"),
            ("fact_family", "in", ["payment", "supplier_contract"]),
            ("project_id", "=", False),
        ],
        order="fact_family, document_date, id",
    )
    existing = Target.search_read(
        [("legacy_source_model", "=", SOURCE_MODEL)],
        ["legacy_source_table", "legacy_record_id"],
    )
    existing_keys = {(row["legacy_source_table"], row["legacy_record_id"]) for row in existing}

    plan_rows: list[dict[str, object]] = []
    created = 0
    skipped_existing = 0
    family_counts: dict[str, int] = {}
    family_amounts: dict[str, float] = {}

    for fact in facts:
        family_counts[fact.fact_family] = family_counts.get(fact.fact_family, 0) + 1
        family_amounts[fact.fact_family] = family_amounts.get(fact.fact_family, 0.0) + (fact.amount_total or 0.0)
        key = (fact.source_table, fact.legacy_record_id)
        action = "skip_existing" if key in existing_keys else "create_enterprise_no_project_fact"
        if action == "skip_existing":
            skipped_existing += 1
        elif apply:
            Target.create(
                {
                    "legacy_source_model": SOURCE_MODEL,
                    "legacy_source_table": fact.source_table,
                    "legacy_record_id": fact.legacy_record_id,
                    "legacy_pid": fact.legacy_pid,
                    "fact_family": fact.fact_family,
                    "document_scope": "enterprise_no_project",
                    "document_no": fact.document_no,
                    "document_date": fact.document_date,
                    "legacy_document_state": fact.document_state,
                    "company_id": env.company.id,  # noqa: F821
                    "business_entity_id": fact.business_entity_id.id or False,
                    "operation_strategy": "direct",
                    "partner_id": fact.partner_id.id or False,
                    "legacy_partner_id": fact.legacy_partner_id,
                    "legacy_partner_name": fact.legacy_partner_name,
                    "amount_total": fact.amount_total or 0.0,
                    "creator_legacy_user_id": fact.creator_legacy_user_id,
                    "creator_name": fact.creator_name,
                    "created_time": fact.created_time,
                    "residual_reason": "no_source_project_clue",
                    "legacy_business_entity_id": fact.legacy_xmid,
                    "legacy_business_entity_name": fact.legacy_xmmc,
                    "legacy_project_name": fact.legacy_gcmc,
                    "source_note": clean(fact.note),
                    "note": "\n".join(
                        [
                            "SCBS历史无项目业务事实承接。",
                            "源数据没有可靠项目ID/项目名称/工程名称线索。",
                            "该事实按公司隔离层承接，不生成项目单据。",
                        ]
                    ),
                    "import_batch": IMPORT_BATCH,
                }
            )
            created += 1
        plan_rows.append(
            {
                "fact_family": fact.fact_family,
                "staging_id": fact.id,
                "legacy_source_table": fact.source_table,
                "legacy_record_id": fact.legacy_record_id,
                "document_no": fact.document_no,
                "document_date": fact.document_date,
                "partner_id": fact.partner_id.id if fact.partner_id else "",
                "partner_name": fact.partner_id.display_name if fact.partner_id else fact.legacy_partner_name,
                "amount_total": fact.amount_total or 0.0,
                "target_model": "sc.legacy.enterprise.business.fact",
                "action": action,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fields = [
        "fact_family",
        "staging_id",
        "legacy_source_table",
        "legacy_record_id",
        "document_no",
        "document_date",
        "partner_id",
        "partner_name",
        "amount_total",
        "target_model",
        "action",
    ]
    write_csv(plan_csv, plan_rows, fields)
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "eligible_rows": len(facts),
        "created_rows": created,
        "skipped_existing": skipped_existing,
        "family_counts": family_counts,
        "family_amounts": family_amounts,
        "plan_csv": str(plan_csv),
    }
    write_json(result_json, payload)
    print("SCBS_ENTERPRISE_NO_PROJECT_FACT_PROJECTION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
