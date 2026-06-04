# -*- coding: utf-8 -*-
"""Project accepted joint construction contracts already in Odoo into income execution."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


DIRECT_PREFIX = "direct_acceptance:construction_contract:"
OLD_BUSINESS_ACTION_ID = 855
OLD_BUSINESS_VISIBLE_FIELD_MAP = {
    "p1_visible_06fa8c6f628f": "legacy_visible_document_state",
    "p1_visible_8fa8662ad38f": "legacy_visible_document_no",
    "p1_visible_2585b4ab16bd": "legacy_visible_contract_date",
    "p1_visible_202b429f79ca": "legacy_visible_archived",
    "p1_visible_fadf1135d6a4": "legacy_visible_counterparty",
    "p1_visible_3e7255522b33": "legacy_visible_project_name",
    "p1_visible_3ec01dd569e2": "legacy_visible_title",
    "p1_visible_0965a7d1e74c": "legacy_visible_category",
    "p1_visible_17b341733b7b": "legacy_visible_contract_no",
    "p1_visible_75e856a13c7c": "legacy_visible_amount",
    "p1_visible_58a2eb3301c1": "legacy_visible_settlement_amount",
    "p1_visible_affba7961481": "legacy_visible_invoice_amount",
    "p1_visible_da9d3c637407": "legacy_visible_received_amount",
    "p1_visible_75b438b16f10": "legacy_visible_unreceived_amount",
    "p1_visible_bf0c9e684289": "legacy_visible_unreceived_rate",
    "p1_visible_5839c15a34a4": "legacy_visible_affiliated_person",
    "p1_visible_0cf26c325f34": "legacy_visible_engineering_address",
    "p1_visible_7b9f4bb3e3ea": "legacy_visible_engineering_content",
    "p1_visible_ee6a4d9e2956": "legacy_visible_creator_name",
    "p1_visible_dfc25d77dc39": "legacy_visible_created_time",
    "p1_visible_99f6fe6c41ad": "legacy_visible_attachment",
}


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "joint_acceptance_contract_income_execution_write_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def acceptance_domain() -> list[tuple]:
    return [
        ("legacy_contract_id", "!=", False),
        ("legacy_contract_id", "not ilike", DIRECT_PREFIX + "%"),
        ("legacy_income_surface_visible", "=", True),
    ]


def text(value) -> str:
    cleaned = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if cleaned in {"False", "false", "None", "none"}:
        return ""
    return cleaned


def parse_date(value):
    raw = text(value).replace("/", "-")
    return raw[:10] or False


def parse_datetime(value):
    raw = text(value).replace("T", " ").replace("/", "-")
    if not raw:
        return False
    raw = re.sub(r"\.\d+$", "", raw)
    return raw[:19]


def old_business_visible_values(contract) -> dict:
    vals = {}
    for source_field, target_field in OLD_BUSINESS_VISIBLE_FIELD_MAP.items():
        value = text(getattr(contract, source_field, ""))
        if target_field == "legacy_visible_contract_date":
            vals[target_field] = parse_date(value) or False
        elif target_field == "legacy_visible_created_time":
            vals[target_field] = parse_datetime(value) or False
        else:
            vals[target_field] = value or False
    return vals


def ensure_old_business_action_domain() -> str:
    action = env["ir.actions.act_window"].sudo().browse(OLD_BUSINESS_ACTION_ID)  # noqa: F821
    if action.exists():
        action.write({"domain": repr(acceptance_domain())})
        return action.domain
    return ""


def main() -> None:
    ensure_allowed_db()
    Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
    Income = env["construction.contract.income"].sudo()  # noqa: F821
    action_domain = ensure_old_business_action_domain()
    domain = acceptance_domain() + [("type", "=", "out")]
    contracts = Contract.search(domain, order="legacy_document_no,id")
    created = 0
    existing = 0
    hidden_direct_count = 0
    samples = []
    for contract in contracts:
        contract.write(old_business_visible_values(contract))
        income = Income.search([("contract_id", "=", contract.id)], limit=1)
        if income:
            existing += 1
            action = "existing"
        else:
            income = Income.create({"contract_id": contract.id})
            created += 1
            action = "created"
        if contract.legacy_contract_id.startswith(DIRECT_PREFIX):
            hidden_direct_count += 1
        if len(samples) < 20:
            samples.append(
                {
                    "action": action,
                    "contract_id": contract.id,
                    "income_id": income.id,
                    "legacy_contract_id": contract.legacy_contract_id,
                    "legacy_document_no": contract.legacy_document_no,
                    "subject": contract.subject,
                }
            )
    env.cr.commit()  # noqa: F821
    income_count = Income.search_count([("contract_id", "in", contracts.ids)])
    result = {
        "status": "PASS" if income_count == len(contracts) and hidden_direct_count == 0 else "FAIL",
        "mode": "joint_acceptance_contract_income_execution_write",
        "db": env.cr.dbname,  # noqa: F821
        "source_model": "construction.contract",
        "source_action_id": OLD_BUSINESS_ACTION_ID,
        "source_action_domain": action_domain,
        "source_contract_count": len(contracts),
        "income_execution_count": income_count,
        "created_income_wrappers": created,
        "existing_income_wrappers": existing,
        "unexpected_direct_source_count": hidden_direct_count,
        "sample": samples,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
