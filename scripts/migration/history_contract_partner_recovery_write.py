#!/usr/bin/env python3
"""Replay contract headers recovered through partner-master / strong-evidence mapping."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/history_contract_partner_recovery_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_partner(row, partner_model):
    legacy_source = clean(row.get("partner_legacy_source"))
    legacy_id = clean(row.get("partner_legacy_id"))
    partner_name = clean(row.get("partner_name"))
    partner = partner_model.search(
        [("legacy_partner_source", "=", legacy_source), ("legacy_partner_id", "=", legacy_id)],
        limit=2,
    )
    if len(partner) == 1:
        return partner.id
    if len(partner) > 1:
        raise RuntimeError(
            {
                "error": "duplicate_partner_match",
                "partner_legacy_source": legacy_source,
                "partner_legacy_id": legacy_id,
                "partner_ids": partner.ids,
            }
        )
    if partner_name:
        name_match = partner_model.search([("name", "=", partner_name)], limit=2)
        if len(name_match) == 1:
            return name_match.id
        if len(name_match) > 1:
            raise RuntimeError({"error": "duplicate_partner_name_match", "partner_name": partner_name, "partner_ids": name_match.ids})
    return None


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/history_contract_partner_recovery_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_contract_partner_recovery_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_contract_partner_recovery_rollback_targets_v1.csv"
EXPECTED_ROWS = 23

ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

rows = read_csv(PAYLOAD_CSV)
ids = [clean(row.get("legacy_contract_id")) for row in rows]
duplicates = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)
existing = Contract.search([("legacy_contract_id", "in", ids)], order="legacy_contract_id,id")
errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})
if duplicates:
    errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicates})
if existing:
    errors.append({"error": "pre_existing_contracts", "count": len(existing), "samples": [{"contract_id": rec.id, "legacy_contract_id": rec.legacy_contract_id or ""} for rec in existing[:20]]})

create_vals = []
for row in rows:
    vals = {
        "legacy_contract_id": clean(row.get("legacy_contract_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "subject": clean(row.get("subject")),
        "type": clean(row.get("type")),
        "legacy_contract_no": clean(row.get("legacy_contract_no")),
        "legacy_document_no": clean(row.get("legacy_document_no")),
        "legacy_external_contract_no": clean(row.get("legacy_external_contract_no")),
        "legacy_status": clean(row.get("legacy_status")),
        "legacy_deleted_flag": clean(row.get("legacy_deleted_flag")),
        "legacy_counterparty_text": clean(row.get("legacy_counterparty_text")),
        "recovery_family": clean(row.get("recovery_family")),
    }
    project = Project.search([("legacy_project_id", "=", vals["legacy_project_id"])], limit=2)
    if len(project) == 1:
        vals["project_id"] = project.id
    elif len(project) > 1:
        errors.append({"error": "duplicate_project_match", "legacy_contract_id": vals["legacy_contract_id"], "legacy_project_id": vals["legacy_project_id"], "project_ids": project.ids})
    else:
        errors.append({"error": "project_missing", "legacy_contract_id": vals["legacy_contract_id"], "legacy_project_id": vals["legacy_project_id"]})

    try:
        partner_id = resolve_partner(row, Partner)
    except RuntimeError as exc:
        errors.append({"legacy_contract_id": vals["legacy_contract_id"], **(exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {"error": "partner_resolution_runtime_error"})})
        partner_id = None
    if partner_id:
        vals["partner_id"] = partner_id
    else:
        errors.append(
            {
                "error": "partner_missing",
                "legacy_contract_id": vals["legacy_contract_id"],
                "partner_legacy_source": clean(row.get("partner_legacy_source")),
                "partner_legacy_id": clean(row.get("partner_legacy_id")),
                "partner_name": clean(row.get("partner_name")),
            }
        )
    create_vals.append(vals)

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:80]})

created_rows = []
try:
    for vals in create_vals:
        recovery_family = vals.pop("recovery_family", "")
        rec = Contract.create(vals)
        created_rows.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
                "recovery_family": recovery_family,
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

write_csv(
    ROLLBACK_CSV,
    ["contract_id", "legacy_contract_id", "legacy_project_id", "project_id", "partner_id", "name", "subject", "type", "state", "recovery_family"],
    created_rows,
)
payload = {
    "status": "PASS",
    "mode": "history_contract_partner_recovery_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "rollback_rows": len(created_rows),
    "artifacts": {"rollback_csv": str(ROLLBACK_CSV)},
}
write_json(OUTPUT_JSON, payload)
print(json.dumps(payload, ensure_ascii=False, indent=2))
