# -*- coding: utf-8 -*-
"""Backfill SCBSLY payment request lines and settlement links.

Run through ``odoo shell``.  The source rows come from the online SCBSLY
``C_ZFSQGL_CB`` relation list dumped by the investigation probe.
"""

from __future__ import annotations

import gzip
import json
import os
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


SOURCE_TABLE = "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED"
SOURCE_SYSTEM = "online_old_scbsly"
LINE_BATCH = "scbsly_payment_settlement_relation_backfill_v1"
DEFAULT_INPUT = Path("artifacts/migration/scbsly_online_payment_request_line_relation_rows_v1.json.gz")
OUTPUT_JSON = Path("artifacts/migration/scbsly_payment_settlement_relation_backfill_write_result_v1.json")
SETTLEMENT_LINE_TYPES = {"材料结算单", "劳务结算单", "机械结算单", "分包结算单", "租赁结算单", "结算"}


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value) -> str:
    text = str(value or "").replace("\u3000", " ").strip()
    return "" if text.lower() in {"false", "none", "null"} else re.sub(r"\s+", " ", text)


def money(value) -> float:
    try:
        return float(Decimal(clean(value) or "0"))
    except (InvalidOperation, ValueError):
        return 0.0


def source_path() -> Path:
    path = Path(os.getenv("SCBSLY_PAYMENT_RELATION_ROWS", str(DEFAULT_INPUT)))
    if not path.exists():
        raise RuntimeError({"missing_scbsly_payment_relation_rows": str(path)})
    return path


def write_json(path: Path, payload: dict) -> Path:
    target = path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        target = Path("/tmp") / path.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise RuntimeError({"invalid_relation_rows_payload": str(path)})
    return rows


def request_map():
    rows = env["payment.request"].sudo().with_context(active_test=False).search_read(  # noqa: F821
        [("legacy_source_table", "=", SOURCE_TABLE), ("legacy_record_id", "!=", False)],
        ["legacy_record_id", "settlement_id"],
    )
    return {
        clean(row["legacy_record_id"]): {
            "id": int(row["id"]),
            "settlement_id": row["settlement_id"][0] if row.get("settlement_id") else False,
        }
        for row in rows
    }


def settlement_map():
    env.cr.execute(  # noqa: F821
        """
        SELECT f.legacy_record_id, so.id
          FROM sc_legacy_direct_acceptance_fact f
          JOIN sc_settlement_order so
            ON so.legacy_fact_model = 'sc.legacy.direct.acceptance.fact'
           AND so.legacy_fact_id = f.id
         WHERE f.source_system = %s
        """,
        (SOURCE_SYSTEM,),
    )
    return {clean(document_no): int(settlement_id) for document_no, settlement_id in env.cr.fetchall()}  # noqa: F821


def existing_lines():
    rows = env["payment.request.line"].sudo().with_context(active_test=False).search_read(  # noqa: F821
        [("import_batch", "=", LINE_BATCH)],
        ["legacy_line_id"],
    )
    return {clean(row["legacy_line_id"]): int(row["id"]) for row in rows}


def line_amount(row: dict) -> float:
    for key in ("line_amount", "line_current_pay"):
        amount = money(row.get(key))
        if amount:
            return amount
    return 0.0


def build_relation_rows(rows: list[dict], requests: dict, settlements: dict):
    result = []
    skipped = Counter()
    for row in rows:
        line_id = clean(row.get("line_id"))
        payment_no = clean(row.get("payment_no"))
        if not line_id:
            skipped["missing_line_id"] += 1
            continue
        request = requests.get(payment_no)
        if not request:
            skipped["missing_payment_request"] += 1
            continue
        document_no = clean(row.get("line_document_no"))
        line_type = clean(row.get("line_type"))
        settlement_id = settlements.get(document_no) if line_type in SETTLEMENT_LINE_TYPES else False
        result.append(
            {
                "source": row,
                "legacy_line_id": "scbsly:%s" % line_id,
                "request_id": request["id"],
                "source_document_no": document_no or False,
                "source_line_type": line_type or False,
                "source_counterparty_text": clean(row.get("line_supplier_name")) or clean(row.get("payment_supplier_name")) or False,
                "legacy_parent_id": payment_no,
                "legacy_supplier_contract_id": clean(row.get("line_business_id")) or False,
                "amount": line_amount(row),
                "paid_before_amount": money(row.get("line_paid_before")),
                "remaining_amount": money(row.get("line_remaining")),
                "current_pay_amount": money(row.get("line_current_pay")),
                "settlement_id": settlement_id,
                "note": (
                    "[migration:scbsly_payment_relation] "
                    "source_table=C_ZFSQGL_CB; "
                    "legacy_line_id=%s; legacy_payment_no=%s; legacy_business_id=%s"
                    % (line_id, payment_no, clean(row.get("line_business_id")))
                ),
                "import_batch": LINE_BATCH,
            }
        )
    return result, skipped


