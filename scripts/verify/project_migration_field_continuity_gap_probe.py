#!/usr/bin/env python3
"""Audit project master-data continuity between history carriers and formal fields.

This script is intended to run inside ``odoo shell``.  It is read-only.

Policy:
- A blocking gap is a formal target field that is empty while a historical
  carrier still has a usable value.
- A relation gap is blocking only when the historical text cannot be resolved
  to exactly one formal record.
- Empty formalized migration fields are reported as coverage only; without a
  separate source value they are not automatic backfill gaps.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    if env_root:
        return Path(env_root)
    for candidate in (Path("/mnt"), Path.cwd()):
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        [
            repo_root() / "artifacts/migration/project_migration_field_continuity_gap_probe_v1",
            Path("/mnt/artifacts/migration/project_migration_field_continuity_gap_probe_v1"),
            Path(f"/tmp/history_continuity/{env.cr.dbname}/project_migration_field_continuity_gap_probe_v1"),  # noqa: F821
        ]
    )
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            continue
    raise RuntimeError("no writable artifact root for project migration field continuity gap probe")


ARTIFACT_ROOT = artifact_root()

TEXT_TARGETS = (
    {
        "target": "owner_contact",
        "sources": ("legacy_owner_contact",),
        "label": "业主联系人",
    },
    {
        "target": "location",
        "sources": ("detail_address", "legacy_region_name"),
        "label": "项目地址",
    },
)

RELATION_TARGETS = (
    {
        "target": "owner_id",
        "source": "legacy_owner_unit",
        "relation_model": "res.partner",
        "match_fields": ("name",),
        "label": "业主单位",
    },
    {
        "target": "manager_id",
        "source": "legacy_project_manager_name",
        "relation_model": "res.users",
        "match_fields": ("name", "login"),
        "label": "项目经理",
    },
)

FORMALIZED_HISTORY_FIELDS = (
    "short_name",
    "project_environment",
    "legacy_company_name",
    "specialty_type_name",
    "legacy_price_method",
    "legacy_contract_status",
    "business_nature",
    "legacy_tax_organization_name",
    "legacy_account_name",
    "legacy_account_number",
    "legacy_account_bank",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_cost",
    "legacy_manage_fee_ratio",
    "legacy_owner_contact_phone",
    "legacy_supervision_unit",
    "legacy_supervisory_engineer",
    "legacy_supervision_phone",
    "legacy_contract_agreement",
    "legacy_project_file",
    "project_overview",
    "legacy_contracting_method",
    "legacy_project_nature",
    "legacy_tax_type",
    "legacy_stage_name",
    "legacy_region_name",
    "legacy_state",
    "legacy_xqrgz",
    "legacy_xqrgzr",
    "legacy_xqrgzxzr",
    "legacy_technical_responsibility_name",
)

CORE_FIELDS = (
    "name",
    "company_id",
    "partner_id",
    "owner_id",
    "manager_id",
    "user_id",
    "location",
    "owner_contact",
    "date_start",
    "date",
    "stage_id",
    "operation_strategy",
    "project_type_id",
    "project_category_id",
)


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def norm(value: object) -> str:
    return re.sub(r"\s+", "", clean(value)).lower()


def field_exists(model, field_name: str) -> bool:
    return field_name in model._fields


def has_value(record, field_name: str) -> bool:
    if not field_exists(record, field_name):
        return False
    value = record[field_name]
    field = record._fields[field_name]
    if field.type in {"many2one", "many2many", "one2many"}:
        return bool(value)
    if field.type in {"integer", "float", "monetary"}:
        return bool(value)
    return bool(clean(value))


def display_value(record, field_name: str) -> str:
    if not field_exists(record, field_name):
        return ""
    value = record[field_name]
    field = record._fields[field_name]
    if field.type == "many2one":
        return value.display_name if value else ""
    if field.type in {"many2many", "one2many"}:
        return ",".join(value.mapped("display_name"))
    return clean(value)


def first_source_value(record, source_fields: tuple[str, ...]) -> tuple[str, str]:
    for field_name in source_fields:
        if field_exists(record, field_name):
            value = clean(record[field_name])
            if value:
                return field_name, value
    return "", ""


def relation_index(model_name: str, match_fields: tuple[str, ...]) -> dict[str, list[int]]:
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    mapping: dict[str, list[int]] = {}
    for record in Model.search([]):
        for field_name in match_fields:
            if not field_exists(record, field_name):
                continue
            key = norm(record[field_name])
            if not key:
                continue
            mapping.setdefault(key, [])
            if record.id not in mapping[key]:
                mapping[key].append(record.id)
    return mapping


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> None:
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    projects = Project.search([], order="id")
    relation_indexes = {
        (target["relation_model"], target["match_fields"]): relation_index(
            target["relation_model"],
            target["match_fields"],
        )
        for target in RELATION_TARGETS
        if target["relation_model"] in env  # noqa: F821
    }

    blocking_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    target_summaries: list[dict[str, object]] = []
    counters: Counter[str] = Counter()

    for spec in TEXT_TARGETS:
        target = spec["target"]
        if not field_exists(Project, target):
            continue
        source_present = 0
        formal_nonempty = 0
        formal_empty_source_present = 0
        formal_empty_no_source = 0
        for project in projects:
            if has_value(project, target):
                formal_nonempty += 1
                continue
            source_field, source_value = first_source_value(project, spec["sources"])
            if source_value:
                source_present += 1
                formal_empty_source_present += 1
                blocking_rows.append(
                    {
                        "project_id": project.id,
                        "project_name": project.display_name,
                        "field": target,
                        "label": spec["label"],
                        "issue": "formal_empty_source_present",
                        "source_field": source_field,
                        "source_value": source_value,
                        "candidate_ids": "",
                    }
                )
            else:
                formal_empty_no_source += 1
        target_summaries.append(
            {
                "field": target,
                "label": spec["label"],
                "kind": "text_backfill",
                "record_count": len(projects),
                "formal_nonempty": formal_nonempty,
                "formal_empty_source_present": formal_empty_source_present,
                "formal_empty_no_source": formal_empty_no_source,
                "source_present_when_formal_empty": source_present,
            }
        )

    for spec in RELATION_TARGETS:
        target = spec["target"]
        source = spec["source"]
        if not field_exists(Project, target) or not field_exists(Project, source):
            continue
        index = relation_indexes.get((spec["relation_model"], spec["match_fields"]), {})
        formal_nonempty = 0
        formal_empty_source_present = 0
        formal_empty_no_source = 0
        unique_match = 0
        no_match = 0
        ambiguous_match = 0
        for project in projects:
            if has_value(project, target):
                formal_nonempty += 1
                continue
            source_value = clean(project[source])
            if not source_value:
                formal_empty_no_source += 1
                continue
            formal_empty_source_present += 1
            matches = index.get(norm(source_value), [])
            if len(matches) == 1:
                unique_match += 1
                issue = "formal_empty_source_unique_match"
            elif matches:
                ambiguous_match += 1
                issue = "formal_empty_source_ambiguous_match"
            else:
                no_match += 1
                issue = "formal_empty_source_no_match"
            blocking_rows.append(
                {
                    "project_id": project.id,
                    "project_name": project.display_name,
                    "field": target,
                    "label": spec["label"],
                    "issue": issue,
                    "source_field": source,
                    "source_value": source_value,
                    "candidate_ids": ",".join(str(item) for item in matches),
                }
            )
        target_summaries.append(
            {
                "field": target,
                "label": spec["label"],
                "kind": "relation_backfill",
                "record_count": len(projects),
                "formal_nonempty": formal_nonempty,
                "formal_empty_source_present": formal_empty_source_present,
                "formal_empty_no_source": formal_empty_no_source,
                "unique_match": unique_match,
                "no_match": no_match,
                "ambiguous_match": ambiguous_match,
            }
        )

    for field_name in CORE_FIELDS + FORMALIZED_HISTORY_FIELDS:
        if not field_exists(Project, field_name):
            continue
        nonempty = sum(1 for project in projects if has_value(project, field_name))
        empty = len(projects) - nonempty
        coverage_rows.append(
            {
                "field": field_name,
                "label": Project._fields[field_name].string,
                "kind": "core" if field_name in CORE_FIELDS else "formalized_history_carrier",
                "record_count": len(projects),
                "nonempty": nonempty,
                "empty": empty,
                "coverage_ratio": round(nonempty / len(projects), 6) if projects else 0,
            }
        )
        counters[f"{field_name}.nonempty"] = nonempty
        counters[f"{field_name}.empty"] = empty

    blocking_csv = ARTIFACT_ROOT / "project_migration_field_continuity_blocking_gaps_v1.csv"
    coverage_csv = ARTIFACT_ROOT / "project_migration_field_continuity_field_coverage_v1.csv"
    result_json = ARTIFACT_ROOT / "project_migration_field_continuity_gap_probe_result_v1.json"
    write_csv(
        blocking_csv,
        blocking_rows,
        ["project_id", "project_name", "field", "label", "issue", "source_field", "source_value", "candidate_ids"],
    )
    write_csv(
        coverage_csv,
        coverage_rows,
        ["field", "label", "kind", "record_count", "nonempty", "empty", "coverage_ratio"],
    )

    payload = {
        "mode": "project_migration_field_continuity_gap_probe",
        "database": env.cr.dbname,  # noqa: F821
        "status": "PASS" if not blocking_rows else "FAIL",
        "decision": "project_master_data_continuity_ready" if not blocking_rows else "project_master_data_continuity_gap",
        "project_count": len(projects),
        "blocking_gap_count": len(blocking_rows),
        "target_summaries": target_summaries,
        "coverage_rows": coverage_rows,
        "blocking_gaps_csv": str(blocking_csv),
        "coverage_csv": str(coverage_csv),
        "counters": dict(sorted(counters.items())),
    }
    result_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PROJECT_MIGRATION_FIELD_CONTINUITY_GAP_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if blocking_rows:
        raise RuntimeError(payload)


main()
