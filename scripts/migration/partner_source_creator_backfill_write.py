#!/usr/bin/env python3
"""Backfill partner source creator fields from legacy source-table evidence.

This is intentionally source-key based. It does not use Odoo create_uid or
create_date, and it does not infer creator values from partner names.
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
    for item in os.getenv("PARTNER_SOURCE_CREATOR_CSVS", str(DEFAULT_INPUT_CSV)).split(",")
    if item.strip()
]
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/partner_source_creator_backfill_v1"),
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


def should_overwrite_created_by(value: object) -> bool:
    text = clean(value)
    return not text or text.lower() in TECHNICAL_CREATED_BY_VALUES or text in TECHNICAL_CREATED_BY_VALUES or is_login_like(text)


def should_overwrite_created_at(value: object) -> bool:
    text = clean(value)
    return not text or text.startswith(TECHNICAL_CREATED_AT_PREFIXES)


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
        ("sc.receipt.income", "legacy_source_table", "legacy_record_id", "partner_id"),
        ("sc.payment.execution", "legacy_source_table", "legacy_record_id", "partner_id"),
        ("sc.legacy.enterprise.business.fact", "legacy_source_table", "legacy_record_id", "partner_id"),
        ("sc.legacy.receipt.income.fact", "legacy_source_table", "legacy_record_id", "partner_id"),
        ("sc.legacy.expense.deposit.fact", "legacy_source_table", "legacy_record_id", "partner_id"),
        ("sc.legacy.payment.residual.fact", "source_table", "legacy_record_id", "partner_id"),
        ("sc.legacy.receipt.residual.fact", "source_table", "legacy_record_id", "partner_id"),
        ("sc.legacy.invoice.registration.line", "source_table", "legacy_line_id", "partner_id"),
    ]
    for model_name, table_field, record_field, partner_field in specs:
        if model_name not in env.registry:  # noqa: F821
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        if all(field in Model._fields for field in (table_field, record_field, partner_field)):
            yield Model, table_field, record_field, partner_field


def add_index_item(index: dict[tuple[str, str], dict[str, object]], key: tuple[str, str], partner_id: int, route: str) -> None:
    item = index.setdefault(key, {"partner_ids": set(), "routes": set()})
    item["partner_ids"].add(partner_id)
    item["routes"].add(route)


def build_source_partner_index(source_keys: set[tuple[str, str]]) -> dict[tuple[str, str], dict[str, object]]:
    index: dict[tuple[str, str], dict[str, object]] = {}
    tables = sorted({key[0] for key in source_keys})
    record_ids = sorted({key[1] for key in source_keys})
    for Model, table_field, record_field, partner_field in fact_specs():
        for rec in Model.search_read(
            [(table_field, "in", tables), (record_field, "in", record_ids), (partner_field, "!=", False)],
            [table_field, record_field, partner_field],
        ):
            key = (clean(rec.get(table_field)), clean(rec.get(record_field)))
            if key not in source_keys:
                continue
            partner_value = rec.get(partner_field)
            partner_id = partner_value[0] if isinstance(partner_value, (list, tuple)) and partner_value else False
            if partner_id:
                add_index_item(index, key, partner_id, Model._name)

    Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
    if "legacy_contract_id" in Contract._fields:
        for rec in Contract.search_read([("legacy_contract_id", "in", record_ids), ("partner_id", "!=", False)], ["legacy_contract_id", "partner_id"]):
            for table_name in ("T_CGHT_INFO", "T_GYSHT_INFO", "T_HTGL_INFO", "T_HTGL_HTINFO", "T_HTGL_FBHT", "T_WBHTGL_INFO"):
                key = (table_name, clean(rec.get("legacy_contract_id")))
                if key not in source_keys:
                    continue
                partner_value = rec.get("partner_id")
                partner_id = partner_value[0] if isinstance(partner_value, (list, tuple)) and partner_value else False
                if partner_id:
                    add_index_item(index, key, partner_id, "construction.contract")

    Payment = env["payment.request"].sudo().with_context(active_test=False)  # noqa: F821
    for rec in Payment.search_read([("note", "ilike", "legacy_"), ("partner_id", "!=", False)], ["note", "partner_id"]):
        note = clean(rec.get("note"))
        key = None
        for source_table, token in (
            ("C_JFHKLR", "legacy_receipt_id"),
            ("C_ZFSQGL", "legacy_outflow_id"),
            ("T_FK_Supplier", "legacy_actual_outflow_id"),
        ):
            match = re.search(r"%s=([^;\\s]+)" % token, note)
            if match:
                candidate = (source_table, match.group(1).strip())
                if candidate in source_keys:
                    key = candidate
                    break
        if not key:
            continue
        partner_value = rec.get("partner_id")
        partner_id = partner_value[0] if isinstance(partner_value, (list, tuple)) and partner_value else False
        if partner_id:
            add_index_item(index, key, partner_id, "payment.request.note")
    return index


ensure_allowed()
rows, source_counts = read_csvs(INPUT_CSVS)
source_rows_by_key = {source_identity(row): row for row in rows if all(source_identity(row))}
source_partner_index = build_source_partner_index(set(source_rows_by_key))
Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821

updates: list[dict[str, object]] = []
misses: list[dict[str, object]] = []
route_counts: Counter[str] = Counter()
field_update_counts: Counter[str] = Counter()

try:
    for row in rows:
        table_name, record_id = source_identity(row)
        creator = normalize_creator(row.get("creator_name"), row.get("creator_legacy_user_id"))
        created_time = clean(row.get("created_time"))
        if not table_name or not record_id or (not creator and not created_time):
            continue
        index_item = source_partner_index.get((table_name, record_id)) or {"partner_ids": set(), "routes": set()}
        partner_ids = index_item["partner_ids"]
        routes = sorted(index_item["routes"])
        if not partner_ids:
            misses.append({"source_table": table_name, "legacy_record_id": record_id, "creator_name": creator, "created_time": created_time})
            continue
        for route in routes:
            route_counts[route] += 1
        for partner in Partner.browse(sorted(partner_ids)).exists():
            vals: dict[str, object] = {}
            if creator and should_overwrite_created_by(partner.sc_source_created_by):
                vals["sc_source_created_by"] = creator
            if created_time and should_overwrite_created_at(partner.sc_source_created_at):
                vals["sc_source_created_at"] = created_time
            if not vals:
                continue
            if MODE == "write":
                partner.write(vals)
            for field in vals:
                field_update_counts[field] += 1
            updates.append(
                {
                    "partner_id": partner.id,
                    "partner_name": partner.name or "",
                    "source_table": table_name,
                    "legacy_record_id": record_id,
                    "creator_name": creator,
                    "created_time": created_time,
                    "routes": ";".join(routes),
                    "updated_fields": ";".join(sorted(vals)),
                }
            )
    if MODE == "write":
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

run_id = datetime.now(timezone.utc).strftime("partner_source_creator_backfill_%Y%m%dT%H%M%SZ")
output_root = ARTIFACT_ROOT / run_id
write_csv(
    output_root / "partner_source_creator_backfill_rows_v1.csv",
    ["partner_id", "partner_name", "source_table", "legacy_record_id", "creator_name", "created_time", "routes", "updated_fields"],
    updates,
)
write_csv(
    output_root / "partner_source_creator_backfill_misses_v1.csv",
    ["source_table", "legacy_record_id", "creator_name", "created_time"],
    misses[:1000],
)
summary = {
    "status": "PASS",
    "mode": "partner_source_creator_backfill",
    "write_mode": MODE,
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "input_source_counts": source_counts,
    "source_key_count": len(source_rows_by_key),
    "partner_rows_to_update": len(updates),
    "miss_count": len(misses),
    "route_counts": dict(sorted(route_counts.items())),
    "field_update_counts": dict(sorted(field_update_counts.items())),
    "db_write": MODE == "write",
    "output_root": str(output_root),
}
write_json(output_root / "partner_source_creator_backfill_result_v1.json", summary)
print("PARTNER_SOURCE_CREATOR_BACKFILL=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
