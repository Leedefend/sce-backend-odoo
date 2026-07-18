#!/usr/bin/env python3
"""Host-side read-only SQL and filestore fingerprint for pre/post upgrade."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


TABLES = {
    "companies": "res_company",
    "users": "res_users",
    "partners": "res_partner",
    "projects": "project_project",
    "contracts": "construction_contract",
    "settlements": "sc_settlement_order",
    "payment_requests": "payment_request",
    "payment_executions": "sc_payment_execution",
    "ledgers": "payment_ledger",
    "attachments": "ir_attachment",
    "config_contracts": "ui_business_config_contract",
    "config_versions": "ui_business_config_contract_version",
    "low_code_change_sets": "ui_business_config_change_set",
}
AMOUNTS = {
    "construction_contract": ("amount_total", "amount", "contract_amount"),
    "sc_settlement_order": ("amount_total", "settlement_amount", "amount"),
    "payment_request": ("amount", "amount_total"),
    "sc_payment_execution": ("amount", "actual_amount", "paid_amount"),
    "payment_ledger": ("amount", "amount_total"),
}
RELATIONS = {
    "construction_contract": ("project_id",),
    "sc_settlement_order": ("contract_id", "project_id"),
    "payment_request": ("settlement_id", "contract_id", "project_id", "partner_id"),
    "sc_payment_execution": ("payment_request_id",),
    "payment_ledger": ("payment_request_id",),
}

project = os.environ["FINGERPRINT_PROJECT"]
compose_file = os.environ["FINGERPRINT_COMPOSE_FILE"]
database = os.environ["FINGERPRINT_DB"]
db_user = os.environ["DB_USER"]
filestore_mode = os.environ.get("FINGERPRINT_FILESTORE_MODE", "exec")
out_path = Path(os.environ["FINGERPRINT_OUTPUT"])
compose = ["docker", "compose", "-p", project, "-f", compose_file]


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()


def sql(statement: str) -> str:
    return run([*compose, "exec", "-T", "db", "psql", "-U", db_user, "-d", database, "-Atc", statement])


def table_exists(table: str) -> bool:
    return sql(f"SELECT to_regclass('public.{table}') IS NOT NULL").lower() == "t"


def column_exists(table: str, column: str) -> bool:
    return sql(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        f"WHERE table_schema='public' AND table_name='{table}' AND column_name='{column}')"
    ).lower() == "t"


counts = {}
id_digests = {}
for label, table in TABLES.items():
    if not table_exists(table):
        counts[label] = None
        id_digests[label] = None
        continue
    counts[label] = int(sql(f"SELECT count(*) FROM {table}"))
    id_digests[label] = sql(f"SELECT md5(COALESCE(string_agg(id::text, ',' ORDER BY id), '')) FROM {table}")

amounts = {}
for table, candidates in AMOUNTS.items():
    if not table_exists(table):
        amounts[table] = None
        continue
    field = next((name for name in candidates if column_exists(table, name)), None)
    value = sql(f"SELECT COALESCE(round(sum({field})::numeric, 2), 0) FROM {table}") if field else "0"
    amounts[table] = {"field": field, "sum": value}

missing_relations = {}
warnings = []
for table, fields in RELATIONS.items():
    if not table_exists(table):
        missing_relations[table] = None
        continue
    missing_relations[table] = {}
    for field in fields:
        if not column_exists(table, field):
            continue
        missing = int(sql(f"SELECT count(*) FROM {table} WHERE {field} IS NULL"))
        missing_relations[table][field] = missing
        if missing:
            warnings.append({"code": "missing_relation", "reference": f"{table}.{field}", "count": missing})

for table in AMOUNTS:
    if not table_exists(table):
        continue
    currency_field = next((field for field in ("currency_id", "company_currency_id") if column_exists(table, field)), None)
    if currency_field:
        missing = int(sql(f"SELECT count(*) FROM {table} WHERE {currency_field} IS NULL"))
        if missing:
            warnings.append({"code": "missing_currency", "reference": f"{table}.{currency_field}", "count": missing})

modules = []
if table_exists("ir_module_module"):
    version_column = "installed_version" if column_exists("ir_module_module", "installed_version") else "latest_version"
    raw = sql(
        "SELECT COALESCE(json_agg(row_to_json(x))::text, '[]') FROM "
        f"(SELECT name,state,COALESCE({version_column},'') AS installed_version "
        "FROM ir_module_module WHERE name LIKE 'smart_%' ORDER BY name) x"
    )
    modules = json.loads(raw)

filestore_command = (
    f"root='/var/lib/odoo/filestore/{database}'; "
    "count=$(find \"$root\" -type f 2>/dev/null | wc -l); "
    "bytes=$(find \"$root\" -type f -printf '%s\\n' 2>/dev/null | awk '{s+=$1} END {print s+0}'); "
    "digest=$(find \"$root\" -type f -printf '%P\\n' 2>/dev/null | sort | while read p; do "
    "printf '%s\\0' \"$p\"; sha256sum \"$root/$p\" | awk '{print $1}'; done | sha256sum | awk '{print $1}'); "
    "printf '%s|%s|%s\\n' \"$count\" \"$bytes\" \"$digest\""
)
if filestore_mode == "exec":
    filestore_raw = run([*compose, "exec", "-T", "odoo", "sh", "-c", filestore_command])
else:
    filestore_raw = run([*compose, "run", "--rm", "--no-deps", "-T", "--entrypoint", "sh", "odoo", "-c", filestore_command])
file_count, file_bytes, file_digest = filestore_raw.split("|")[-3:]

payload = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "database": database,
    "mode": "sql_and_filestore_read_only_redacted",
    "database_bytes": int(sql(f"SELECT pg_database_size('{database}')")),
    "counts": counts,
    "id_digests": id_digests,
    "amounts": amounts,
    "missing_relations": missing_relations,
    "known_historical_warnings": warnings,
    "known_historical_warning_count": len(warnings),
    "filestore": {"file_count": int(file_count), "bytes": int(file_bytes), "sha256": file_digest},
    "modules": modules,
    "pending_modules": [row["name"] for row in modules if row["state"] in {"to install", "to upgrade", "to remove"}],
    "demo_module_state": next((row["state"] for row in modules if row["name"] == "smart_construction_demo"), "uninstalled"),
    "sensitive_values_included": False,
    "database_write_count": 0,
}
canonical = dict(payload)
canonical.pop("generated_at")
canonical.pop("database")
canonical.pop("modules")
canonical.pop("pending_modules")
canonical.pop("database_bytes")
payload["business_fingerprint_sha256"] = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
print(f"[candidate.sql_fingerprint] PASS db={database} fingerprint={payload['business_fingerprint_sha256']} warnings={len(warnings)}")
