#!/usr/bin/env python3
"""Replay legacy invoice surcharge facts into allowed replay databases."""

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
        if (candidate / "artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv").exists():
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


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def as_float(value: object) -> float:
    text = clean(value)
    return float(text) if text else 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        fallback.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_date(value: object) -> str | bool:
    return clean(value) or False


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv"
INPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_legacy_invoice_surcharge_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])

Model = env["sc.legacy.invoice.surcharge.fact"].sudo().with_context(active_test=False)  # noqa: F821
Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821

project_legacy_ids = sorted({clean(row.get("project_legacy_id")) for row in rows if clean(row.get("project_legacy_id"))})
project_map = {
    rec["legacy_project_id"]: rec["id"]
    for rec in Project.search_read([("legacy_project_id", "in", project_legacy_ids)], ["legacy_project_id"])
    if rec.get("legacy_project_id")
}
partner_legacy_ids = sorted({clean(row.get("partner_legacy_id")) for row in rows if clean(row.get("partner_legacy_id"))})
partner_map = {
    rec["legacy_partner_id"]: rec["id"]
    for rec in Partner.search_read([("legacy_partner_id", "in", partner_legacy_ids)], ["legacy_partner_id"])
    if rec.get("legacy_partner_id")
}
partner_names = sorted({clean(row.get("partner_name")) for row in rows if clean(row.get("partner_name"))})
partner_name_map = {}
for rec in Partner.search_read([("name", "in", partner_names)], ["name"]):
    name = clean(rec.get("name"))
    if name and name not in partner_name_map:
        partner_name_map[name] = rec["id"]

existing_keys = {
    (rec["direction"], clean(rec["legacy_line_id"]))
    for rec in Model.search_read([("legacy_line_id", "!=", False)], ["direction", "legacy_line_id"])
}

created = 0
updated = 0
missing_project = 0
missing_partner = 0
for row in rows:
    direction = clean(row.get("direction"))
    legacy_line_id = clean(row.get("legacy_line_id"))
    project_id = project_map.get(clean(row.get("project_legacy_id")))
    partner_id = partner_map.get(clean(row.get("partner_legacy_id"))) or partner_name_map.get(clean(row.get("partner_name")))
    if not project_id:
        missing_project += 1
    if not partner_id:
        missing_partner += 1
    vals = {
        "direction": direction,
        "legacy_line_id": legacy_line_id,
        "legacy_header_id": clean(row.get("legacy_header_id")),
        "source_table": clean(row.get("source_table")),
        "document_no": clean(row.get("document_no")),
        "document_date": parse_date(row.get("document_date")),
        "document_state": clean(row.get("document_state")),
        "deleted_flag": clean(row.get("deleted_flag")),
        "project_legacy_id": clean(row.get("project_legacy_id")),
        "project_name": clean(row.get("project_name")),
        "project_id": project_id or False,
        "partner_legacy_id": clean(row.get("partner_legacy_id")),
        "partner_name": clean(row.get("partner_name")),
        "partner_credit_code": clean(row.get("partner_credit_code")),
        "partner_id": partner_id or False,
        "invoice_no": clean(row.get("invoice_no")),
        "invoice_date": parse_date(row.get("invoice_date")),
        "surcharge_amount": as_float(row.get("surcharge_amount")),
        "import_batch": clean(row.get("import_batch")) or "legacy_invoice_surcharge_v1",
        "active": True,
    }
    key = (direction, legacy_line_id)
    if key in existing_keys:
        rec = Model.search([("direction", "=", direction), ("legacy_line_id", "=", legacy_line_id)], limit=1)
        rec.write(vals)
        updated += 1
    else:
        Model.create(vals)
        existing_keys.add(key)
        created += 1

env.cr.commit()  # noqa: F821
status = "PASS" if created + updated == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_legacy_invoice_surcharge_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "updated_rows": updated,
    "missing_project": missing_project,
    "missing_partner": missing_partner,
    "db_writes": created + updated,
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_LEGACY_INVOICE_SURCHARGE_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
