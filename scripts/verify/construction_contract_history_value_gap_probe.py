#!/usr/bin/env python3
"""Audit construction contract values against raw historical contract data.

Run inside ``odoo shell``.  This script is read-only.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    if env_root:
        return Path(env_root)
    for candidate in (Path("/mnt"), Path.cwd()):
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
RAW_CSV_NAME = "T_ProjectContract_Out_contract.csv"


def raw_csv_path() -> Path:
    configured = os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV")
    if configured:
        return Path(configured)
    candidates = [
        Path("/mnt/artifacts/migration/source_extracts") / RAW_CSV_NAME,
        REPO_ROOT / "artifacts/migration/source_extracts" / RAW_CSV_NAME,
        Path.cwd() / "artifacts/migration/source_extracts" / RAW_CSV_NAME,
    ]
    artifact_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if artifact_root:
        candidates.append(Path(artifact_root).parent / "source_extracts" / RAW_CSV_NAME)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


RAW_CSV = raw_csv_path()
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/construction_contract_history_value_gap_probe_v1"),
    )
)


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null", "/"} else text


def clean_rich_text(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    result = re.sub(r"\n{3,}", "\n\n", text).strip()
    return "" if result in {"/", "／"} else result


def parse_datetime(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    normalized = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S.%f"):
        try:
            return datetime.strptime(normalized[:26], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return ""


def parse_date(value: object) -> str:
    parsed = parse_datetime(value)
    if parsed:
        return parsed[:10]
    text = clean(value)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def source_duration(row: dict[str, str]) -> str:
    return clean_rich_text(row.get("GQSM")) or clean(row.get("f_HTGQ")) or clean(row.get("f_THGQTS"))


def source_payment_method(row: dict[str, str]) -> str:
    return clean_rich_text(row.get("HTYDFKFS")) or clean_rich_text(row.get("f_FKFS"))


def source_entry_user(row: dict[str, str]) -> str:
    return clean(row.get("LRR")) or clean(row.get("f_LRR"))


def source_entry_time(row: dict[str, str]) -> str:
    return parse_datetime(row.get("f_LRSJ")) or parse_datetime(row.get("LRRQ"))


def read_rows(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = clean(row.get("Id"))
            if legacy_id:
                rows[legacy_id] = row
    return rows


FIELD_SOURCES = (
    ("date_contract", "合同订立日期", lambda row: parse_date(row.get("f_HTDLRQ"))),
    ("engineering_category_text", "工程类别", lambda row: clean(row.get("HTLX"))),
    ("affiliated_person", "挂靠人", lambda row: clean(row.get("GKR"))),
    ("engineering_address", "工程地址", lambda row: clean(row.get("f_GCDZ"))),
    ("engineering_content", "工程内容", lambda row: clean(row.get("f_GCNR"))),
    ("contract_duration_text", "合同工期", source_duration),
    ("contract_payment_method_text", "合同约定付款方式", source_payment_method),
    ("entry_user_text", "录入人", source_entry_user),
    ("entry_time", "录入时间", source_entry_time),
    ("attachment_text", "附件", lambda row: clean(row.get("f_FJ"))),
)


def target_value(record, field: str) -> str:
    if field not in record._fields:
        return ""
    value = record[field]
    if record._fields[field].type == "datetime":
        return str(value or "")[:19]
    if record._fields[field].type == "date":
        return str(value or "")
    return clean(value)


def main() -> None:
    rows_by_id = read_rows(RAW_CSV)
    Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
    contracts = Contract.search([("legacy_contract_id", "in", sorted(rows_by_id))], order="id")

    summaries = []
    gap_rows = []
    mismatch_rows = []
    matched = 0
    for field, label, getter in FIELD_SOURCES:
        source_nonempty = target_nonempty = source_present_target_empty = mismatches = 0
        for contract in contracts:
            row = rows_by_id.get(clean(contract.legacy_contract_id))
            if not row:
                continue
            matched += 1
            source = getter(row)
            target = target_value(contract, field)
            if source:
                source_nonempty += 1
            if target:
                target_nonempty += 1
            if source and not target:
                source_present_target_empty += 1
                gap_rows.append(
                    {
                        "contract_id": contract.id,
                        "legacy_contract_id": contract.legacy_contract_id,
                        "legacy_document_no": contract.legacy_document_no,
                        "field": field,
                        "label": label,
                        "source_value": source[:500],
                    }
                )
            elif source and target and field in {"date_contract", "entry_time"} and source != target:
                mismatches += 1
                mismatch_rows.append(
                    {
                        "contract_id": contract.id,
                        "legacy_contract_id": contract.legacy_contract_id,
                        "legacy_document_no": contract.legacy_document_no,
                        "field": field,
                        "label": label,
                        "source_value": source,
                        "target_value": target,
                    }
                )
        summaries.append(
            {
                "field": field,
                "label": label,
                "matched_contracts": len(contracts),
                "source_nonempty": source_nonempty,
                "target_nonempty": target_nonempty,
                "source_present_target_empty": source_present_target_empty,
                "date_or_time_mismatch": mismatches,
            }
        )

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    result = {
        "mode": "construction_contract_history_value_gap_probe",
        "database": env.cr.dbname,  # noqa: F821
        "raw_csv": str(RAW_CSV),
        "raw_rows": len(rows_by_id),
        "matched_contracts": len(contracts),
        "blocking_gap_count": len(gap_rows),
        "date_or_time_mismatch_count": len(mismatch_rows),
        "status": "PASS" if not gap_rows and not mismatch_rows else "FAIL",
        "field_summaries": summaries,
    }
    (ARTIFACT_ROOT / "construction_contract_history_value_gap_probe_result_v1.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (ARTIFACT_ROOT / "construction_contract_history_value_blocking_gaps_v1.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["contract_id", "legacy_contract_id", "legacy_document_no", "field", "label", "source_value"])
        writer.writeheader()
        writer.writerows(gap_rows)
    with (ARTIFACT_ROOT / "construction_contract_history_value_mismatches_v1.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["contract_id", "legacy_contract_id", "legacy_document_no", "field", "label", "source_value", "target_value"])
        writer.writeheader()
        writer.writerows(mismatch_rows)
    print("CONSTRUCTION_CONTRACT_HISTORY_VALUE_GAP_PROBE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise RuntimeError(result)


main()
