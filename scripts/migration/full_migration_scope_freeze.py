"""Freeze full migration scope and execution lanes without DB access."""

from __future__ import annotations

import csv
import json
from pathlib import Path


RAW_SOURCES = {
    "project": Path("tmp/raw/project/project.csv"),
    "partner_company": Path("tmp/raw/partner/company.csv"),
    "partner_supplier": Path("tmp/raw/partner/supplier.csv"),
    "contract": Path("tmp/raw/contract/contract.csv"),
    "project_member": Path("tmp/raw/project_member/project_member.csv"),
    "payment": Path("tmp/raw/payment/payment.csv"),
    "receipt": Path("tmp/raw/receipt/receipt.csv"),
}
JSON_ARTIFACTS = {
    "project_30_write": Path("artifacts/migration/project_create_only_write_result_v1.json"),
    "project_100_expand_write": Path("artifacts/migration/project_create_only_expand_write_result_v1.json"),
    "partner_30_write": Path("artifacts/migration/partner_30_row_write_result_v1.json"),
    "contract_12_write": Path("artifacts/migration/contract_12_row_write_result_v1.json"),
    "contract_12_post_review": Path("artifacts/migration/contract_12_row_post_write_review_result_v1.json"),
    "legacy_blueprint": Path("artifacts/migration/legacy_db_full_rebuild_blueprint_v1.json"),
}
OUTPUT_JSON = Path("artifacts/migration/full_migration_scope_freeze_v1.json")
OUTPUT_CSV = Path("artifacts/migration/full_migration_execution_lanes_v1.csv")


def count_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


raw_counts = {name: count_csv_rows(path) for name, path in RAW_SOURCES.items()}
artifacts = {name: read_json(path) for name, path in JSON_ARTIFACTS.items()}

project_created = (
    artifacts["project_30_write"].get("summary", {}).get("created", 0)
    + artifacts["project_100_expand_write"].get("summary", {}).get("created", 0)
)
partner_created = artifacts["partner_30_write"].get("summary", {}).get("created", 0)
contract_created = artifacts["contract_12_write"].get("summary", {}).get("created", 0)

lanes = [
    {
        "lane": "project_expand",
        "source": "tmp/raw/project/project.csv",
        "raw_rows": raw_counts["project"],
        "materialized_rows": project_created,
        "next_action": "bounded create-only expansion dry-run",
        "risk": "medium",
        "write_allowed_now": "no",
        "reason": "requires next bounded payload and post-write rollback lock",
    },
    {
        "lane": "partner_company_expand",
        "source": "tmp/raw/partner/company.csv",
        "raw_rows": raw_counts["partner_company"],
        "materialized_rows": partner_created,
        "next_action": "bounded company-primary create-only expansion dry-run",
        "risk": "medium",
        "write_allowed_now": "no",
        "reason": "cross-source conflicts remain manually gated",
    },
    {
        "lane": "partner_supplier_supplement",
        "source": "tmp/raw/partner/supplier.csv",
        "raw_rows": raw_counts["partner_supplier"],
        "materialized_rows": 0,
        "next_action": "no-DB supplement enrichment design after company-primary expansion",
        "risk": "medium",
        "write_allowed_now": "no",
        "reason": "supplier is supplemental-only and must not override company-primary identity",
    },
    {
        "lane": "contract_expand",
        "source": "tmp/raw/contract/contract.csv",
        "raw_rows": raw_counts["contract"],
        "materialized_rows": contract_created,
        "next_action": "bounded header expansion dry-run after project/partner anchors expand",
        "risk": "high",
        "write_allowed_now": "no",
        "reason": "depends on broader project and partner anchors",
    },
    {
        "lane": "project_member",
        "source": "tmp/raw/project_member/project_member.csv",
        "raw_rows": raw_counts["project_member"],
        "materialized_rows": 0,
        "next_action": "readiness screening only",
        "risk": "high",
        "write_allowed_now": "no",
        "reason": "may imply user/permission semantics and must not touch ACL implicitly",
    },
    {
        "lane": "payment",
        "source": "tmp/raw/payment/payment.csv",
        "raw_rows": raw_counts["payment"],
        "materialized_rows": 0,
        "next_action": "STOP: dedicated financial/payment task line required",
        "risk": "stop_domain",
        "write_allowed_now": "no",
        "reason": "payment lane is a financial stop domain",
    },
    {
        "lane": "receipt",
        "source": "tmp/raw/receipt/receipt.csv",
        "raw_rows": raw_counts["receipt"],
        "materialized_rows": 0,
        "next_action": "STOP: dedicated financial/receipt task line required",
        "risk": "stop_domain",
        "write_allowed_now": "no",
        "reason": "receipt lane is a financial/cashflow stop domain",
    },
]

write_csv(
    OUTPUT_CSV,
    ["lane", "source", "raw_rows", "materialized_rows", "next_action", "risk", "write_allowed_now", "reason"],
    lanes,
)

payload = {
    "status": "PASS",
    "mode": "full_migration_scope_freeze_no_db",
    "raw_counts": raw_counts,
    "current_materialized": {
        "project_created": project_created,
        "partner_created": partner_created,
        "contract_created": contract_created,
        "contract_post_write_review_status": artifacts["contract_12_post_review"].get("status"),
    },
    "lanes_csv": str(OUTPUT_CSV),
    "lanes": lanes,
    "decision": "full migration opened as controlled batch chain; no monolithic write",
    "next_safe_batch": "project_expand bounded create-only dry-run",
    "stop_lanes": ["payment", "receipt", "project_member if it implies permissions"],
}
write_json(OUTPUT_JSON, payload)
print(
    "FULL_MIGRATION_SCOPE_FREEZE="
    + json.dumps(
        {
            "status": payload["status"],
            "next_safe_batch": payload["next_safe_batch"],
            "project_created": project_created,
            "partner_created": partner_created,
            "contract_created": contract_created,
            "stop_lanes": payload["stop_lanes"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
