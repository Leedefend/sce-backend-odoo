# -*- coding: utf-8 -*-
"""Create placeholder settlement orders for SCBSLY payment relation gaps.

This script is intentionally narrow: it only handles payment request lines from
``scbsly_payment_settlement_relation_backfill_v1`` whose old-system relation type
is a settlement document but no imported settlement entity exists yet.
"""

from __future__ import annotations

import json
import os
import zlib
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


LINE_BATCH = "scbsly_payment_settlement_relation_backfill_v1"
PLACEHOLDER_FACT_MODEL = "scbsly.payment.settlement.placeholder"
OUTPUT_JSON = Path("artifacts/migration/scbsly_missing_payment_settlement_placeholder_backfill_result_v1.json")
SETTLEMENT_LINE_TYPES = {"材料结算单", "劳务结算单", "机械结算单", "分包结算单", "租赁结算单", "结算"}


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict) -> Path:
    target = path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        target = Path("/tmp") / path.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def placeholder_fact_id(document_no: str) -> int:
    return int(zlib.crc32(document_no.encode("utf-8")) & 0x7FFFFFFF)


def money(value) -> Decimal:
    return Decimal(str(value or "0"))


def candidate_rows() -> list[dict]:
    Line = env["payment.request.line"].sudo().with_context(active_test=False)  # noqa: F821
    rows = Line.search(
        [
            ("import_batch", "=", LINE_BATCH),
            ("settlement_id", "=", False),
            ("source_document_no", "!=", False),
            ("source_line_type", "in", sorted(SETTLEMENT_LINE_TYPES)),
            ("request_id.legacy_source_table", "=", "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED"),
        ],
        order="source_line_type, source_document_no, id",
    )
    return [
        {
            "line": line,
            "document_no": (line.source_document_no or "").strip(),
            "line_type": (line.source_line_type or "").strip(),
            "project": line.request_id.project_id,
            "partner": line.request_id.partner_id,
            "counterparty": line.source_counterparty_text or line.request_id.legacy_visible_actual_payee_unit or "",
            "current_pay_amount": money(line.current_pay_amount),
            "request_amount": money(line.request_id.amount),
        }
        for line in rows
        if (line.source_document_no or "").strip() and line.request_id.project_id
    ]


def grouped_candidates(rows: list[dict]) -> dict[tuple, list[dict]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["document_no"], row["line_type"], row["project"].id, row["partner"].id if row["partner"] else False)].append(row)
    return grouped


def existing_settlement(document_no: str, fact_id: int):
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False)  # noqa: F821
    settlement = Settlement.search(
        [
            ("legacy_fact_model", "=", PLACEHOLDER_FACT_MODEL),
            ("legacy_fact_id", "=", fact_id),
        ],
        limit=1,
    )
    if settlement:
        return settlement
    return Settlement.search([("name", "=", document_no)], limit=1)


def create_or_update_placeholder(document_no: str, line_type: str, rows: list[dict]):
    fact_id = placeholder_fact_id(document_no)
    settlement = existing_settlement(document_no, fact_id)
    project = rows[0]["project"]
    partner = rows[0]["partner"]
    currency = project.company_id.currency_id or env.company.currency_id  # noqa: F821
    line_current_total = sum((row["current_pay_amount"] for row in rows), Decimal("0"))
    fallback_request_amount = max((row["request_amount"] for row in rows), default=Decimal("0"))
    amount = line_current_total if line_current_total > 0 else fallback_request_amount
    counterparty = rows[0]["counterparty"] or (partner.display_name if partner else "")
    vals = {
        "name": document_no,
        "project_id": project.id,
        "partner_id": partner.id if partner else False,
        "settlement_unit_id": partner.id if partner else False,
        "legacy_counterparty_name": counterparty,
        "title": "%s历史占位" % line_type,
        "settlement_type": "out",
        "business_category_id": env["sc.business.category"].sudo().search(  # noqa: F821
            [("code", "=", "settlement.expense"), ("target_model", "=", "sc.settlement.order")],
            limit=1,
        ).id,
        "legacy_settlement_category": line_type,
        "legacy_document_state": "历史占位",
        "legacy_payment_request_state": "已关联付款申请",
        "legacy_fact_model": PLACEHOLDER_FACT_MODEL,
        "legacy_fact_id": fact_id,
        "legacy_fact_type": line_type,
        "currency_id": currency.id,
        "company_id": project.company_id.id or env.company.id,  # noqa: F821
        "state": "approve",
        "note": (
            "[migration:scbsly_missing_payment_settlement_placeholder] "
            "旧系统付款关系中存在%s %s，但当前库未导入对应结算实体；"
            "本记录用于恢复历史付款申请办理链路，后续可用完整结算导入替换。"
        )
        % (line_type, document_no),
    }
    Settlement = env["sc.settlement.order"].sudo().with_context(active_test=False)  # noqa: F821
    if settlement:
        settlement.write(vals)
        created = False
    else:
        settlement = Settlement.create(vals)
        created = True

    existing_line = settlement.line_ids[:1]
    line_vals = {
        "name": "%s %s" % (line_type, document_no),
        "qty": 1.0,
        "price_unit": float(amount),
    }
    if existing_line:
        existing_line.with_context(legacy_migration_allow_missing_contract=True).write(line_vals)
    else:
        env["sc.settlement.order.line"].sudo().with_context(legacy_migration_allow_missing_contract=True).create(  # noqa: F821
            dict(line_vals, settlement_id=settlement.id)
        )
    return settlement, created, float(amount)


def update_request_main_settlements(requests):
    updated = 0
    Payment = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
    for request in Payment.browse(list(requests)).exists():
        settlements = request.outflow_line_ids.mapped("settlement_id").exists()
        if settlements.filtered(lambda settlement: settlement.legacy_fact_model == PLACEHOLDER_FACT_MODEL):
            continue
        if not request.settlement_id and len(settlements) == 1:
            request.write({"settlement_id": settlements.id})
            updated += 1
    return updated


def main() -> None:
    ensure_allowed_db()
    rows = candidate_rows()
    grouped = grouped_candidates(rows)
    created = updated = linked_lines = 0
    touched_requests = set()
    samples = []
    for (document_no, line_type, _project_id, _partner_id), group_rows in grouped.items():
        settlement, was_created, amount = create_or_update_placeholder(document_no, line_type, group_rows)
        if was_created:
            created += 1
        else:
            updated += 1
        lines = env["payment.request.line"].sudo().browse([row["line"].id for row in group_rows])  # noqa: F821
        lines.write({"settlement_id": settlement.id})
        linked_lines += len(lines)
        touched_requests.update(lines.mapped("request_id").ids)
        if len(samples) < 20:
            samples.append(
                {
                    "document_no": document_no,
                    "line_type": line_type,
                    "settlement_id": settlement.id,
                    "amount": amount,
                    "line_count": len(lines),
                }
            )
    main_links = update_request_main_settlements(touched_requests)
    payload = {
        "status": "PASS",
        "candidate_lines": len(rows),
        "candidate_documents": len(grouped),
        "created_settlements": created,
        "updated_settlements": updated,
        "linked_lines": linked_lines,
        "updated_main_payment_requests": main_links,
        "samples": samples,
    }
    output = write_json(OUTPUT_JSON, payload)
    env.cr.commit()  # noqa: F821
    print(json.dumps(dict(payload, output=str(output)), ensure_ascii=False, indent=2, sort_keys=True))


main()
