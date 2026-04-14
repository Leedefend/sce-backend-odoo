#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


COMPANY_CSV = Path("tmp/raw/partner/company.csv")
SUPPLIER_CSV = Path("tmp/raw/partner/supplier.csv")
CONTRACT_MATCH_JSON = Path("artifacts/migration/contract_partner_match_recompute_v1.json")
CONTRACT_CSV = Path("tmp/raw/contract/contract.csv")
OUTPUT_JSON = Path("artifacts/migration/partner_source_baseline_v1.json")

ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")
OWN_COMPANY_NAMES = {"四川保盛建设集团有限公司", "My Company"}


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


def profile_source(path: Path, kind: str, name_field: str, short_field: str) -> dict[str, object]:
    rows = read_csv(path)
    names = [clean_text(row.get(name_field)) for row in rows]
    shorts = [clean_text(row.get(short_field)) for row in rows]
    name_counts = Counter(name for name in names if name)
    short_counts = Counter(name for name in shorts if name)
    normalized_counts = Counter(norm_name(name) for name in names if norm_name(name))
    duplicate_names = [
        {"name": name, "rows": count}
        for name, count in name_counts.most_common()
        if count > 1
    ][:30]
    return {
        "kind": kind,
        "path": str(path),
        "row_count": len(rows),
        "field_count": len(rows[0]) if rows else 0,
        "fields": list(rows[0].keys()) if rows else [],
        "name_field": name_field,
        "short_field": short_field,
        "nonempty_name_rows": sum(1 for name in names if name),
        "nonempty_short_name_rows": sum(1 for name in shorts if name),
        "distinct_names": len(name_counts),
        "distinct_short_names": len(short_counts),
        "distinct_normalized_names": len(normalized_counts),
        "duplicate_name_count": len([name for name, count in name_counts.items() if count > 1]),
        "top_duplicate_names": duplicate_names,
        "sample_names": list(name_counts.keys())[:20],
    }


def infer_contract_counterparty(row: dict[str, str]) -> str:
    fbf = clean_text(row.get("FBF"))
    cbf = clean_text(row.get("CBF"))
    if cbf in OWN_COMPANY_NAMES and fbf not in OWN_COMPANY_NAMES:
        return fbf
    if fbf in OWN_COMPANY_NAMES and cbf not in OWN_COMPANY_NAMES:
        return cbf
    return ""


def load_counterparties() -> list[dict[str, object]]:
    rows = read_csv(CONTRACT_CSV)
    counts = Counter()
    for row in rows:
        counterparty = infer_contract_counterparty(row)
        if counterparty:
            counts[counterparty] += 1
    return [
        {"text": text, "rows": count}
        for text, count in counts.most_common()
    ]


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


def coverage(counterparties: list[dict[str, object]]) -> dict[str, object]:
    company_rows = read_csv(COMPANY_CSV)
    supplier_rows = read_csv(SUPPLIER_CSV)
    company_index = build_index(company_rows, "DWMC", "DWJC")
    supplier_index = build_index(supplier_rows, "f_SupplierName", "f_SupplierShortName")

    rows = []
    summary = Counter()
    weighted_rows = Counter()
    for item in counterparties:
        text = clean_text(item.get("text"))
        contract_rows = int(item.get("rows") or 0)
        c_matches = company_index.get(text, []) or company_index.get(f"norm:{norm_name(text)}", [])
        s_matches = supplier_index.get(text, []) or supplier_index.get(f"norm:{norm_name(text)}", [])
        match_sources = []
        if c_matches:
            match_sources.append("company")
        if s_matches:
            match_sources.append("supplier")
        match_type = "defer"
        if len(match_sources) == 1:
            candidates = c_matches if c_matches else s_matches
            match_type = f"{match_sources[0]}_single" if len(candidates) == 1 else f"{match_sources[0]}_multiple"
        elif len(match_sources) > 1:
            match_type = "cross_source_conflict"
        summary[match_type] += 1
        weighted_rows[match_type] += contract_rows
        rows.append(
            {
                "counterparty_text": text,
                "contract_rows": contract_rows,
                "match_type": match_type,
                "company_candidates": len(c_matches),
                "supplier_candidates": len(s_matches),
            }
        )
    return {
        "counterparty_count": len(counterparties),
        "summary_by_text": dict(sorted(summary.items())),
        "summary_by_contract_rows": dict(sorted(weighted_rows.items())),
        "top_by_match_type": {
            key: [row for row in rows if row["match_type"] == key][:30]
            for key in sorted(summary)
        },
        "rows": rows,
    }


def main() -> int:
    company_profile = profile_source(COMPANY_CSV, "company", "DWMC", "DWJC")
    supplier_profile = profile_source(SUPPLIER_CSV, "supplier", "f_SupplierName", "f_SupplierShortName")
    counterparties = load_counterparties()
    coverage_result = coverage(counterparties)
    result = {
        "status": "PASS",
        "mode": "partner_source_baseline_no_db_write",
        "contract_match_artifact_reference": str(CONTRACT_MATCH_JSON),
        "sources": {
            "company": company_profile,
            "supplier": supplier_profile,
        },
        "contract_counterparty_coverage": coverage_result,
        "decision": "NO-GO for partner import; source baseline only",
        "next_step": "open partner candidate normalization and manual confirmation batch before creating partners",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PARTNER_SOURCE_BASELINE="
        + json.dumps(
            {
                "status": result["status"],
                "company_rows": company_profile["row_count"],
                "supplier_rows": supplier_profile["row_count"],
                "counterparty_coverage": coverage_result["summary_by_text"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
