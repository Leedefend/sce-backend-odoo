"""Project SCBS negative payment rows into historical adjustment facts.

Negative rows are not written to sc.payment.execution because that model
represents positive payment execution. They are preserved here as source-tagged
historical refund/return/adjustment facts.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.scbs.fact.staging"
SOURCE_TABLE = "T_FK_Supplier"
IMPORT_BATCH = "scbs_negative_payment_adjustment_v1"


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


def classify(fact) -> str:
    text = " ".join(
        clean(value)
        for value in [
            fact.document_no,
            fact.project_id.display_name if fact.project_id else "",
            fact.partner_id.display_name if fact.partner_id else "",
            fact.legacy_xmmc,
            fact.legacy_partner_name,
            fact.note,
        ]
    )
    if any(token in text for token in ["调户", "调账", "调整", "冲账", "冲销", "保证金"]):
        return "account_or_internal_adjustment"
    if any(token in text for token in ["退回", "退款", "退还", "退付", "返还", "还款", "退税"]):
        return "refund_or_return"
    return "negative_without_text_semantics"


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_negative_payment_adjustment_projection_plan_v1.csv"
    result_json = artifacts / "scbs_negative_payment_adjustment_projection_result_v1.json"

    Fact = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    Target = env["sc.legacy.payment.adjustment.fact"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Fact.search(
        [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", True),
            ("mapping_gate_state", "=", "projection_ready"),
            ("fact_family", "=", "payment"),
            ("source_table", "=", SOURCE_TABLE),
            ("project_id", "!=", False),
            ("amount_total", "<", 0),
        ],
        order="document_date, id",
    )
    existing = Target.search_read(
        [("legacy_source_model", "=", SOURCE_MODEL), ("legacy_source_table", "=", SOURCE_TABLE)],
        ["legacy_record_id"],
    )
    existing_ids = {row["legacy_record_id"] for row in existing}

    plan_rows: list[dict[str, object]] = []
    created = 0
    skipped_existing = 0
    amount_total = 0.0
    classification_counts: dict[str, int] = {}
    classification_amounts: dict[str, float] = {}

    for fact in facts:
        classification = classify(fact)
        amount = fact.amount_total or 0.0
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        classification_amounts[classification] = classification_amounts.get(classification, 0.0) + amount
        amount_total += amount
        action = "skip_existing" if fact.legacy_record_id in existing_ids else "create_payment_adjustment_fact"
        if action == "skip_existing":
            skipped_existing += 1
        elif apply:
            Target.create(
                {
                    "legacy_source_model": SOURCE_MODEL,
                    "legacy_source_table": fact.source_table,
                    "legacy_record_id": fact.legacy_record_id,
                    "legacy_pid": fact.legacy_pid,
                    "document_no": fact.document_no,
                    "document_date": fact.document_date,
                    "legacy_document_state": fact.document_state,
                    "adjustment_classification": classification,
                    "source_amount": amount,
                    "absolute_amount": abs(amount),
                    "project_id": fact.project_id.id,
                    "partner_id": fact.partner_id.id or False,
                    "legacy_project_id": fact.legacy_xmid,
                    "legacy_project_name": fact.legacy_xmmc or fact.legacy_gcmc,
                    "legacy_partner_id": fact.legacy_partner_id,
                    "legacy_partner_name": fact.legacy_partner_name,
                    "source_note": clean(fact.note),
                    "note": "\n".join(
                        [
                            "SCBS历史负数付款事实承接。",
                            "该事实不写入正向付款执行模型。",
                            "classification=%s" % classification,
                        ]
                    ),
                    "import_batch": IMPORT_BATCH,
                }
            )
            created += 1
        plan_rows.append(
            {
                "staging_id": fact.id,
                "legacy_record_id": fact.legacy_record_id,
                "document_no": fact.document_no,
                "document_date": fact.document_date,
                "project_id": fact.project_id.id,
                "project_name": fact.project_id.display_name,
                "partner_id": fact.partner_id.id if fact.partner_id else "",
                "partner_name": fact.partner_id.display_name if fact.partner_id else fact.legacy_partner_name,
                "amount_total": amount,
                "classification": classification,
                "target_model": "sc.legacy.payment.adjustment.fact",
                "action": action,
            }
        )

    if apply:
        env.cr.commit()  # noqa: F821

    fields = [
        "staging_id",
        "legacy_record_id",
        "document_no",
        "document_date",
        "project_id",
        "project_name",
        "partner_id",
        "partner_name",
        "amount_total",
        "classification",
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
        "amount_total": amount_total,
        "classification_counts": classification_counts,
        "classification_amounts": classification_amounts,
        "plan_csv": str(plan_csv),
    }
    write_json(result_json, payload)
    print("SCBS_NEGATIVE_PAYMENT_ADJUSTMENT_PROJECTION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