def write_lines(relations: list[dict]) -> dict:
    Line = env["payment.request.line"].sudo().with_context(active_test=False)  # noqa: F821
    existing = existing_lines()
    created = updated = 0
    for relation in relations:
        vals = {
            "request_id": relation["request_id"],
            "legacy_line_id": relation["legacy_line_id"],
            "legacy_parent_id": relation["legacy_parent_id"],
            "legacy_supplier_contract_id": relation["legacy_supplier_contract_id"],
            "source_document_no": relation["source_document_no"],
            "source_line_type": relation["source_line_type"],
            "source_counterparty_text": relation["source_counterparty_text"],
            "amount": relation["amount"],
            "paid_before_amount": relation["paid_before_amount"],
            "remaining_amount": relation["remaining_amount"],
            "current_pay_amount": relation["current_pay_amount"],
            "settlement_id": relation["settlement_id"] or False,
            "note": relation["note"],
            "import_batch": relation["import_batch"],
        }
        line_id = existing.get(relation["legacy_line_id"])
        if line_id:
            Line.browse(line_id).write(vals)
            updated += 1
        else:
            Line.create(vals)
            created += 1
    return {"created_lines": created, "updated_lines": updated}


def single_request_pairs(relations: list[dict]) -> tuple[list[tuple[int, int]], dict]:
    by_request = defaultdict(set)
    for relation in relations:
        if relation["settlement_id"]:
            by_request[relation["request_id"]].add(relation["settlement_id"])
    single = [(request_id, next(iter(settlement_ids))) for request_id, settlement_ids in by_request.items() if len(settlement_ids) == 1]
    multi_count = sum(1 for settlement_ids in by_request.values() if len(settlement_ids) > 1)
    if not single:
        return [], {"candidate_single_requests": 0, "multi_settlement_requests": multi_count, "context_safe_requests": 0}

    values = ",".join("(%s,%s)" % pair for pair in single)
    env.cr.execute(  # noqa: F821
        """
        WITH pairs(payment_id, settlement_id) AS (VALUES %s)
        SELECT p.payment_id, p.settlement_id, pr.settlement_id
          FROM pairs p
          JOIN payment_request pr ON pr.id = p.payment_id
          JOIN sc_settlement_order so ON so.id = p.settlement_id
         WHERE pr.project_id IS NOT DISTINCT FROM so.project_id
           AND (so.partner_id IS NULL OR pr.partner_id IS NULL OR pr.partner_id = so.partner_id)
           AND (so.contract_id IS NULL OR pr.contract_id IS NULL OR pr.contract_id = so.contract_id)
           AND so.settlement_type = 'out'
           AND pr.type = 'pay'
        """
        % values
    )
    safe_rows = env.cr.fetchall()  # noqa: F821
    safe = {(int(request_id), int(settlement_id)) for request_id, settlement_id, _current in safe_rows}
    already_linked = len([1 for request_id, settlement_id in single if (request_id, settlement_id) in safe])
    return single, {
        "candidate_single_requests": len(single),
        "multi_settlement_requests": multi_count,
        "context_safe_requests": len(safe),
        "context_safe_or_already_linked_requests": already_linked,
        "context_blocked_single_requests": len(single) - len(safe),
    }


def write_request_settlement_links(pairs: list[tuple[int, int]]) -> int:
    if not pairs:
        return 0
    values = ",".join("(%s,%s)" % pair for pair in pairs)
    env.cr.execute(  # noqa: F821
        """
        WITH pairs(payment_id, settlement_id) AS (VALUES %s)
        UPDATE payment_request pr
           SET settlement_id = p.settlement_id,
               write_date = NOW()
          FROM pairs p
         WHERE pr.id = p.payment_id
           AND pr.settlement_id IS NULL
        """
        % values
    )
    return env.cr.rowcount  # noqa: F821


def main() -> None:
    ensure_allowed_db()
    rows = load_rows(source_path())
    requests = request_map()
    settlements = settlement_map()
    relations, skipped = build_relation_rows(rows, requests, settlements)
    line_result = write_lines(relations)
    single_pairs, request_link_stats = single_request_pairs(relations)
    linked_requests = write_request_settlement_links(single_pairs)
    env.cr.commit()  # noqa: F821

    result = {
        "status": "PASS",
        "mode": "scbsly_payment_settlement_relation_backfill_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_rows": len(rows),
        "imported_payment_requests": len(requests),
        "imported_settlements": len(settlements),
        "relation_lines": len(relations),
        "relation_lines_with_settlement": sum(1 for item in relations if item["settlement_id"]),
        "line_type_counts": dict(Counter(clean(item["source"].get("line_type")) for item in relations)),
        "skipped": dict(skipped),
        **line_result,
        **request_link_stats,
        "linked_request_settlement_id": linked_requests,
        "decision": "full old C_ZFSQGL_CB relation is stored on payment.request.line; payment.request.settlement_id is filled for every single-settlement request because the old relation line is authoritative",
    }
    output = write_json(OUTPUT_JSON, result)
    result["output_json"] = str(output)
    print("SCBSLY_PAYMENT_SETTLEMENT_RELATION_BACKFILL=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
