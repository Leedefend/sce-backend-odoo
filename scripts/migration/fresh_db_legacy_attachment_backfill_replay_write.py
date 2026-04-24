#!/usr/bin/env python3
"""Replay legacy attachment backfill URL relations into allowed replay databases."""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


LEGACY_FILE_ID_RE = re.compile(r"legacy_file_id=([0-9a-fA-F-]+)")
LEGACY_ACTUAL_OUTFLOW_ID_RE = re.compile(r"legacy_actual_outflow_id=([0-9a-fA-F]+)")
LEGACY_SUPPLIER_CONTRACT_LINE_ID_RE = re.compile(r"legacy_supplier_contract_id=([0-9a-fA-F]+)")


def suffix_from_ref(res_ref: str, prefix: str) -> str:
    value = (res_ref or "").strip()
    if value.startswith(prefix):
        return value.removeprefix(prefix)
    return ""


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_attachment_backfill_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Attachment = env["ir.attachment"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
ProjectMember = env["sc.project.member.staging"].sudo().with_context(active_test=False)  # noqa: F821
Request = env["payment.request"].sudo()  # noqa: F821
RequestLine = env["payment.request.line"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821
ContractLine = env["construction.contract.line"].sudo()  # noqa: F821

project_ids = sorted({suffix_from_ref(row["res_ref"], "legacy_project_sc_") for row in rows if row.get("res_ref", "").startswith("legacy_project_sc_")})
project_ids = [item for item in project_ids if item]
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_ids)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}

member_ids = sorted({suffix_from_ref(row["res_ref"], "legacy_project_member_sc_") for row in rows if row.get("res_ref", "").startswith("legacy_project_member_sc_")})
member_ids = [item for item in member_ids if item]
member_map = {
    rec["legacy_member_id"]: rec["id"]
    for rec in ProjectMember.search_read([("legacy_member_id", "in", member_ids)], ["legacy_member_id"])
    if rec.get("legacy_member_id")
}

request_line_ids = sorted({suffix_from_ref(row["res_ref"], "legacy_outflow_request_line_sc_") for row in rows if row.get("res_ref", "").startswith("legacy_outflow_request_line_sc_")})
request_line_ids = [item for item in request_line_ids if item]
request_line_map = {
    rec["legacy_line_id"]: rec["id"]
    for rec in RequestLine.search_read([("legacy_line_id", "in", request_line_ids)], ["legacy_line_id"])
    if rec.get("legacy_line_id")
}

contract_ids = sorted(
    {
        suffix_from_ref(row["res_ref"], "legacy_supplier_contract_sc_") or suffix_from_ref(row["res_ref"], "legacy_supplier_contract_line_sc_")
        for row in rows
        if row.get("res_ref", "").startswith("legacy_supplier_contract_sc_")
        or row.get("res_ref", "").startswith("legacy_supplier_contract_line_sc_")
    }
)
contract_ids = [item for item in contract_ids if item]
contract_map = {
    rec["legacy_contract_id"]: rec["id"]
    for rec in Contract.search_read([("legacy_contract_id", "in", contract_ids)], ["legacy_contract_id"])
    if rec.get("legacy_contract_id")
}

actual_outflow_map: dict[str, int] = {}
for rec in Request.search_read([("note", "ilike", "[migration:actual_outflow_core]")], ["note"]):
    note = rec.get("note") or ""
    match = LEGACY_ACTUAL_OUTFLOW_ID_RE.search(note)
    if match:
        actual_outflow_map[match.group(1)] = rec["id"]

contract_line_map: dict[str, int] = {}
if contract_ids:
    contract_db_ids = list(contract_map.values())
    if contract_db_ids:
        for rec in ContractLine.search_read([("contract_id", "in", contract_db_ids), ("note", "ilike", "[migration:supplier_contract_summary_line]")], ["note"]):
            note = rec.get("note") or ""
            match = LEGACY_SUPPLIER_CONTRACT_LINE_ID_RE.search(note)
            if match:
                contract_line_map[match.group(1)] = rec["id"]

existing_descriptions = set()
for rec in Attachment.search_read([("description", "ilike", "[migration:legacy_attachment_backfill]")], ["description"]):
    description = rec.get("description") or ""
    if description:
        existing_descriptions.add(description)


def resolve_res_id(row: dict[str, str]) -> int:
    res_ref = row.get("res_ref", "")
    if res_ref.startswith("legacy_project_sc_"):
        legacy_id = suffix_from_ref(res_ref, "legacy_project_sc_")
        res_id = project_map.get(legacy_id)
        if not res_id:
            raise RuntimeError({"missing_project_anchor": res_ref, "external_id": row["external_id"]})
        return res_id
    if res_ref.startswith("legacy_project_member_sc_"):
        legacy_id = suffix_from_ref(res_ref, "legacy_project_member_sc_")
        res_id = member_map.get(legacy_id)
        if not res_id:
            raise RuntimeError({"missing_project_member_anchor": res_ref, "external_id": row["external_id"]})
        return res_id
    if res_ref.startswith("legacy_actual_outflow_sc_"):
        legacy_id = suffix_from_ref(res_ref, "legacy_actual_outflow_sc_")
        res_id = actual_outflow_map.get(legacy_id)
        if not res_id:
            raise RuntimeError({"missing_actual_outflow_anchor": res_ref, "external_id": row["external_id"]})
        return res_id
    if res_ref.startswith("legacy_outflow_request_line_sc_"):
        legacy_id = suffix_from_ref(res_ref, "legacy_outflow_request_line_sc_")
        res_id = request_line_map.get(legacy_id)
        if not res_id:
            raise RuntimeError({"missing_outflow_request_line_anchor": res_ref, "external_id": row["external_id"]})
        return res_id
    if res_ref.startswith("legacy_supplier_contract_sc_"):
        legacy_id = suffix_from_ref(res_ref, "legacy_supplier_contract_sc_")
        res_id = contract_map.get(legacy_id)
        if not res_id:
            raise RuntimeError({"missing_supplier_contract_anchor": res_ref, "external_id": row["external_id"]})
        return res_id
    if res_ref.startswith("legacy_supplier_contract_line_sc_"):
        legacy_id = suffix_from_ref(res_ref, "legacy_supplier_contract_line_sc_")
        res_id = contract_line_map.get(legacy_id)
        if not res_id:
            raise RuntimeError({"missing_supplier_contract_line_anchor": res_ref, "external_id": row["external_id"]})
        return res_id
    raise RuntimeError({"unsupported_attachment_target_ref": res_ref, "external_id": row["external_id"]})


created = 0
skipped = 0
buffer: list[dict[str, object]] = []
batch_size = 500
for row in rows:
    description = row.get("description") or ""
    if description and description in existing_descriptions:
        skipped += 1
        continue
    vals = {
        "name": row.get("name") or False,
        "type": row.get("type") or "url",
        "url": row.get("url") or False,
        "res_model": row.get("res_model") or False,
        "res_id": resolve_res_id(row),
        "mimetype": row.get("mimetype") or False,
        "description": description or False,
    }
    buffer.append(vals)
    if description:
        existing_descriptions.add(description)
    if len(buffer) >= batch_size:
        Attachment.create(buffer)
        created += len(buffer)
        buffer = []

if buffer:
    Attachment.create(buffer)
    created += len(buffer)

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_legacy_attachment_backfill_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "db_writes": created,
    "decision": "legacy_attachment_backfill_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_ATTACHMENT_BACKFILL_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
