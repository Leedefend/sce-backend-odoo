#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


COMPANY_CSV = Path("tmp/raw/partner/company.csv")
SUPPLIER_CSV = Path("tmp/raw/partner/supplier.csv")
CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
CURRENT_PARTNER_BASELINE = Path("artifacts/migration/contract_partner_baseline_v1.json")
OUTPUT_CSV = Path("artifacts/migration/partner_candidate_confirmation_v1.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_candidate_confirmation_summary_v1.json")

OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\u3000", " ").strip()
    return re.sub(r"\s+", " ", text)


def norm_name(value: object) -> str:
    text = clean_text(value)
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", text)
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def infer_contract_counterparty(row: dict[str, str]) -> str:
    fbf = clean_text(row.get("FBF"))
    cbf = clean_text(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return cbf
    return ""


def build_index(rows: list[dict[str, str]], name_field: str, short_field: str) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        for field in (name_field, short_field):
            name = clean_text(row.get(field))
            if not name:
                continue
            index.setdefault(name, []).append(row)
            normalized = norm_name(name)
            if normalized:
                index.setdefault(f"norm:{normalized}", []).append(row)
    return index


def current_partner_names() -> set[str]:
    if not CURRENT_PARTNER_BASELINE.exists():
        return set()
    data = json.loads(CURRENT_PARTNER_BASELINE.read_text(encoding="utf-8"))
    names = set()
    for partner in data.get("partners") or []:
        for key in ("display_name", "name"):
            name = clean_text(partner.get(key))
            if name:
                names.add(name)
                normalized = norm_name(name)
                if normalized:
                    names.add(f"norm:{normalized}")
    return names


def candidate_token(source: str, row: dict[str, str]) -> str:
    if source == "company":
        return "|".join(
            [
                clean_text(row.get("Id")),
                clean_text(row.get("DWMC")),
                clean_text(row.get("TYSHXYDM")),
                clean_text(row.get("XXDZ")),
            ]
        )
    return "|".join(
        [
            clean_text(row.get("ID")),
            clean_text(row.get("f_SupplierName")),
            clean_text(row.get("f_SupplierCode")),
            clean_text(row.get("f_Address")),
        ]
    )


def summarize_candidate(source: str, row: dict[str, str]) -> dict[str, str]:
    if source == "company":
        return {
            "source": "company",
            "source_id": clean_text(row.get("Id")),
            "source_name": clean_text(row.get("DWMC")),
            "source_short_name": clean_text(row.get("DWJC")),
            "source_code": clean_text(row.get("TYSHXYDM")),
            "source_address": clean_text(row.get("XXDZ")),
            "source_contact": clean_text(row.get("YWLXRXM")) or clean_text(row.get("FRXM")),
            "source_phone": clean_text(row.get("YWLXRHM")) or clean_text(row.get("FRSJHM")),
        }
    return {
        "source": "supplier",
        "source_id": clean_text(row.get("ID")),
        "source_name": clean_text(row.get("f_SupplierName")),
        "source_short_name": clean_text(row.get("f_SupplierShortName")),
        "source_code": clean_text(row.get("f_SupplierCode")),
        "source_address": clean_text(row.get("f_Address")),
        "source_contact": clean_text(row.get("f_Person")),
        "source_phone": clean_text(row.get("f_Phone")),
    }


def main() -> int:
    contract_rows = read_csv(CONTRACT_CSV)
    company_rows = read_csv(COMPANY_CSV)
    supplier_rows = read_csv(SUPPLIER_CSV)
    company_index = build_index(company_rows, "DWMC", "DWJC")
    supplier_index = build_index(supplier_rows, "f_SupplierName", "f_SupplierShortName")
    current_names = current_partner_names()

    counterparty_counts = Counter()
    for row in contract_rows:
        counterparty = infer_contract_counterparty(row)
        if counterparty:
            counterparty_counts[counterparty] += 1

    output_rows = []
    summary = Counter()
    weighted_summary = Counter()
    for text, contract_count in counterparty_counts.most_common():
        normalized = norm_name(text)
        company_matches = company_index.get(text, []) or company_index.get(f"norm:{normalized}", [])
        supplier_matches = supplier_index.get(text, []) or supplier_index.get(f"norm:{normalized}", [])
        existing_partner_hint = text in current_names or f"norm:{normalized}" in current_names
        if company_matches and supplier_matches:
            match_type = "cross_source_conflict"
            recommended_action = "manual_confirm_source"
            primary = summarize_candidate("company", company_matches[0])
        elif len(company_matches) == 1:
            match_type = "company_single"
            recommended_action = "manual_confirm_company_candidate"
            primary = summarize_candidate("company", company_matches[0])
        elif len(company_matches) > 1:
            match_type = "company_multiple"
            recommended_action = "manual_select_company_candidate"
            primary = summarize_candidate("company", company_matches[0])
        elif len(supplier_matches) == 1:
            match_type = "supplier_single"
            recommended_action = "manual_confirm_supplier_candidate"
            primary = summarize_candidate("supplier", supplier_matches[0])
        elif len(supplier_matches) > 1:
            match_type = "supplier_multiple"
            recommended_action = "manual_select_supplier_candidate"
            primary = summarize_candidate("supplier", supplier_matches[0])
        else:
            match_type = "defer"
            recommended_action = "manual_supply_partner_candidate"
            primary = {
                "source": "",
                "source_id": "",
                "source_name": "",
                "source_short_name": "",
                "source_code": "",
                "source_address": "",
                "source_contact": "",
                "source_phone": "",
            }
        summary[match_type] += 1
        weighted_summary[match_type] += contract_count
        output_rows.append(
            {
                "counterparty_text": text,
                "normalized_name": normalized,
                "contract_rows": contract_count,
                "match_type": match_type,
                "recommended_action": recommended_action,
                "manual_confirm_required": "yes",
                "auto_create_allowed": "no",
                "existing_partner_hint": "yes" if existing_partner_hint else "no",
                "company_candidate_count": len({candidate_token("company", row) for row in company_matches}),
                "supplier_candidate_count": len({candidate_token("supplier", row) for row in supplier_matches}),
                **primary,
                "confirm_result": "",
                "confirmed_partner_action": "",
                "confirmed_source": "",
                "confirmed_source_id": "",
                "review_note": "",
            }
        )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    result = {
        "status": "PASS",
        "mode": "partner_candidate_confirmation_no_db_write",
        "counterparty_texts": len(output_rows),
        "contract_rows_in_scope": sum(counterparty_counts.values()),
        "summary_by_text": dict(sorted(summary.items())),
        "summary_by_contract_rows": dict(sorted(weighted_summary.items())),
        "output_csv": str(OUTPUT_CSV),
        "decision": "NO-GO for partner import; manual confirmation table prepared",
        "next_step": "manual confirmation is required before partner creation dry-run",
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PARTNER_CANDIDATE_CONFIRMATION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
