#!/usr/bin/env python3
"""Replay ready unreached contract headers into allowed DBs."""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/history_contract_unreached_ready_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/history_contract_unreached_ready_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "history_contract_unreached_ready_replay_write_result_v1.json"
ROLLBACK_CSV = ARTIFACT_ROOT / "history_contract_unreached_ready_replay_rollback_targets_v1.csv"
EXPECTED_ROWS = 56
ORG_SUFFIXES = ("有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "公司")


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()


def norm_name(value: object) -> str:
    text = re.sub(r"[（）()·,，.。/、\s\\-]", "", clean(value))
    for suffix in ORG_SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text


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


def resolve_project_id(row, project_model):
    legacy_project_id = clean(row.get("legacy_project_id"))
    if legacy_project_id:
        matches = project_model.search([("legacy_project_id", "=", legacy_project_id)], limit=2)
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            raise RuntimeError({"duplicate_legacy_project_matches": legacy_project_id, "project_ids": matches.ids})
    return None


def resolve_partner_id(row, partner_model):
    partner_text = clean(row.get("legacy_counterparty_text"))
    if partner_text:
        matches = partner_model.search([("name", "=", partner_text)], limit=2)
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            raise RuntimeError({"duplicate_partner_name_matches": partner_text, "partner_ids": matches.ids})
        normalized_target = norm_name(partner_text)
        if normalized_target:
            normalized_matches = partner_model.search([]).filtered(lambda rec: norm_name(rec.name) == normalized_target)
            if len(normalized_matches) == 1:
                return normalized_matches.id
            if len(normalized_matches) > 1:
                raise RuntimeError(
                    {
                        "duplicate_partner_normalized_matches": partner_text,
                        "normalized_target": normalized_target,
                        "partner_ids": normalized_matches.ids,
                    }
                )
    return None


ensure_allowed_db()

Contract = env["construction.contract"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

rows = read_csv(PAYLOAD_CSV)
ids = [clean(row.get("legacy_contract_id")) for row in rows]
duplicate_ids = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)
existing = Contract.search([("legacy_contract_id", "in", ids)], order="legacy_contract_id,id")

errors: list[dict[str, object]] = []
if len(rows) != EXPECTED_ROWS:
    errors.append({"error": "unexpected_row_count", "actual": len(rows), "expected": EXPECTED_ROWS})
if duplicate_ids:
    errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicate_ids})
if existing:
    errors.append(
        {
            "error": "pre_existing_contracts",
            "count": len(existing),
            "samples": [{"contract_id": rec.id, "legacy_contract_id": rec.legacy_contract_id or ""} for rec in existing[:20]],
        }
    )

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
    }
    project_id = resolve_project_id(row, Project)
    partner_id = resolve_partner_id(row, Partner)
    if project_id:
        vals["project_id"] = project_id
    if partner_id:
        vals["partner_id"] = partner_id
    if not vals.get("project_id"):
        errors.append({"error": "project_missing", "legacy_contract_id": vals["legacy_contract_id"], "legacy_project_id": vals["legacy_project_id"]})
    if not vals.get("partner_id"):
        errors.append({"error": "partner_missing", "legacy_contract_id": vals["legacy_contract_id"], "legacy_counterparty_text": vals["legacy_counterparty_text"]})
    create_vals.append(vals)

if errors:
    env.cr.rollback()  # noqa: F821
    raise RuntimeError({"precheck_failed": errors[:80]})

created_rows = []
try:
    for vals in create_vals:
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
            }
        )
    env.cr.commit()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

write_csv(
    ROLLBACK_CSV,
    ["contract_id", "legacy_contract_id", "legacy_project_id", "project_id", "partner_id", "name", "subject", "type", "state"],
    created_rows,
)
payload = {
    "status": "PASS",
    "mode": "history_contract_unreached_ready_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": len(created_rows),
    "rollback_rows": len(created_rows),
    "artifacts": {"rollback_csv": str(ROLLBACK_CSV)},
}
write_json(OUTPUT_JSON, payload)
print(json.dumps(payload, ensure_ascii=False, indent=2))
