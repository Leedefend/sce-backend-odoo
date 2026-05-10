#!/usr/bin/env python3
"""Backfill source creator/time onto runtime business fact records.

This writes only objective source-table evidence from legacy rows. It does not
use Odoo create_uid/create_date and does not infer operator values from names.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
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
DEFAULT_INPUT_CSV = REPO_ROOT / "artifacts/migration/partner_source_creator_from_legacy_mssql_v1.csv"
INPUT_CSVS = [
    Path(item.strip())
    for item in os.getenv("BUSINESS_FACT_SOURCE_CREATOR_CSVS", os.getenv("PARTNER_SOURCE_CREATOR_CSVS", str(DEFAULT_INPUT_CSV))).split(",")
    if item.strip()
]
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/business_fact_source_creator_backfill_v1"),
    )
)
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}
TECHNICAL_CREATED_BY_VALUES = {"odoobot", "administrator", "admin", "system", "系统", "系统导入"}
TECHNICAL_CREATED_AT_PREFIXES = ("2026-05-08", "2026-05-09")


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def is_login_like(value: object) -> bool:
    text = clean(value)
    if not text or re.search(r"[\u4e00-\u9fff]", text):
        return False
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.@-]{1,63}", text))


def should_overwrite_text(value: object) -> bool:
    text = clean(value)
    return not text or text.lower() in TECHNICAL_CREATED_BY_VALUES or text in TECHNICAL_CREATED_BY_VALUES or is_login_like(text)


def should_overwrite_time(value: object) -> bool:
    text = clean(value)
    return not text or text.startswith(TECHNICAL_CREATED_AT_PREFIXES)


def normalize_datetime(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    if "." in text:
        text = text.split(".", 1)[0]
    return text[:19]


def user_display_name_maps() -> tuple[dict[str, str], dict[str, str]]:
    by_login: dict[str, str] = {}
    by_legacy_id: dict[str, str] = {}
    Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    for user in Users.search([]):
        login = clean(user.login).lower()
        name = clean(user.name)
        if login and name and login != name.lower() and name.lower() not in TECHNICAL_CREATED_BY_VALUES:
            by_login[login] = name
    if "sc.legacy.user.profile" in env.registry:  # noqa: F821
        Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
        for profile in Profile.search([]):
            name = clean(profile.display_name) or clean(profile.user_id.name)
            if not name or name.lower() in TECHNICAL_CREATED_BY_VALUES:
                continue
            legacy_id = clean(profile.legacy_user_id)
            if legacy_id:
                by_legacy_id[legacy_id] = name
            for raw_login in (profile.source_login, profile.generated_login):
                login = clean(raw_login).lower()
                if login:
                    by_login.setdefault(login, name)
    return by_login, by_legacy_id


USER_BY_LOGIN, USER_BY_LEGACY_ID = user_display_name_maps()


def normalize_creator(name: object, legacy_user_id: object = "") -> str:
    legacy_id = clean(legacy_user_id)
    if legacy_id and legacy_id in USER_BY_LEGACY_ID:
        return USER_BY_LEGACY_ID[legacy_id]
    text = clean(name)
    if not text or text.lower() in TECHNICAL_CREATED_BY_VALUES or text in TECHNICAL_CREATED_BY_VALUES:
        return ""
    mapped = USER_BY_LOGIN.get(text.lower())
    if mapped:
        return mapped
    if is_login_like(text):
        return ""
    return text


def read_csvs(paths: list[Path]) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    for path in paths:
        if not path.exists():
            counts[str(path)] = 0
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            path_rows = [dict(row) for row in csv.DictReader(handle)]
        rows.extend(path_rows)
        counts[str(path)] = len(path_rows)
    return rows, counts


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed() -> None:
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821


def source_identity(row: dict[str, str]) -> tuple[str, str]:
    return clean(row.get("source_table")), clean(row.get("legacy_record_id"))


def fact_specs():
    specs = [
        ("sc.receipt.income", "legacy_source_table", "legacy_record_id"),
        ("sc.payment.execution", "legacy_source_table", "legacy_record_id"),
        ("sc.legacy.enterprise.business.fact", "legacy_source_table", "legacy_record_id"),
        ("sc.legacy.scbs.fact.staging", "source_table", "legacy_record_id"),
        ("sc.legacy.receipt.income.fact", "legacy_source_table", "legacy_record_id"),
        ("sc.legacy.receipt.residual.fact", "source_table", "legacy_record_id"),
        ("sc.legacy.payment.residual.fact", "source_table", "legacy_record_id"),
        ("sc.legacy.fund.confirmation.line", "source_table", "legacy_line_id"),
    ]
    for model_name, table_field, record_field in specs:
        if model_name not in env.registry:  # noqa: F821
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        required_fields = {
            table_field,
            record_field,
            "creator_legacy_user_id",
            "creator_name",
            "created_time",
        }
        if required_fields.issubset(Model._fields):
            yield Model, table_field, record_field


def source_values(row: dict[str, str]) -> dict[str, object]:
    creator = normalize_creator(row.get("creator_name"), row.get("creator_legacy_user_id"))
    created_time = normalize_datetime(row.get("created_time"))
    values: dict[str, object] = {}
    legacy_user_id = clean(row.get("creator_legacy_user_id"))
    if legacy_user_id:
        values["creator_legacy_user_id"] = legacy_user_id
    if creator:
        values["creator_name"] = creator
    if created_time:
        values["created_time"] = created_time
    return values


def record_update_values(record, values: dict[str, object]) -> dict[str, object]:
    update: dict[str, object] = {}
    if values.get("creator_legacy_user_id") and should_overwrite_text(record.creator_legacy_user_id):
        update["creator_legacy_user_id"] = values["creator_legacy_user_id"]
    if values.get("creator_name") and should_overwrite_text(record.creator_name):
        update["creator_name"] = values["creator_name"]
    if values.get("created_time") and should_overwrite_time(record.created_time):
        update["created_time"] = values["created_time"]
    return update


def payment_request_source_key(note: object) -> tuple[str, str]:
    note_text = clean(note)
    for source_table, token in (
        ("C_JFHKLR", "legacy_receipt_id"),
        ("C_ZFSQGL", "legacy_outflow_id"),
        ("T_FK_Supplier", "legacy_actual_outflow_id"),
    ):
        match = re.search(r"%s=([^;\\s]+)" % token, note_text)
        if match:
            return source_table, match.group(1).strip()
    return "", ""


ensure_allowed()
rows, input_counts = read_csvs(INPUT_CSVS)
source_rows_by_key = {source_identity(row): row for row in rows if all(source_identity(row)) and source_values(row)}
tables = sorted({key[0] for key in source_rows_by_key})
record_ids = sorted({key[1] for key in source_rows_by_key})

updates: list[dict[str, object]] = []
misses: list[dict[str, object]] = []
route_counts: Counter[str] = Counter()
field_update_counts: Counter[str] = Counter()

try:
    for Model, table_field, record_field in fact_specs():
        for record in Model.search([(table_field, "in", tables), (record_field, "in", record_ids)]):
            key = (clean(record[table_field]), clean(record[record_field]))
            row = source_rows_by_key.get(key)
            if not row:
                continue
            vals = record_update_values(record, source_values(row))
            if not vals:
                continue
            if MODE == "write":
                record.write(vals)
            route_counts[Model._name] += 1
            for field in vals:
                field_update_counts[field] += 1
            updates.append({"model": Model._name, "record_id": record.id, "source_table": key[0], "legacy_record_id": key[1], "updated_fields": ";".join(sorted(vals))})

    if "payment.request" in env.registry:  # noqa: F821
        Request = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
        if {"legacy_source_table", "legacy_record_id", "creator_legacy_user_id", "creator_name", "created_time"}.issubset(Request._fields):
            for request in Request.search([("note", "ilike", "legacy_"), ("partner_id", "!=", False)]):
                key = payment_request_source_key(request.note)
                row = source_rows_by_key.get(key)
                if not row:
                    continue
                values = source_values(row)
                vals = {}
                if key[0] and should_overwrite_text(request.legacy_source_table):
                    vals["legacy_source_table"] = key[0]
                if key[1] and should_overwrite_text(request.legacy_record_id):
                    vals["legacy_record_id"] = key[1]
                vals.update(record_update_values(request, values))
                if not vals:
                    continue
                if MODE == "write":
                    request.write(vals)
                route_counts["payment.request.note"] += 1
                for field in vals:
                    field_update_counts[field] += 1
                updates.append({"model": "payment.request", "record_id": request.id, "source_table": key[0], "legacy_record_id": key[1], "updated_fields": ";".join(sorted(vals))})

    if MODE == "write":
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

matched_keys = {(clean(row["source_table"]), clean(row["legacy_record_id"])) for row in updates}
for key in sorted(set(source_rows_by_key) - matched_keys)[:1000]:
    row = source_rows_by_key[key]
    misses.append({"source_table": key[0], "legacy_record_id": key[1], "creator_name": normalize_creator(row.get("creator_name"), row.get("creator_legacy_user_id")), "created_time": normalize_datetime(row.get("created_time"))})

run_id = datetime.now(timezone.utc).strftime("business_fact_source_creator_backfill_%Y%m%dT%H%M%SZ")
output_root = ARTIFACT_ROOT / run_id
write_csv(
    output_root / "business_fact_source_creator_backfill_rows_v1.csv",
    ["model", "record_id", "source_table", "legacy_record_id", "updated_fields"],
    updates,
)
write_csv(
    output_root / "business_fact_source_creator_backfill_misses_v1.csv",
    ["source_table", "legacy_record_id", "creator_name", "created_time"],
    misses,
)
summary = {
    "status": "PASS",
    "mode": "business_fact_source_creator_backfill",
    "write_mode": MODE,
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "input_counts": input_counts,
    "source_key_count": len(source_rows_by_key),
    "fact_rows_to_update": len(updates),
    "miss_count": len(misses),
    "route_counts": dict(sorted(route_counts.items())),
    "field_update_counts": dict(sorted(field_update_counts.items())),
    "db_write": MODE == "write",
    "output_root": str(output_root),
}
write_json(output_root / "business_fact_source_creator_backfill_result_v1.json", summary)
print("BUSINESS_FACT_SOURCE_CREATOR_BACKFILL=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
