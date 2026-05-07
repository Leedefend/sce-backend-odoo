#!/usr/bin/env python3
"""Generate the business-aligned partner rebuild payload.

The existing rebuild flow already has a payload contract. This adapter keeps
that contract and refreshes the rows from the user's full mixed partner source.
It performs no database writes.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from partner_import_source_audit import (
    build_entity_rows,
    clean,
    identity_for,
    load_source_records,
    looks_personal,
    norm_name,
    norm_tax,
    parse_amount,
    write_csv,
    write_json,
)


DEFAULT_CURRENT_PAYLOAD = (
    "artifacts/migration/fact_based_partner_rebuild_2_fact_only_20260506T2055/"
    "fact_based_partner_rebuild_payload_v1.csv"
)
DEFAULT_CUSTOMER_FACT_CSVS = [
    "artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_legacy_receipt_residual_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv",
    "artifacts/migration/history_receipt_income_partner_targeted_replay_payload_v1.csv",
    "tmp/raw/contract/contract.csv",
    "tmp/raw/receipt/receipt.csv",
]
DEFAULT_SUPPLIER_FACT_CSVS = [
    "artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv",
    "artifacts/migration/history_outflow_partner_targeted_replay_payload_v1.csv",
    "artifacts/migration/history_actual_outflow_partner_targeted_replay_payload_v1.csv",
]
DEFAULT_CUSTOMER_FACT_ONLY_CSVS = [
    "artifacts/migration/legacy_mssql_customer_business_fact_candidates_v1.csv",
]

PAYLOAD_FIELDS = [
    "partner_key",
    "legacy_partner_source",
    "legacy_partner_id",
    "legacy_partner_ids",
    "name",
    "company_type",
    "customer_rank",
    "supplier_rank",
    "sc_supplier_type",
    "sc_region",
    "street",
    "sc_registered_capital",
    "sc_business_scope",
    "sc_default_tax_rate",
    "sc_default_tax_rate_text",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "vat",
    "legacy_credit_code",
    "source_created_by",
    "source_created_at",
    "source_project_name",
    "source_partner_code",
    "source_cooperation_type",
    "source_fact_count",
    "source_fact_source",
    "source_document_state",
    "source_push_result",
    "source_tax_rate",
    "source_receipt_amount",
    "source_payment_amount",
    "source_files",
    "legacy_source_evidence",
    "review_flags",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def current_keys(row: dict[str, str]) -> set[str]:
    keys: set[str] = set()
    vat = norm_tax(row.get("vat") or row.get("legacy_credit_code"))
    name = norm_name(row.get("name"))
    partner_key = clean(row.get("partner_key"))
    legacy_partner_id = clean(row.get("legacy_partner_id"))
    if vat:
        keys.add(f"tax:{vat}")
    if name:
        keys.add(f"name:{name}")
    if partner_key:
        keys.add(partner_key)
    if legacy_partner_id:
        keys.add(legacy_partner_id)
    return keys


CUSTOMER_OR_SUPPLIER_NAME_FIELDS = (
    "name",
    "legacy_partner_name",
    "legacy_counterparty_text",
    "partner_name",
    "counterparty_name",
    "invoice_party_name",
    "invoice_issue_company",
    "WLDWMC",
    "FBF",
    "GCJSDW",
    "f_JSDW",
)
CUSTOMER_OR_SUPPLIER_TAX_FIELDS = (
    "vat",
    "legacy_credit_code",
    "legacy_tax_no",
    "tax_no",
    "credit_code",
    "TYSHXYDM",
    "SH",
    "NSRSBH",
)


def business_fact_keys(row: dict[str, str]) -> set[str]:
    keys: set[str] = set()
    for field in CUSTOMER_OR_SUPPLIER_TAX_FIELDS:
        value = norm_tax(row.get(field))
        if value:
            keys.add(f"tax:{value}")
    for field in CUSTOMER_OR_SUPPLIER_NAME_FIELDS:
        value = norm_name(row.get(field))
        if value:
            keys.add(f"name:{value}")
    return keys


def load_business_fact_index(paths: list[str]) -> tuple[set[str], dict[str, int]]:
    keys: set[str] = set()
    source_counts: Counter[str] = Counter()
    for raw_path in paths:
        path = Path(raw_path)
        rows = read_csv(path)
        if not rows:
            continue
        source_counts[str(path)] = len(rows)
        for row in rows:
            keys.update(business_fact_keys(row))
    return keys, dict(sorted(source_counts.items()))


def load_business_fact_rows(paths: list[str]) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows: list[dict[str, str]] = []
    source_counts: Counter[str] = Counter()
    for raw_path in paths:
        path = Path(raw_path)
        path_rows = read_csv(path)
        if not path_rows:
            continue
        source_counts[str(path)] = len(path_rows)
        rows.extend(path_rows)
    return rows, dict(sorted(source_counts.items()))


def first_value(rows: list[dict[str, str]], field: str) -> str:
    values = [clean(row.get(field)) for row in rows if clean(row.get(field))]
    return Counter(values).most_common(1)[0][0] if values else ""


def join_values(rows: list[dict[str, str]], field: str, limit: int = 50) -> str:
    return ";".join(sorted({clean(row.get(field)) for row in rows if clean(row.get(field))})[:limit])


def supplier_type(rows: list[dict[str, str]]) -> str:
    text = ";".join(
        clean(row.get("cooperation_type") or row.get("main_supply_type") or row.get("category_label"))
        for row in rows
    )
    if "劳务" in text:
        return "labor"
    if "分包" in text:
        return "subcontract"
    if "设备" in text:
        return "equipment"
    if "材料" in text:
        return "material"
    return "other"


def partner_key_for(identity_key: str) -> str:
    if identity_key.startswith("tax:"):
        return "credit:" + identity_key.split(":", 1)[1]
    return identity_key


def first_fact_value(rows: list[dict[str, str]], *fields: str) -> str:
    for field in fields:
        value = first_value(rows, field)
        if value:
            return value
    return ""


def is_valid_bank_account(value: object) -> bool:
    text = re.sub(r"\s+", "", clean(value))
    if not text or text in {"0", "1", ".", "/", "无", "无开户行"}:
        return False
    return bool(re.search(r"\d{6,}", text))


def normalize_tax_rate(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    normalized = text.replace("%", "").replace("％", "").replace(",", "").strip()
    try:
        number = float(normalized)
    except ValueError:
        return ""
    if "%" not in text and "％" not in text and 0 < number < 1:
        number *= 100
    return f"{number:.4f}".rstrip("0").rstrip(".")


def amount_text(amount: float) -> str:
    return f"{amount:.2f}" if amount else ""


def cooperation_type_from_business(role: str, rows: list[dict[str, str]]) -> str:
    receipt_amount = sum(parse_amount(row.get("receipt_amount")) for row in rows)
    payment_amount = sum(parse_amount(row.get("payment_amount")) for row in rows)
    if role == "customer_and_supplier":
        return "客户/供应商"
    if role == "customer":
        return "客户（收款事实）" if receipt_amount else "客户（收款合同/收入事实）"
    if role == "supplier":
        return "供应商（付款事实）" if payment_amount else "供应商（供应商合同/应付事实）"
    return "后台留存"


def entity_match_keys(identity_key: str, entity: dict[str, object]) -> set[str]:
    keys = {identity_key}
    name = norm_name(entity.get("canonical_name"))
    tax_no = norm_tax(entity.get("tax_no"))
    if name:
        keys.add(f"name:{name}")
    if tax_no:
        keys.add(f"tax:{tax_no}")
    return keys


def role_from_business_facts(
    *,
    identity_key: str,
    entity: dict[str, object],
    rows: list[dict[str, str]],
    customer_fact_keys: set[str],
    supplier_fact_keys: set[str],
) -> tuple[str, set[str]]:
    keys = entity_match_keys(identity_key, entity)
    customer_fact = bool(keys & customer_fact_keys) or any(parse_amount(row.get("receipt_amount")) > 0 for row in rows)
    supplier_fact = bool(keys & supplier_fact_keys) or any(parse_amount(row.get("payment_amount")) > 0 for row in rows)
    basis: set[str] = set()
    if customer_fact:
        basis.add("customer_business_fact")
    if supplier_fact:
        basis.add("supplier_business_fact")
    if customer_fact and supplier_fact:
        return "customer_and_supplier", basis
    if customer_fact:
        return "customer", basis
    if supplier_fact:
        return "supplier", basis
    return "background_only", basis


def build_payload_rows(
    source_records: list[dict[str, str]],
    current_rows: list[dict[str, str]],
    customer_fact_keys: set[str],
    supplier_fact_keys: set[str],
    customer_fact_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in source_records:
        grouped[identity_for(record)].append(record)
    entity_by_key = {clean(row["identity_key"]): row for row in build_entity_rows(source_records)}

    current_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in current_rows:
        for key in current_keys(row):
            current_by_key[key].append(row)

    payload_rows: list[dict[str, object]] = []
    matched_current_row_ids: set[int] = set()
    for identity_key, rows in sorted(grouped.items()):
        entity = entity_by_key[identity_key]
        matches = current_by_key.get(identity_key, [])
        if not matches and identity_key.startswith("tax:"):
            matches = current_by_key.get("name:" + norm_name(entity.get("canonical_name")), [])
        if matches:
            matched_current_row_ids.add(id(matches[0]))

        role, role_basis = role_from_business_facts(
            identity_key=identity_key,
            entity=entity,
            rows=rows,
            customer_fact_keys=customer_fact_keys,
            supplier_fact_keys=supplier_fact_keys,
        )
        customer_rank = 1 if role in {"customer", "customer_and_supplier"} else 0
        supplier_rank = 1 if role in {"supplier", "customer_and_supplier"} else 0
        name = norm_name(entity.get("canonical_name"))
        tax_no = norm_tax(entity.get("tax_no"))
        bank_account = first_value(rows, "bank_account")
        tax_rate_text = first_value(rows, "tax_rate")
        review_flags = set()
        if role == "background_only":
            review_flags.add("background_only_no_user_requested_business_fact")
        if not tax_no:
            review_flags.add("missing_credit_code")
        if role == "background_only" and clean(entity.get("personal_fragment")) == "1":
            review_flags.add("personal_fragment_review")
        if bank_account and not is_valid_bank_account(bank_account):
            review_flags.add("invalid_bank_account_review")
        if len(matches) > 1:
            review_flags.add("multiple_current_payload_matches")
        for match in matches[:1]:
            for flag in clean(match.get("review_flags")).split(";"):
                if flag:
                    review_flags.add(flag)

        payload_rows.append(
            {
                "partner_key": partner_key_for(identity_key),
                "legacy_partner_source": "xlsx_business_aligned_partner",
                "legacy_partner_id": identity_key,
                "legacy_partner_ids": "",
                "name": name,
                "company_type": "person" if clean(entity.get("personal_fragment")) == "1" else "company",
                "customer_rank": customer_rank,
                "supplier_rank": supplier_rank,
                "sc_supplier_type": supplier_type(rows),
                "sc_region": first_value(rows, "region"),
                "street": first_value(rows, "address"),
                "sc_registered_capital": first_value(rows, "register_capital"),
                "sc_business_scope": first_value(rows, "business_scope"),
                "sc_default_tax_rate": normalize_tax_rate(tax_rate_text),
                "sc_default_tax_rate_text": tax_rate_text,
                "sc_account_name": first_value(rows, "bank_account_name") or name,
                "sc_bank_name": first_value(rows, "bank_name"),
                "sc_bank_account": bank_account,
                "vat": tax_no,
                "legacy_credit_code": tax_no,
                "source_created_by": first_value(rows, "source_operator"),
                "source_created_at": first_value(rows, "source_time"),
                "source_project_name": join_values(rows, "project_name"),
                "source_partner_code": join_values(rows, "partner_code"),
                "source_cooperation_type": cooperation_type_from_business(role, rows),
                "source_fact_count": str(len(rows)),
                "source_fact_source": join_values(rows, "source_kind"),
                "source_document_state": join_values(rows, "document_state"),
                "source_push_result": join_values(rows, "push_result"),
                "source_tax_rate": first_value(rows, "tax_rate"),
                "source_receipt_amount": amount_text(sum(parse_amount(row.get("receipt_amount")) for row in rows)),
                "source_payment_amount": amount_text(sum(parse_amount(row.get("payment_amount")) for row in rows)),
                "source_files": join_values(rows, "source_file"),
                "legacy_source_evidence": "partner_import_source_business_aligned:" + identity_key,
                "review_flags": ";".join(sorted(review_flags | role_basis)),
            }
        )

    source_identity_keys = set(grouped)
    source_name_keys = {"name:" + norm_name(row.get("canonical_name")) for row in entity_by_key.values()}
    source_tax_keys = {"tax:" + norm_tax(row.get("tax_no")) for row in entity_by_key.values() if norm_tax(row.get("tax_no"))}
    source_keys = source_identity_keys | source_name_keys | source_tax_keys

    fact_grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in customer_fact_rows:
        keys = business_fact_keys(row)
        identity_key = sorted(keys)[0] if keys else ""
        if identity_key:
            fact_grouped[identity_key].append(row)

    for identity_key, rows in sorted(fact_grouped.items()):
        keys = set().union(*(business_fact_keys(row) for row in rows))
        if keys & source_keys:
            continue
        name = norm_name(first_fact_value(rows, "name", "legacy_partner_name", "WLDWMC", "FKDW", "FBF", "GMDW"))
        tax_no = norm_tax(first_fact_value(rows, "vat", "legacy_credit_code", "legacy_tax_no", "tax_no", "credit_code"))
        if not name:
            continue
        raw_legacy_partner_ids = join_values(rows, "legacy_partner_id")
        legacy_partner_id = "customer_fact:" + identity_key
        source_tables = join_values(rows, "source_table")
        source_fields = join_values(rows, "source_field")
        profile_sources = join_values(rows, "profile_source_table")
        evidence = "legacy_mssql_customer_business_fact:" + ";".join(sorted(keys))
        review_flags = {"customer_business_fact"}
        if not tax_no:
            review_flags.add("missing_credit_code")
        payload_rows.append(
            {
                "partner_key": partner_key_for(identity_key),
                "legacy_partner_source": "legacy_mssql_customer_business_fact",
                "legacy_partner_id": legacy_partner_id,
                "legacy_partner_ids": raw_legacy_partner_ids,
                "name": name,
                "company_type": "person" if looks_personal(name, tax_no) else "company",
                "customer_rank": 1,
                "supplier_rank": 0,
                "sc_supplier_type": "",
                "sc_region": first_fact_value(rows, "region"),
                "street": first_fact_value(rows, "address"),
                "sc_registered_capital": first_fact_value(rows, "registered_capital"),
                "sc_business_scope": first_fact_value(rows, "business_scope"),
                "sc_default_tax_rate": "",
                "sc_default_tax_rate_text": "",
                "sc_account_name": first_fact_value(rows, "bank_account_name", "contact_name") or name,
                "sc_bank_name": first_fact_value(rows, "bank_name"),
                "sc_bank_account": first_fact_value(rows, "bank_account"),
                "vat": tax_no,
                "legacy_credit_code": tax_no,
                "source_created_by": first_fact_value(rows, "source_operator"),
                "source_created_at": first_fact_value(rows, "source_time"),
                "source_project_name": ";".join(item for item in (source_tables, profile_sources) if item),
                "source_partner_code": first_fact_value(rows, "partner_code") or raw_legacy_partner_ids,
                "source_cooperation_type": "客户（收款合同/收款/收入事实）",
                "source_fact_count": str(sum(int(float(clean(row.get("fact_row_count")) or "0")) for row in rows)),
                "source_fact_source": ";".join(item for item in (source_tables, profile_sources) if item),
                "source_document_state": first_fact_value(rows, "document_state"),
                "source_push_result": "",
                "source_tax_rate": "",
                "source_receipt_amount": amount_text(sum(parse_amount(row.get("fact_amount")) for row in rows)),
                "source_payment_amount": "",
                "source_files": "legacy_mssql:" + ";".join(item for item in (source_tables, source_fields) if item),
                "legacy_source_evidence": evidence,
                "review_flags": ";".join(sorted(review_flags)),
            }
        )

    current_only_rows: list[dict[str, object]] = []
    payload_keys = source_keys | {key for row in payload_rows for key in current_keys({**row, "name": row.get("name")})}
    for row in current_rows:
        if current_keys(row) & payload_keys:
            continue
        current_only_rows.append({**row, "review_reason": "current_payload_row_not_found_in_business_source"})
    return payload_rows, current_only_rows


def summarize(
    payload_rows: list[dict[str, object]],
    current_rows: list[dict[str, str]],
    current_only_rows: list[dict[str, object]],
    customer_fact_sources: dict[str, int],
    supplier_fact_sources: dict[str, int],
    customer_fact_only_sources: dict[str, int],
) -> dict[str, object]:
    role_counts = Counter()
    review_counts = Counter()
    for row in payload_rows:
        customer = clean(row["customer_rank"]) == "1"
        supplier = clean(row["supplier_rank"]) == "1"
        if customer and supplier:
            role_counts["customer_and_supplier"] += 1
        elif customer:
            role_counts["customer"] += 1
        elif supplier:
            role_counts["supplier"] += 1
        else:
            role_counts["background_only"] += 1
        for flag in clean(row["review_flags"]).split(";"):
            if flag:
                review_counts[flag] += 1
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "partner_business_aligned_rebuild_adapter",
        "source": "/home/odoo/workspace/partner_import_source",
        "current_payload_rows": len(current_rows),
        "business_aligned_payload_rows": len(payload_rows),
        "current_only_review_rows": len(current_only_rows),
        "customer_business_fact_sources": customer_fact_sources,
        "customer_business_fact_only_sources": customer_fact_only_sources,
        "supplier_business_fact_sources": supplier_fact_sources,
        "role_counts": dict(sorted(role_counts.items())),
        "review_flag_counts": dict(sorted(review_counts.items())),
        "rows_with_bank_account": sum(1 for row in payload_rows if clean(row["sc_bank_account"])),
        "rows_with_bank_name": sum(1 for row in payload_rows if clean(row["sc_bank_name"])),
        "rows_with_region": sum(1 for row in payload_rows if clean(row["sc_region"])),
        "rows_with_address": sum(1 for row in payload_rows if clean(row["street"])),
        "rows_with_registered_capital": sum(1 for row in payload_rows if clean(row["sc_registered_capital"])),
        "rows_with_business_scope": sum(1 for row in payload_rows if clean(row["sc_business_scope"])),
        "rows_with_tax_rate": sum(1 for row in payload_rows if clean(row["sc_default_tax_rate"])),
        "rows_with_credit_code": sum(1 for row in payload_rows if clean(row["vat"])),
        "db_write": False,
        "decision": "business_aligned_partner_payload_ready",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default="/home/odoo/workspace/partner_import_source")
    parser.add_argument("--current-payload", default=DEFAULT_CURRENT_PAYLOAD)
    parser.add_argument("--out-dir", default="artifacts/migration/partner_business_aligned_rebuild_v1")
    parser.add_argument("--customer-fact-csv", action="append", default=[])
    parser.add_argument("--supplier-fact-csv", action="append", default=[])
    parser.add_argument("--customer-fact-only-csv", action="append", default=[])
    args = parser.parse_args()

    source_records = load_source_records(Path(args.source_root))
    current_rows = read_csv(Path(args.current_payload))
    customer_fact_paths = args.customer_fact_csv or DEFAULT_CUSTOMER_FACT_CSVS
    supplier_fact_paths = args.supplier_fact_csv or DEFAULT_SUPPLIER_FACT_CSVS
    customer_fact_only_paths = args.customer_fact_only_csv or DEFAULT_CUSTOMER_FACT_ONLY_CSVS
    customer_fact_keys, customer_fact_sources = load_business_fact_index(customer_fact_paths)
    supplier_fact_keys, supplier_fact_sources = load_business_fact_index(supplier_fact_paths)
    customer_fact_rows, customer_fact_only_sources = load_business_fact_rows(customer_fact_only_paths)
    payload_rows, current_only_rows = build_payload_rows(
        source_records,
        current_rows,
        customer_fact_keys,
        supplier_fact_keys,
        customer_fact_rows,
    )
    out_dir = Path(args.out_dir)
    write_csv(out_dir / "fact_based_partner_rebuild_payload_business_aligned_v1.csv", PAYLOAD_FIELDS, payload_rows)
    write_csv(
        out_dir / "fact_based_partner_rebuild_current_only_review_v1.csv",
        list(current_only_rows[0].keys()) if current_only_rows else PAYLOAD_FIELDS + ["review_reason"],
        current_only_rows,
    )
    summary = summarize(
        payload_rows,
        current_rows,
        current_only_rows,
        customer_fact_sources,
        supplier_fact_sources,
        customer_fact_only_sources,
    )
    write_json(out_dir / "fact_based_partner_rebuild_business_aligned_result_v1.json", summary)
    print("PARTNER_BUSINESS_ALIGNED_REBUILD=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
