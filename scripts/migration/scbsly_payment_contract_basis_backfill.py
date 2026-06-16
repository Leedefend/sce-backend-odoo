# -*- coding: utf-8 -*-
"""Backfill contract basis for SCBSLY payment requests.

Only updates legacy payment requests that still have no settlement/material
settlement/contract basis, and only when old-system relation lines point to
exactly one imported contract with matching project, partner, and direction.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


LINE_BATCH = "scbsly_payment_settlement_relation_backfill_v1"
SOURCE_TABLE = "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED"
OUTPUT_JSON = Path("artifacts/migration/scbsly_payment_contract_basis_backfill_result_v1.json")
CONTRACT_LINE_TYPES = {"供货合同", "合同", "租赁合同", "劳务合同", "机械合同", "分包合同"}


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


def contract_by_document():
    Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
    mapping = {}
    duplicates = set()
    for contract in Contract.search([]):
        keys = {
            (contract.legacy_document_no or "").strip(),
            (contract.legacy_contract_no or "").strip(),
            (contract.name or "").strip(),
        }
        for key in keys:
            if not key:
                continue
            if key in mapping and mapping[key].id != contract.id:
                duplicates.add(key)
                continue
            mapping[key] = contract
    for key in duplicates:
        mapping.pop(key, None)
    return mapping, duplicates


def candidate_requests():
    return env["payment.request"].sudo().with_context(active_test=False).search(  # noqa: F821
        [
            ("legacy_source_table", "=", SOURCE_TABLE),
            ("settlement_id", "=", False),
            ("material_settlement_id", "=", False),
            ("contract_id", "=", False),
            ("line_settlement_count", "=", 0),
        ]
    )


def expected_contract_type(request):
    return "in" if request.type == "pay" else "out"


def context_matches(request, contract) -> bool:
    if request.project_id and contract.project_id and request.project_id != contract.project_id:
        return False
    if request.partner_id and contract.partner_id and request.partner_id != contract.partner_id:
        return False
    return contract.type == expected_contract_type(request)


def main() -> None:
    ensure_allowed_db()
    mapping, duplicate_keys = contract_by_document()
    stats = {
        "candidate_requests": 0,
        "requests_with_contract_relation": 0,
        "requests_with_matched_contract": 0,
        "updated_requests": 0,
        "skipped_no_contract_relation": 0,
        "skipped_no_contract_match": 0,
        "skipped_multi_contract": 0,
        "skipped_context_mismatch": 0,
        "duplicate_contract_keys_ignored": len(duplicate_keys),
    }
    samples = []
    for request in candidate_requests():
        stats["candidate_requests"] += 1
        relation_lines = request.outflow_line_ids.filtered(
            lambda line: line.import_batch == LINE_BATCH
            and (line.source_line_type or "").strip() in CONTRACT_LINE_TYPES
            and (line.source_document_no or "").strip()
        )
        if not relation_lines:
            stats["skipped_no_contract_relation"] += 1
            continue
        stats["requests_with_contract_relation"] += 1
        contracts = env["construction.contract"].sudo().browse()  # noqa: F821
        for line in relation_lines:
            contract = mapping.get((line.source_document_no or "").strip())
            if contract:
                contracts |= contract
        contracts = contracts.exists()
        if not contracts:
            stats["skipped_no_contract_match"] += 1
            continue
        stats["requests_with_matched_contract"] += 1
        if len(contracts) != 1:
            stats["skipped_multi_contract"] += 1
            continue
        contract = contracts[:1]
        if not context_matches(request, contract):
            stats["skipped_context_mismatch"] += 1
            continue
        request.write({"contract_id": contract.id})
        stats["updated_requests"] += 1
        if len(samples) < 20:
            samples.append(
                {
                    "request_id": request.id,
                    "request_no": request.name,
                    "contract_id": contract.id,
                    "contract_no": contract.legacy_document_no or contract.legacy_contract_no or contract.name,
                }
            )
    payload = dict(stats, status="PASS", samples=samples)
    output = write_json(OUTPUT_JSON, payload)
    env.cr.commit()  # noqa: F821
    print(json.dumps(dict(payload, output=str(output)), ensure_ascii=False, indent=2, sort_keys=True))


main()
