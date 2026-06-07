# -*- coding: utf-8 -*-
"""Backfill accepted formal-list ordering anchors.

Run with:
    odoo shell -d sc_demo -c /path/to/odoo.conf --no-http < scripts/migration/direct_acceptance_formal_list_rank_backfill_write.py
"""

from __future__ import annotations

import json
import os
from collections import defaultdict, deque
from pathlib import Path


SOURCE_SYSTEM = "online_old_scbsly"


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "direct_acceptance_formal_list_rank_backfill_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_rank_backfill": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def text(value) -> str:
    cleaned = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if cleaned.lower() in {"false", "none", "null"} else cleaned


def visible_values(record, count: int) -> tuple[str, ...]:
    return tuple(text(getattr(record, "legacy_visible_%02d" % index, "")) for index in range(1, count + 1))


def sql_update(record, vals: dict) -> None:
    allowed = {key: value for key, value in vals.items() if key in record._fields}
    if not allowed:
        return
    assignments = ", ".join("%s = %%s" % key for key in allowed)
    env.cr.execute(  # noqa: F821
        "UPDATE %s SET %s WHERE id = %%s" % (record._table, assignments),
        list(allowed.values()) + [record.id],
    )
    record.invalidate_recordset(list(allowed))


def ranked_buckets(label: str, field_count: int):
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
    facts = Fact.search(
        [("active", "=", True), ("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label)],
        order="document_date desc, id desc",
    )
    total = len(facts)
    buckets = defaultdict(deque)
    for offset, fact in enumerate(facts):
        buckets[visible_values(fact, field_count)].append(total - offset)
    return facts, buckets


def backfill_by_fingerprint(label: str, model_name: str, domain: list, field_count: int) -> dict:
    Model = env[model_name].sudo().with_context(active_test=False, prefetch_fields=False)  # noqa: F821
    facts, buckets = ranked_buckets(label, field_count)
    updated = missing = 0
    for record in Model.search(domain):
        bucket = buckets.get(visible_values(record, field_count))
        if not bucket:
            missing += 1
            continue
        sql_update(
            record,
            {
                "legacy_acceptance_label": label,
                "legacy_acceptance_sort_id": bucket.popleft(),
            },
        )
        updated += 1
    return {"label": label, "model": model_name, "source_count": len(facts), "updated": updated, "missing": missing}


def backfill_construction_contracts() -> dict:
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo()  # noqa: F821
    Income = env["construction.contract.income"].sudo().with_context(active_test=False, prefetch_fields=False)  # noqa: F821
    facts = Fact.search(
        [("active", "=", True), ("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", "施工合同")],
        order="document_date desc, id desc",
    )
    total = len(facts)
    by_doc = {text(fact.document_no): (fact, total - offset) for offset, fact in enumerate(facts) if text(fact.document_no)}
    updated = missing = 0
    for income in Income.search([("legacy_contract_id", "ilike", "direct_acceptance:construction_contract:%")]):
        document_no = (
            text(income.legacy_document_no)
            or text(income.contract_id.legacy_document_no)
            or text(income.legacy_contract_id).split(":")[-1]
        )
        matched = by_doc.get(document_no)
        if not matched:
            missing += 1
            continue
        fact, rank = matched
        vals = {"legacy_acceptance_label": "施工合同", "legacy_acceptance_sort_id": rank}
        for index in range(1, 21):
            vals["legacy_visible_%02d" % index] = text(getattr(fact, "legacy_visible_%02d" % index, ""))
        vals.update(
            {
                "legacy_visible_document_state": vals["legacy_visible_01"],
                "legacy_visible_document_no": vals["legacy_visible_02"],
                "legacy_visible_counterparty": vals["legacy_visible_03"],
                "legacy_visible_contractor": vals["legacy_visible_04"],
                "legacy_visible_project_name": vals["legacy_visible_05"],
                "legacy_visible_title": vals["legacy_visible_06"],
                "legacy_visible_amount": vals["legacy_visible_07"],
                "legacy_visible_invoice_amount": vals["legacy_visible_08"],
                "legacy_visible_received_amount": vals["legacy_visible_09"],
                "legacy_visible_invoice_unreceived_amount": vals["legacy_visible_10"],
                "legacy_visible_unreceived_amount": vals["legacy_visible_11"],
                "legacy_visible_unreceived_rate": vals["legacy_visible_12"],
                "legacy_visible_contract_no": vals["legacy_visible_13"],
                "legacy_visible_engineering_address": vals["legacy_visible_15"],
                "legacy_visible_engineering_content": vals["legacy_visible_16"],
                "legacy_visible_contract_duration_days": vals["legacy_visible_17"],
                "legacy_visible_creator_name": vals["legacy_visible_18"],
                "legacy_visible_created_time": vals["legacy_visible_19"] or False,
                "legacy_visible_attachment": vals["legacy_visible_20"],
            }
        )
        income.write(vals)
        updated += 1
    return {"label": "施工合同", "model": "construction.contract.income", "source_count": len(facts), "updated": updated, "missing": missing}


def main() -> dict:
    ensure_allowed_db()
    results = [
        backfill_by_fingerprint(
            "入库",
            "sc.material.inbound",
            [("legacy_fact_model", "=", "online_old_scbsly:direct_acceptance_fact"), ("legacy_fact_type", "=", "direct_acceptance:入库")],
            22,
        ),
        backfill_by_fingerprint(
            "管理人员工资表",
            "sc.hr.payroll.document",
            [("legacy_source_table", "=", "direct_acceptance:管理人员工资表")],
            14,
        ),
        backfill_by_fingerprint(
            "进项上报",
            "sc.invoice.registration",
            [
                ("legacy_source_model", "=", "online_old_scbsly:direct_acceptance:input_tax_report:action932"),
                ("legacy_source_table", "=", "SCBSLY_DIRECT_INPUT_TAX_REPORT"),
            ],
            18,
        ),
        backfill_by_fingerprint(
            "总包进项上报",
            "sc.invoice.registration",
            [
                ("legacy_source_model", "=", "online_old_scbsly:direct_acceptance:general_contract_input_tax_report:action933"),
                ("legacy_source_table", "=", "SCBSLY_DIRECT_GENERAL_CONTRACT_INPUT_TAX_REPORT"),
            ],
            18,
        ),
        backfill_construction_contracts(),
    ]
    payload = {"db": env.cr.dbname, "results": results}  # noqa: F821
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    env.cr.commit()  # noqa: F821
    return payload


result = main()
print("DIRECT_ACCEPTANCE_FORMAL_LIST_RANK_BACKFILL=" + json.dumps(result, ensure_ascii=False))
