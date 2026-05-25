#!/usr/bin/env python3
"""Backfill full payment-request facts from legacy C_ZFSQGL.

Approval state is preserved as metadata; it is not a fact filter. A payment
request fact is included when it is not deleted, has legacy project and
counterparty identifiers, and has a positive amount in request/payment fields.
Missing anchors are created explicitly so valid facts are not silently dropped.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


AMOUNT_FIELDS = ("f_JHJE", "f_JHFKJE", "f_NEW_JHJE", "f_SFJE", "ZSJE", "YJJE", "LJFK")
EXPECTED_FACT_ROWS = 13390
SOURCE_TABLE = "C_ZFSQGL"


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "tmp/raw/payment/payment.csv").exists():
            return candidate
    return Path.cwd()


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())


def resolve_artifact_root(root: Path) -> Path:
    env_root = clean(os.getenv("MIGRATION_ARTIFACT_ROOT"))
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([root / "artifacts/migration", Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    raise RuntimeError({"artifact_root_not_writable": [str(item) for item in candidates]})


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in AMOUNT_FIELDS:
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("DEL")) == "1" or bool(clean(row.get("SCRID")) or clean(row.get("SCR")) or clean(row.get("SCRQ")))


def parse_date(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def parse_datetime(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return ""


def read_source(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_fact_row(row: dict[str, str]) -> bool:
    if is_deleted(row):
        return False
    if not clean(row.get("Id")):
        return False
    if not clean(row.get("f_XMID")) or not clean(row.get("f_GYSID")):
        return False
    return best_amount(row)[1] > 0


def resolve_project(row: dict[str, str]):
    legacy_project_id = clean(row.get("f_XMID"))
    project = Project.search(  # noqa: F821
        ["|", ("legacy_project_id", "=", legacy_project_id), ("legacy_parent_id", "=", legacy_project_id)],
        limit=1,
    )
    if project:
        return project, False
    vals = {
        "name": clean(row.get("f_XMMC")) or legacy_project_id,
        "legacy_project_id": legacy_project_id,
        "short_name": clean(row.get("f_XMMC")) or False,
        "project_environment": "legacy_payment_request_fact_anchor",
        "legacy_state": "fact_anchor_for_C_ZFSQGL",
        "legacy_note": "历史付款申请事实补锚; source=C_ZFSQGL",
    }
    return Project.create(vals), True  # noqa: F821


def resolve_partner(row: dict[str, str]):
    legacy_partner_id = clean(row.get("f_GYSID"))
    partner = Partner.search([("legacy_partner_id", "=", legacy_partner_id)], limit=1)  # noqa: F821
    if partner:
        return partner, False
    partner_name = clean(row.get("f_GYSMC")) or legacy_partner_id
    vals = {
        "name": partner_name,
        "company_type": "company",
        "is_company": True,
        "supplier_rank": 1,
        "legacy_partner_id": legacy_partner_id,
        "legacy_partner_source": "payment_request_counterparty",
        "legacy_partner_name": partner_name,
        "legacy_source_evidence": "历史付款申请事实补锚; source=C_ZFSQGL.f_GYSID",
    }
    return Partner.create(vals), True  # noqa: F821


def request_note(row: dict[str, str], amount_source: str) -> str:
    return (
        "[migration:outflow_request_fact_coverage] "
        f"legacy_outflow_id={clean(row.get('Id'))}; "
        f"legacy_project_id={clean(row.get('f_XMID'))}; "
        f"legacy_partner_id={clean(row.get('f_GYSID'))}; "
        f"legacy_contract_id={clean(row.get('f_GYSHTID'))}; "
        f"amount_source={amount_source}; "
        f"document_no={clean(row.get('DJBH'))}; "
        f"legacy_document_state={clean(row.get('DJZT'))}"
    )


REPO_ROOT = repo_root()
ARTIFACT_ROOT = resolve_artifact_root(REPO_ROOT)
SOURCE_CSV = REPO_ROOT / "tmp/raw/payment/payment.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_outflow_request_fact_coverage_write_result_v1.json"

ensure_allowed_db()

Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821

source_rows = read_source(SOURCE_CSV)
fact_rows = [row for row in source_rows if is_fact_row(row)]
if len(fact_rows) != EXPECTED_FACT_ROWS:
    raise RuntimeError({"payment_request_fact_count_drifted": len(fact_rows), "expected": EXPECTED_FACT_ROWS})

legacy_ids = [clean(row.get("Id")) for row in fact_rows]
existing = Request.search_read(
    [("legacy_source_table", "=", SOURCE_TABLE), ("legacy_record_id", "in", legacy_ids)],
    ["legacy_record_id", "legacy_document_state"],
)
existing_ids = {clean(row.get("legacy_record_id")) for row in existing}
existing_state_by_id = {
    clean(row.get("legacy_record_id")): clean(row.get("legacy_document_state"))
    for row in existing
    if clean(row.get("legacy_record_id"))
}

created_requests = 0
skipped_existing = 0
updated_existing = 0
created_project_anchors = 0
created_partner_anchors = 0
amount_source_counts: dict[str, int] = {}
batch: list[dict[str, object]] = []

for row in fact_rows:
    legacy_id = clean(row.get("Id"))
    amount_source, amount = best_amount(row)
    amount_source_counts[amount_source] = amount_source_counts.get(amount_source, 0) + 1
    if legacy_id in existing_ids:
        vals: dict[str, object] = {}
        document_state = clean(row.get("DJZT"))
        if "legacy_document_state" in Request._fields and existing_state_by_id.get(legacy_id) != document_state:
            vals["legacy_document_state"] = document_state or False
        if vals:
            request = Request.search([("legacy_source_table", "=", SOURCE_TABLE), ("legacy_record_id", "=", legacy_id)], limit=1)
            request.write(vals)
            updated_existing += 1
        skipped_existing += 1
        continue

    project, project_created = resolve_project(row)
    partner, partner_created = resolve_partner(row)
    created_project_anchors += int(project_created)
    created_partner_anchors += int(partner_created)
    vals = {
        "type": "pay",
        "project_id": project.id,
        "partner_id": partner.id,
        "amount": money(amount),
        "note": request_note(row, amount_source),
        "legacy_source_table": SOURCE_TABLE,
        "legacy_record_id": legacy_id,
    }
    if parse_date(row.get("f_SQRQ")):
        vals["date_request"] = parse_date(row.get("f_SQRQ"))
    if clean(row.get("LRRID")):
        vals["creator_legacy_user_id"] = clean(row.get("LRRID"))
    if clean(row.get("f_LRR")):
        vals["creator_name"] = clean(row.get("f_LRR"))
    if parse_datetime(row.get("f_LRSJ")):
        vals["created_time"] = parse_datetime(row.get("f_LRSJ"))
    if "legacy_document_state" in Request._fields and clean(row.get("DJZT")):
        vals["legacy_document_state"] = clean(row.get("DJZT"))
    batch.append(vals)
    existing_ids.add(legacy_id)

    if len(batch) >= 500:
        Request.create(batch)
        created_requests += len(batch)
        batch = []

if batch:
    Request.create(batch)
    created_requests += len(batch)

env.cr.commit()  # noqa: F821

final_count = Request.search_count([("legacy_source_table", "=", SOURCE_TABLE), ("legacy_record_id", "in", legacy_ids)])
status = "PASS" if final_count == EXPECTED_FACT_ROWS else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_outflow_request_fact_coverage_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_rows": len(source_rows),
    "expected_fact_rows": EXPECTED_FACT_ROWS,
    "final_fact_rows": final_count,
    "created_requests": created_requests,
    "skipped_existing": skipped_existing,
    "updated_existing": updated_existing,
    "created_project_anchors": created_project_anchors,
    "created_partner_anchors": created_partner_anchors,
    "amount_source_counts": dict(sorted(amount_source_counts.items())),
    "boundary": {
        "source_table": SOURCE_TABLE,
        "approval_state_is_fact_filter": False,
        "deleted_rows_excluded": True,
        "project_anchor_policy": "create_fact_anchor_when_missing",
        "partner_anchor_policy": "create_payment_request_counterparty_anchor_when_missing",
    },
    "decision": "outflow_request_fact_coverage_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_OUTFLOW_REQUEST_FACT_COVERAGE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
