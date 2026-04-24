#!/usr/bin/env python3
"""Read-only precheck for fresh database replay payloads.

Run with:
    DB=sc_migration_fresh make odoo.shell.exec < scripts/migration/fresh_db_replay_payload_precheck.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
PARTNER_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv"
PROJECT_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv"
CONTRACT_PARTNER_PAYLOAD = REPO_ROOT / "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_replay_payload_precheck_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "fresh_db_replay_payload_precheck_report_v1.md"


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Fresh DB Replay Payload Precheck Report v1

Status: {payload["status"]}

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-PAYLOAD-PRECHECK`

## Scope

Read-only validation of ready replay payloads against the current replay target.
This batch does not create, update, or delete business records.

## Payload Rows

- partner L4 anchors: `{payload["payload_rows"]["partner_l4"]}`
- project anchors: `{payload["payload_rows"]["project_anchor"]}`
- contract partner 12 anchors: `{payload["payload_rows"]["contract_partner_12"]}`

## Target State

- database: `{payload["database"]}`
- target model missing count: `{len(payload["missing_models"])}`
- required identity field missing count: `{len(payload["missing_required_fields"])}`
- existing partner identity collisions: `{payload["identity_collisions"]["partner_l4"]}`
- existing project identity collisions: `{payload["identity_collisions"]["project_anchor"]}`
- existing contract partner name collisions: `{payload["identity_collisions"]["contract_partner_12"]}`
- DB writes: `0`

## Current Counts

```json
{json.dumps(payload["current_counts"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""
    try:
        OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_REPORT.write_text(text, encoding="utf-8")
    except OSError:
        pass


partner_rows = read_csv(PARTNER_PAYLOAD)
project_rows = read_csv(PROJECT_PAYLOAD)
contract_partner_rows = read_csv(CONTRACT_PARTNER_PAYLOAD)

required_fields = {
    "res.partner": ["name", "legacy_partner_source", "legacy_partner_id", "legacy_source_evidence", "legacy_tax_no", "legacy_deleted_flag"],
    "project.project": ["name", "legacy_project_id", "legacy_parent_id", "legacy_company_id", "other_system_id", "other_system_code"],
    "construction.contract": ["name", "legacy_contract_id", "legacy_project_id", "partner_id", "project_id"],
    "sc.project.member.staging": ["legacy_project_id", "legacy_user_ref", "legacy_role_text", "project_id"],
}
optional_fields = {
    "project.project": ["legacy_deleted_flag"],
}

missing_models: list[str] = []
missing_required_fields: list[dict[str, str]] = []
missing_optional_fields: list[dict[str, str]] = []
for model_name, fields in required_fields.items():
    if model_name not in env:
        missing_models.append(model_name)
        continue
    model_fields = env[model_name]._fields
    for field_name in fields:
        if field_name not in model_fields:
            missing_required_fields.append({"model": model_name, "field": field_name})
for model_name, fields in optional_fields.items():
    if model_name not in env:
        continue
    model_fields = env[model_name]._fields
    for field_name in fields:
        if field_name not in model_fields:
            missing_optional_fields.append({"model": model_name, "field": field_name})

Partner = env["res.partner"].sudo()
Project = env["project.project"].sudo()

partner_collisions = 0
for row in partner_rows:
    if Partner.search_count(
        [
            ("legacy_partner_source", "=", clean(row.get("legacy_partner_source"))),
            ("legacy_partner_id", "=", clean(row.get("legacy_partner_id"))),
        ]
    ):
        partner_collisions += 1

project_collisions = 0
for row in project_rows:
    if Project.search_count([("legacy_project_id", "=", clean(row.get("legacy_project_id")))]):
        project_collisions += 1

contract_partner_collisions = 0
for row in contract_partner_rows:
    if Partner.search_count([("name", "=", clean(row.get("name")))]):
        contract_partner_collisions += 1

current_counts = {
    "res.partner": Partner.search_count([]),
    "project.project": Project.search_count([]),
    "construction.contract": env["construction.contract"].sudo().search_count([]) if "construction.contract" in env else None,
    "sc.project.member.staging": env["sc.project.member.staging"].sudo().search_count([]) if "sc.project.member.staging" in env else None,
}

status = "PASS" if not missing_models and not missing_required_fields else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_replay_payload_precheck",
    "database": env.cr.dbname,
    "db_writes": 0,
    "database_operations": 0,
    "write_scripts_executed": 0,
    "payload_rows": {
        "partner_l4": len(partner_rows),
        "project_anchor": len(project_rows),
        "contract_partner_12": len(contract_partner_rows),
    },
    "missing_models": missing_models,
    "missing_required_fields": missing_required_fields,
    "missing_optional_fields": missing_optional_fields,
    "identity_collisions": {
        "partner_l4": partner_collisions,
        "project_anchor": project_collisions,
        "contract_partner_12": contract_partner_collisions,
    },
    "current_counts": current_counts,
    "decision": "fresh_db_replay_payloads_precheck_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
    "next_step": "execute bounded replay writes in dependency order: partner anchors, project anchors, contract partner 12 anchors",
}
write_json(OUTPUT_JSON, payload)
write_report(payload)
print(
    "FRESH_DB_REPLAY_PAYLOAD_PRECHECK="
    + json.dumps(
        {
            "status": status,
            "database": env.cr.dbname,
            "partner_l4_rows": len(partner_rows),
            "project_anchor_rows": len(project_rows),
            "contract_partner_12_rows": len(contract_partner_rows),
            "missing_models": len(missing_models),
            "missing_required_fields": len(missing_required_fields),
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
