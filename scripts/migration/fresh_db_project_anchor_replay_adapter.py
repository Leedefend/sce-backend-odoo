#!/usr/bin/env python3
"""Build a no-DB fresh-db replay payload for all project anchors."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path.cwd()
PROJECT_CSV = REPO_ROOT / "tmp/raw/project/project.csv"
CONTRACT_CSV = REPO_ROOT / "tmp/raw/contract/contract.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json"
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv"
OUTPUT_GAP_CSV = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_gap_matrix_v1.csv"
OUTPUT_REPORT = REPO_ROOT / "docs/migration_alignment/fresh_db_project_anchor_replay_adapter_report_v1.md"
ASSET_XML = REPO_ROOT / "migration_assets/10_master/project/project_master_v1.xml"

WRITE_RESULTS = [
    "artifacts/migration/project_create_only_write_result_v1.json",
    "artifacts/migration/project_create_only_expand_write_result_v1.json",
    "artifacts/migration/project_v2_100_write_result.json",
    "artifacts/migration/project_v3_100_write_result.json",
    "artifacts/migration/project_v4_200_write_result.json",
    "artifacts/migration/project_v5_200_write_result.json",
    "artifacts/migration/project_remaining_25_write_result.json",
]

PAYLOAD_FIELDS = [
    "legacy_project_id",
    "legacy_parent_id",
    "name",
    "short_name",
    "project_environment",
    "legacy_company_id",
    "legacy_company_name",
    "legacy_specialty_type_id",
    "specialty_type_name",
    "legacy_price_method",
    "business_nature",
    "operation_strategy",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_is_shared_base",
    "legacy_sort",
    "legacy_attachment_ref",
    "project_overview",
    "legacy_project_nature",
    "legacy_is_material_library",
    "other_system_id",
    "other_system_code",
    "legacy_stage_id",
    "legacy_stage_name",
    "legacy_region_id",
    "legacy_region_name",
    "legacy_state",
    "legacy_deleted_flag",
    "legacy_project_manager_name",
    "legacy_technical_responsibility_name",
    "current_db_project_id",
    "evidence_file",
    "replay_source_lane",
    "replay_evidence_rows",
    "idempotency_key",
    "replay_action",
]

GAP_FIELDS = [
    "legacy_project_id",
    "source_lane",
    "source_rows",
    "visible_source_rows",
    "project_name",
    "sample_contract_id",
    "sample_contract_subject",
    "visible_filter_reasons",
    "legacy_status_counts",
    "source_deleted_rows",
    "missing_subject_rows",
    "missing_counterparty_rows",
    "amount_gcyszj_sum",
    "business_nature_counts",
    "gap_route",
    "gap_note",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def is_deleted_flag(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n"}


def operation_strategy_from_business_nature(value: object) -> str:
    text = clean(value)
    if text == "联营":
        return "joint"
    if text == "自营":
        return "direct"
    return ""


def visible_filter_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    if clean(row.get("DEL")) == "1":
        reasons.append("deleted_contract")
    if clean(row.get("DJZT")) not in {"2", "1", ""}:
        reasons.append("non_visible_status")
    if not clean(row.get("HTBT")):
        reasons.append("missing_subject")
    if not clean(row.get("FBF")):
        reasons.append("missing_counterparty")
    return reasons or ["visible"]


def parse_amount(value: object) -> float:
    text = clean(value).replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_source_index() -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in read_csv(PROJECT_CSV):
        legacy_project_id = clean(row.get("ID"))
        if not legacy_project_id:
            continue
        index[legacy_project_id] = {
            "legacy_project_id": legacy_project_id,
            "legacy_parent_id": clean(row.get("PID")),
            "name": clean(row.get("XMMC")),
            "short_name": clean(row.get("SHORT_NAME")),
            "project_environment": clean(row.get("PROJECT_ENV")),
            "legacy_company_id": clean(row.get("COMPANYID")),
            "legacy_company_name": clean(row.get("COMPANYNAME")),
            "legacy_specialty_type_id": clean(row.get("SPECIALTY_TYPE_ID")),
            "specialty_type_name": clean(row.get("SPECIALTY_TYPE_NAME")),
            "legacy_price_method": clean(row.get("PRICE_METHOD")),
            "business_nature": clean(row.get("NATURE")),
            "operation_strategy": operation_strategy_from_business_nature(row.get("NATURE")),
            "detail_address": clean(row.get("DETAIL_ADDRESS")),
            "project_profile": clean(row.get("PROFILE")),
            "project_area": clean(row.get("AREA")),
            "legacy_is_shared_base": clean(row.get("IS_SHARED_BASE")),
            "legacy_sort": clean(row.get("SORT")),
            "legacy_attachment_ref": clean(row.get("FJ")),
            "project_overview": clean(row.get("PROJECTOVERVIEW")),
            "legacy_project_nature": clean(row.get("PROJECT_NATURE")),
            "legacy_is_material_library": clean(row.get("IS_MACHINTERIAL_LIBRARY")),
            "other_system_id": clean(row.get("OTHER_SYSTEM_ID")),
            "other_system_code": clean(row.get("OTHER_SYSTEM_CODE")),
            "legacy_stage_id": clean(row.get("XMJDID")),
            "legacy_stage_name": clean(row.get("XMJD")),
            "legacy_region_id": clean(row.get("SSDQID")),
            "legacy_region_name": clean(row.get("SSDQ")),
            "legacy_state": clean(row.get("STATE")),
            "legacy_deleted_flag": clean(row.get("DEL")),
            "legacy_project_manager_name": clean(row.get("PROJECTMANAGER")),
            "legacy_technical_responsibility_name": clean(row.get("TECHNICALRESPONSIBILITY")),
        }
    return index


def is_legacy_income_visible(row: dict[str, str]) -> bool:
    return (
        clean(row.get("DEL")) != "1"
        and clean(row.get("DJZT")) in {"2", "1", ""}
        and bool(clean(row.get("HTBT")))
        and bool(clean(row.get("FBF")))
    )


def enrich_project_master_from_visible_contracts(project_index: dict[str, dict[str, str]]) -> int:
    if not CONTRACT_CSV.exists():
        return 0

    visible_contracts_by_project: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(CONTRACT_CSV):
        legacy_project_id = clean(row.get("XMID"))
        if legacy_project_id in project_index and is_legacy_income_visible(row):
            visible_contracts_by_project.setdefault(legacy_project_id, []).append(row)

    enriched = 0
    for legacy_project_id, source in project_index.items():
        if clean(source.get("business_nature")):
            continue
        contracts = visible_contracts_by_project.get(legacy_project_id) or []
        nature_counts = Counter(clean(row.get("f_GCXZ")) for row in contracts if clean(row.get("f_GCXZ")))
        if len(nature_counts) != 1:
            continue
        business_nature = next(iter(nature_counts))
        source["business_nature"] = business_nature
        source["operation_strategy"] = operation_strategy_from_business_nature(business_nature)
        source["_replay_source_lane"] = "project_master_contract_enriched"
        source["_replay_evidence_rows"] = str(sum(nature_counts.values()))
        enriched += 1
    return enriched


def contract_project_anchor_candidates(project_index: dict[str, dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if not CONTRACT_CSV.exists():
        return [], []

    rows_by_project: dict[str, list[dict[str, str]]] = {}
    visible_by_project: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(CONTRACT_CSV):
        legacy_project_id = clean(row.get("XMID"))
        if not legacy_project_id or legacy_project_id in project_index:
            continue
        rows_by_project.setdefault(legacy_project_id, []).append(row)
        if is_legacy_income_visible(row):
            visible_by_project.setdefault(legacy_project_id, []).append(row)

    candidates: list[dict[str, object]] = []
    gaps: list[dict[str, object]] = []
    for legacy_project_id, source_rows in sorted(rows_by_project.items()):
        visible_rows = visible_by_project.get(legacy_project_id, [])
        selected = visible_rows[0] if visible_rows else source_rows[0]
        name = clean(selected.get("f_XMMC")) or clean(selected.get("XMBM")) or clean(selected.get("HTBT")) or legacy_project_id
        fact_rows_for_nature = visible_rows or source_rows
        nature_counts = Counter(clean(row.get("f_GCXZ")) or "__empty__" for row in fact_rows_for_nature)
        selected_nature = next((nature for nature, _count in nature_counts.most_common() if nature != "__empty__"), "")
        if visible_rows:
            candidates.append(
                {
                    "source_file": str(CONTRACT_CSV.relative_to(REPO_ROOT)),
                    "legacy_project_id": legacy_project_id,
                    "name": name,
                    "project_environment": "legacy_contract_visible_project_anchor",
                    "business_nature": selected_nature,
                    "operation_strategy": operation_strategy_from_business_nature(selected_nature),
                    "legacy_state": "contract_visible_project_anchor",
                    "current_db_project_id": "",
                    "replay_source_lane": "contract_visible_project_anchor",
                    "replay_evidence_rows": len(visible_rows),
                }
            )
            continue
        gaps.append(
            {
                "legacy_project_id": legacy_project_id,
                "source_lane": "contract_project_anchor_gap",
                "source_rows": len(source_rows),
                "visible_source_rows": 0,
                "project_name": name,
                "sample_contract_id": clean(selected.get("Id")),
                "sample_contract_subject": clean(selected.get("HTBT")),
                "visible_filter_reasons": ",".join(
                    sorted({reason for row in source_rows for reason in visible_filter_reasons(row)})
                ),
                "legacy_status_counts": json.dumps(
                    dict(sorted(Counter(clean(row.get("DJZT")) or "__empty__" for row in source_rows).items())),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "source_deleted_rows": sum(1 for row in source_rows if clean(row.get("DEL")) == "1"),
                "missing_subject_rows": sum(1 for row in source_rows if not clean(row.get("HTBT"))),
                "missing_counterparty_rows": sum(1 for row in source_rows if not clean(row.get("FBF"))),
                "amount_gcyszj_sum": f"{sum(parse_amount(row.get('GCYSZJ')) for row in source_rows):.2f}",
                "business_nature_counts": json.dumps(dict(sorted(nature_counts.items())), ensure_ascii=False, sort_keys=True),
                "gap_route": "contract_not_visible_project_anchor_deferred",
                "gap_note": "contract source has project id absent from project.csv but does not pass visible income contract filter",
            }
        )
    return candidates, gaps


def load_created_rows() -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    missing_files: list[str] = []
    for rel_path in WRITE_RESULTS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("created", []):
            rows.append(
                {
                    "source_file": rel_path,
                    "legacy_project_id": clean(row.get("legacy_project_id")),
                    "name": clean(row.get("name")),
                    "current_db_project_id": clean(row.get("id")),
                }
            )
    return rows, missing_files


def field_map(record: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in record.findall("field"):
        name = clean(field.get("name"))
        if name:
            values[name] = clean(field.text)
    return values


def load_asset_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    root = ET.parse(ASSET_XML).getroot()
    for record in root.findall(".//record[@model='project.project']"):
        values = field_map(record)
        legacy_project_id = clean(values.get("legacy_project_id"))
        if not legacy_project_id:
            continue
        rows.append(
            {
                "source_file": str(ASSET_XML.relative_to(REPO_ROOT)),
                "legacy_project_id": legacy_project_id,
                "name": clean(values.get("name")),
                "current_db_project_id": "",
                **{field: clean(values.get(field)) for field in PAYLOAD_FIELDS if field not in {"current_db_project_id", "evidence_file", "idempotency_key", "replay_action"}},
            }
        )
    return rows


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Project Anchor Replay Adapter Report v1

Status: {payload["status"]}

Task: `ITER-2026-05-07-FRESH-DB-REPLAY-PROJECT-ANCHOR-CONSOLIDATED`

## Scope

Build a no-DB consolidated replay payload for project anchors from the project
master source and visible contract-fact project anchors. This batch does not
execute project write scripts and does not touch a database.

## Result

- project master source rows: `{payload["project_master_source_rows"]}`
- project master contract-enriched rows: `{payload["project_master_contract_enriched_rows"]}`
- contract visible project anchor rows: `{payload["contract_visible_project_anchor_rows"]}`
- deferred contract project gaps: `{payload["deferred_contract_project_gap_count"]}`
- deferred contract project gap amount: `{payload["deferred_contract_project_gap_amount_sum"]}`
- replay payload rows: `{payload["replay_payload_rows"]}`
- duplicate replay identities: `{payload["duplicate_replay_identities"]}`
- raw source misses: `{payload["raw_source_misses"]}`
- deleted source rows in payload: `{payload["deleted_source_rows"]}`
- DB writes: `0`

## Source Lanes

```json
{json.dumps(payload["source_lane_counts"], ensure_ascii=False, indent=2)}
```

## Operation Strategy

```json
{json.dumps(payload["operation_strategy_counts"], ensure_ascii=False, indent=2)}
```

## Stage Counts

```json
{json.dumps(payload["stage_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


def main() -> int:
    source_index = project_source_index()
    project_master_contract_enriched_rows = enrich_project_master_from_visible_contracts(source_index)
    asset_rows = load_asset_rows() if ASSET_XML.exists() else []
    created_rows = [
        {
            "source_file": str(PROJECT_CSV.relative_to(REPO_ROOT)),
            "legacy_project_id": legacy_project_id,
            "name": source["name"],
            "current_db_project_id": "",
            "replay_source_lane": source.get("_replay_source_lane", "project_master"),
            "replay_evidence_rows": source.get("_replay_evidence_rows", 1),
        }
        for legacy_project_id, source in sorted(source_index.items())
    ]
    contract_rows, gap_rows = contract_project_anchor_candidates(source_index)
    created_rows.extend(contract_rows)
    seen: dict[str, dict[str, object]] = {}
    duplicates: list[dict[str, object]] = []
    raw_misses: list[dict[str, str]] = []
    stage_counts: Counter[str] = Counter()
    source_lane_counts: Counter[str] = Counter()
    deleted_source_rows = 0

    for row in created_rows:
        legacy_project_id = clean(row["legacy_project_id"])
        if not legacy_project_id:
            raw_misses.append({"legacy_project_id": legacy_project_id, "reason": "missing_identity"})
            continue
        if legacy_project_id in seen:
            duplicates.append({"legacy_project_id": legacy_project_id})
            continue
        source = source_index.get(legacy_project_id)
        if not source:
            source = {
                field: ""
                for field in PAYLOAD_FIELDS
                if field
                not in {
                    "current_db_project_id",
                    "evidence_file",
                    "replay_source_lane",
                    "replay_evidence_rows",
                    "idempotency_key",
                    "replay_action",
                }
            }
            source["legacy_project_id"] = legacy_project_id
            source["name"] = clean(row["name"])
            for field in PAYLOAD_FIELDS:
                if field in row and clean(row.get(field)):
                    source[field] = clean(row.get(field))
        stage_counts[source.get("legacy_stage_name", "") or "unknown"] += 1
        if is_deleted_flag(source.get("legacy_deleted_flag")):
            deleted_source_rows += 1
        payload_row = dict(source)
        payload_row.pop("_replay_source_lane", None)
        payload_row.pop("_replay_evidence_rows", None)
        payload_row.update(
            {
                "current_db_project_id": clean(row["current_db_project_id"]),
                "evidence_file": row["source_file"],
                "replay_source_lane": clean(row.get("replay_source_lane")) or "project_master",
                "replay_evidence_rows": clean(row.get("replay_evidence_rows")) or "1",
                "idempotency_key": f"project::{legacy_project_id}",
                "replay_action": "create_if_missing",
            }
        )
        source_lane_counts[payload_row["replay_source_lane"]] += 1
        seen[legacy_project_id] = payload_row

    payload_rows = sorted(seen.values(), key=lambda item: clean(item["legacy_project_id"]))
    asset_ids = {clean(row.get("legacy_project_id")) for row in asset_rows}
    payload_ids = {clean(row.get("legacy_project_id")) for row in payload_rows}
    operation_strategy_counts = Counter(clean(row.get("operation_strategy")) or "unspecified" for row in payload_rows)
    status = "PASS" if not duplicates and not raw_misses else "FAIL"
    payload = {
        "status": status,
        "mode": "fresh_db_project_anchor_replay_adapter",
        "source_mode": "project_master_plus_visible_contract_facts",
        "db_writes": 0,
        "database_operations": 0,
        "write_scripts_executed": 0,
        "write_result_files": 0,
        "missing_write_result_files": [],
        "asset_xml": str(ASSET_XML) if ASSET_XML.exists() else "",
        "asset_xml_rows": len(asset_rows),
        "asset_xml_missing_from_payload_rows": len(asset_ids - payload_ids),
        "project_master_source_rows": len(source_index),
        "project_master_contract_enriched_rows": project_master_contract_enriched_rows,
        "contract_visible_project_anchor_rows": len(contract_rows),
        "contract_visible_project_anchor_contract_rows": sum(int(clean(row.get("replay_evidence_rows")) or "0") for row in contract_rows),
        "deferred_contract_project_gap_count": len(gap_rows),
        "deferred_contract_project_gap_amount_sum": f"{sum(float(clean(row.get('amount_gcyszj_sum')) or '0') for row in gap_rows):.2f}",
        "created_evidence_rows": len(created_rows),
        "replay_payload_rows": len(payload_rows),
        "duplicate_replay_identities": len(duplicates),
        "duplicate_samples": duplicates[:20],
        "raw_source_misses": len(raw_misses),
        "raw_source_miss_samples": raw_misses[:20],
        "deleted_source_rows": deleted_source_rows,
        "source_lane_counts": dict(sorted(source_lane_counts.items())),
        "operation_strategy_counts": dict(sorted(operation_strategy_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "gap_artifact": str(OUTPUT_GAP_CSV),
        "decision": "project_anchor_replay_payload_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
        "next_step": "run unified project anchor replay write before dependent fact replay",
    }
    write_csv(OUTPUT_CSV, PAYLOAD_FIELDS, payload_rows)
    write_csv(OUTPUT_GAP_CSV, GAP_FIELDS, gap_rows)
    write_json(OUTPUT_JSON, payload)
    write_report(payload)
    print(
        "FRESH_DB_PROJECT_ANCHOR_REPLAY_ADAPTER="
        + json.dumps(
            {
                "status": status,
                "created_evidence_rows": len(created_rows),
                "replay_payload_rows": len(payload_rows),
                "duplicates": len(duplicates),
                "raw_source_misses": len(raw_misses),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
