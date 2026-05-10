#!/usr/bin/env python3
"""Classify business-fact coverage for migrated project master anchors.

Run through ``scripts/ops/odoo_shell_exec.sh`` so the global ``env`` is
available. The classifier uses historical project and contract facts as
evidence. It does not force old projects to satisfy new-system lifecycle,
operation, or visibility rules.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DB_NAME = env.cr.dbname  # noqa: F821
REPO_ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", "/mnt"))
ARTIFACT_ROOT = Path(
    os.getenv(
        "PROJECT_MASTER_FACT_COVERAGE_ROOT",
        f"/mnt/artifacts/business-fact-audit/{DB_NAME}_project_master_fact_coverage",
    )
)
PROJECT_CSV = Path(os.getenv("PROJECT_MASTER_RAW_CSV", str(REPO_ROOT / "tmp/raw/project/project.csv")))
CONTRACT_CSV = Path(os.getenv("CONSTRUCTION_CONTRACT_RAW_CSV", str(REPO_ROOT / "tmp/raw/contract/contract.csv")))
PAYLOAD_CSV = Path(
    os.getenv("PROJECT_MASTER_REPLAY_PAYLOAD_CSV", str(REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv"))
)

OUTPUT_JSON = ARTIFACT_ROOT / "project_master_business_fact_coverage_classifier_v1.json"
SOURCE_ROW_CSV = ARTIFACT_ROOT / "project_master_source_rows_v1.csv"
CONTRACT_ANCHOR_CSV = ARTIFACT_ROOT / "project_contract_project_anchor_rows_v1.csv"
UNCOVERED_CSV = ARTIFACT_ROOT / "project_master_uncovered_business_fact_rows_v1.csv"

TECHNICAL_CREATED_BY_VALUES = {"odoobot", "administrator", "admin", "system", "系统", "系统导入"}


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def money_present(value: object) -> bool:
    text = clean(value).replace(",", "")
    if not text:
        return False
    try:
        return abs(float(text)) > 0.000001
    except ValueError:
        return False


def business_creator_present(value: object) -> bool:
    text = clean(value)
    return bool(text and text.lower() not in TECHNICAL_CREATED_BY_VALUES and text not in TECHNICAL_CREATED_BY_VALUES)


def legacy_source_project_rows() -> tuple[dict[str, dict[str, str]], list[dict[str, object]]]:
    source_index: dict[str, dict[str, str]] = {}
    evidence_rows: list[dict[str, object]] = []
    for row in read_csv(PROJECT_CSV):
        legacy_project_id = clean(row.get("ID"))
        if not legacy_project_id:
            continue
        source_index[legacy_project_id] = row
        creator_name = clean(row.get("LRR"))
        created_time = clean(row.get("LRSJ"))
        evidence_rows.append(
            {
                "source_table": "T_Project",
                "legacy_project_id": legacy_project_id,
                "project_name": clean(row.get("XMMC")),
                "legacy_deleted_flag": clean(row.get("DEL")),
                "business_nature": clean(row.get("NATURE")),
                "legacy_stage_name": clean(row.get("XMJD")),
                "legacy_company_name": clean(row.get("COMPANYNAME")),
                "creator_name": creator_name,
                "created_time": created_time,
                "source_creator_status": "source_creator_present" if business_creator_present(creator_name) else "source_creator_blank",
                "source_time_status": "source_time_present" if created_time else "source_time_blank",
                "coverage_basis": "project_master_source_row",
            }
        )
    return source_index, evidence_rows


def contract_has_business_fact(row: dict[str, str]) -> bool:
    fact_fields = (
        "DJBH",
        "HTBH",
        "HTBT",
        "f_XMMC",
        "f_GCXZ",
        "FBF",
        "CBF",
        "f_LRSJ",
        "LRRQ",
        "f_LRR",
        "LRR",
    )
    if any(clean(row.get(field)) for field in fact_fields):
        return True
    return any(money_present(row.get(field)) for field in ("GCYSZJ", "f_HTJK", "YFK", "ZLBZJ", "D_SCBSJS_QYHTJ", "D_SCBSJS_JSJE"))


def contract_project_anchor_rows(source_project_ids: set[str]) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(CONTRACT_CSV):
        legacy_project_id = clean(row.get("XMID"))
        if legacy_project_id and contract_has_business_fact(row):
            grouped.setdefault(legacy_project_id, []).append(row)

    anchor_index: dict[str, dict[str, object]] = {}
    evidence_rows: list[dict[str, object]] = []
    for legacy_project_id, rows in sorted(grouped.items()):
        visible_rows = [
            row
            for row in rows
            if clean(row.get("DEL")) != "1"
            and clean(row.get("DJZT")) in {"2", "1", ""}
            and bool(clean(row.get("HTBT")))
            and bool(clean(row.get("FBF")))
        ]
        selected = visible_rows[0] if visible_rows else rows[0]
        amount_sum = sum(
            float(clean(row.get("GCYSZJ")).replace(",", "") or "0")
            for row in rows
            if clean(row.get("GCYSZJ")).replace(",", "").replace(".", "", 1).replace("-", "", 1).isdigit()
        )
        creator_values = [clean(row.get("LRR")) or clean(row.get("f_LRR")) for row in rows]
        time_values = [clean(row.get("LRRQ")) or clean(row.get("f_LRSJ")) for row in rows]
        business_nature_counts = Counter(clean(row.get("f_GCXZ")) or "__empty__" for row in rows)
        status_counts = Counter(clean(row.get("DJZT")) or "__empty__" for row in rows)
        anchor_index[legacy_project_id] = {
            "legacy_project_id": legacy_project_id,
            "source_rows": len(rows),
            "visible_source_rows": len(visible_rows),
            "project_name": clean(selected.get("f_XMMC")) or clean(selected.get("XMBM")) or clean(selected.get("HTBT")) or legacy_project_id,
            "sample_contract_id": clean(selected.get("Id")),
            "sample_contract_no": clean(selected.get("DJBH")) or clean(selected.get("HTBH")),
            "sample_contract_subject": clean(selected.get("HTBT")),
            "amount_gcyszj_sum": f"{amount_sum:.2f}",
            "business_nature_counts": dict(sorted(business_nature_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "has_project_master_row": legacy_project_id in source_project_ids,
            "creator_present_rows": sum(1 for value in creator_values if business_creator_present(value)),
            "time_present_rows": sum(1 for value in time_values if clean(value)),
        }
        evidence_rows.append(
            {
                **anchor_index[legacy_project_id],
                "business_nature_counts": json.dumps(dict(sorted(business_nature_counts.items())), ensure_ascii=False, sort_keys=True),
                "status_counts": json.dumps(dict(sorted(status_counts.items())), ensure_ascii=False, sort_keys=True),
                "coverage_basis": "contract_project_business_fact",
            }
        )
    return anchor_index, evidence_rows


def payload_project_ids() -> set[str]:
    return {clean(row.get("legacy_project_id")) for row in read_csv(PAYLOAD_CSV) if clean(row.get("legacy_project_id"))}


def target_project_index() -> dict[str, object]:
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    if "legacy_project_id" not in Project._fields:
        return {}
    records = Project.search([("legacy_project_id", "!=", False)])
    index: dict[str, object] = {}
    for record in records:
        legacy_project_id = clean(record.legacy_project_id)
        if legacy_project_id and legacy_project_id not in index:
            index[legacy_project_id] = record
    return index


def downstream_project_fact_counts(project_ids: list[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for model_name in (
        "construction.contract",
        "payment.request",
        "sc.payment.execution",
        "sc.receipt.income",
        "sc.invoice.registration",
        "sc.general.contract",
        "sc.treasury.ledger",
        "sc.legacy.receipt.income.fact",
        "sc.legacy.payment.residual.fact",
        "sc.legacy.receipt.residual.fact",
        "sc.legacy.supplier.contract.pricing.fact",
        "sc.legacy.project.fund.balance.fact",
        "sc.legacy.fund.daily.line",
        "sc.legacy.invoice.registration.line",
        "sc.legacy.enterprise.business.fact",
    ):
        if model_name not in env:  # noqa: F821
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        if "project_id" not in Model._fields:
            continue
        counts[model_name] = Model.search_count([("project_id", "in", project_ids)])
    return dict(sorted(counts.items()))


def classify() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    source_index, source_rows = legacy_source_project_rows()
    contract_index, contract_rows = contract_project_anchor_rows(set(source_index))
    payload_ids = payload_project_ids()
    target_index = target_project_index()
    target_ids = set(target_index)
    source_ids = set(source_index)
    contract_ids = set(contract_index)
    all_business_fact_project_ids = source_ids | contract_ids

    uncovered_rows: list[dict[str, object]] = []
    blocking_counts: Counter[str] = Counter()
    for legacy_project_id in sorted(all_business_fact_project_ids):
        in_source = legacy_project_id in source_ids
        in_contract = legacy_project_id in contract_ids
        in_payload = legacy_project_id in payload_ids
        in_target = legacy_project_id in target_ids
        if in_payload and in_target:
            continue
        contract_fact = contract_index.get(legacy_project_id, {})
        reason = []
        if not in_payload:
            reason.append("missing_replay_payload")
            blocking_counts["missing_replay_payload"] += 1
        if not in_target:
            reason.append("missing_target_project_anchor")
            blocking_counts["missing_target_project_anchor"] += 1
        uncovered_rows.append(
            {
                "legacy_project_id": legacy_project_id,
                "project_name": clean(source_index.get(legacy_project_id, {}).get("XMMC")) or clean(contract_fact.get("project_name")),
                "has_project_master_source": int(in_source),
                "has_contract_business_fact": int(in_contract),
                "in_replay_payload": int(in_payload),
                "in_target_project": int(in_target),
                "contract_source_rows": contract_fact.get("source_rows", 0),
                "contract_visible_source_rows": contract_fact.get("visible_source_rows", 0),
                "contract_amount_gcyszj_sum": contract_fact.get("amount_gcyszj_sum", ""),
                "blocking_reason": ",".join(reason),
            }
        )

    target_project_ids = [record.id for key, record in target_index.items() if key in all_business_fact_project_ids]
    downstream_counts = downstream_project_fact_counts(target_project_ids)
    source_creator_counts = Counter(row["source_creator_status"] for row in source_rows)
    source_time_counts = Counter(row["source_time_status"] for row in source_rows)
    contract_payload_missing = sorted(contract_ids - payload_ids)
    status = "PASS" if not blocking_counts else "WARN"
    return {
        "status": status,
        "database": DB_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "project_master_business_fact_coverage_classifier",
        "project_master_business_fact_coverage": {
            "legacy_project_source_rows": len(source_ids),
            "contract_project_business_fact_anchors": len(contract_ids),
            "contract_project_anchors_without_project_master_source": len(contract_ids - source_ids),
            "all_business_fact_project_anchors": len(all_business_fact_project_ids),
            "replay_payload_project_anchors": len(payload_ids),
            "target_project_anchors": len(target_ids & all_business_fact_project_ids),
            "uncovered_business_fact_project_anchors": len(uncovered_rows),
            "blocking_counts": dict(sorted(blocking_counts.items())),
            "project_source_creator_coverage_counts": dict(sorted(source_creator_counts.items())),
            "project_source_time_coverage_counts": dict(sorted(source_time_counts.items())),
            "contract_project_anchors_missing_from_payload": len(contract_payload_missing),
            "contract_project_anchors_missing_from_payload_samples": contract_payload_missing[:20],
            "downstream_project_fact_counts": downstream_counts,
        },
        "legacy_source_blank_fields_are_acceptance_blockers": False,
        "objective_fact_policy": (
            "Project master acceptance is based on carrying historical project business facts and source anchors. "
            "Old project data is not forced to satisfy new lifecycle, operation-strategy, visibility, or mandatory-field rules. "
            "Contract facts with a legacy project id are project-anchor evidence even when old visibility/status fields would not pass a new user-facing filter. "
            "Odoo create_uid/create_date and import timestamps are technical metadata."
        ),
        "artifact_root": str(ARTIFACT_ROOT),
        "source_project_csv": str(PROJECT_CSV),
        "source_contract_csv": str(CONTRACT_CSV),
        "replay_payload_csv": str(PAYLOAD_CSV),
    }, source_rows, contract_rows, uncovered_rows


ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
payload, source_rows, contract_rows, uncovered_rows = classify()
write_csv(SOURCE_ROW_CSV, source_rows)
write_csv(CONTRACT_ANCHOR_CSV, contract_rows)
write_csv(UNCOVERED_CSV, uncovered_rows)
write_json(OUTPUT_JSON, payload)
print("PROJECT_MASTER_BUSINESS_FACT_COVERAGE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
