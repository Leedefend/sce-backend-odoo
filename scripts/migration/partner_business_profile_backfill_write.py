#!/usr/bin/env python3
"""Backfill visible customer/supplier profile fields from accepted assets.

Default mode is dry-run. Set MIGRATION_WRITE_MODE=write to commit.
This script only updates existing fact-backed customer/supplier partners and
only fills empty compatibility/profile fields.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    if env_root:
        return Path(env_root)
    candidates = []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
DEFAULT_PROFILE_CSVS = [
    REPO_ROOT / "artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv",
    REPO_ROOT
    / "artifacts/migration/partner_business_aligned_replay_package_v1/artifacts/migration/"
    / "partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv",
    REPO_ROOT
    / "artifacts/migration/fact_based_partner_rebuild_2_fact_only_20260506T2055/"
    / "fact_based_partner_rebuild_payload_v1.csv",
    REPO_ROOT / "artifacts/migration/legacy_mssql_customer_business_fact_candidates_v1.csv",
    REPO_ROOT / "artifacts/migration/runtime_partner_business_fit_sc_v1/10_master/partner/partner_master_v1.csv",
    REPO_ROOT / "artifacts/migration/partner_import_source_asset_v1/partner_master_source_v1.csv",
]
DEFAULT_BANK_CSVS = [
    REPO_ROOT / "artifacts/migration/runtime_partner_bank_business_fit_v1/10_master/partner_bank/partner_bank_master_v1.csv",
    REPO_ROOT
    / "artifacts/migration/partner_business_aligned_replay_package_v1/artifacts/migration_assets/"
    / "partner_bank_business_fit_v1/10_master/partner_bank/partner_bank_master_v1.csv",
]
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/partner_business_profile_backfill_v1"),
    )
)
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}
PROFILE_CSVS = [
    Path(item.strip())
    for item in os.getenv("PARTNER_PROFILE_BACKFILL_CSVS", "").split(",")
    if item.strip()
] or DEFAULT_PROFILE_CSVS
BANK_CSVS = [
    Path(item.strip())
    for item in os.getenv("PARTNER_PROFILE_BACKFILL_BANK_CSVS", "").split(",")
    if item.strip()
] or DEFAULT_BANK_CSVS

PROFILE_FIELD_SOURCES = {
    "vat": ("vat", "legacy_credit_code", "legacy_tax_no", "tax_no"),
    "legacy_credit_code": ("legacy_credit_code", "vat", "tax_no"),
    "legacy_tax_no": ("legacy_tax_no", "vat", "tax_no"),
    "sc_account_name": ("sc_account_name", "account_name", "bank_account_name"),
    "sc_bank_name": ("sc_bank_name", "bank_name"),
    "sc_bank_account": ("sc_bank_account", "bank_account"),
    "sc_source_cooperation_type": ("sc_source_cooperation_type", "source_cooperation_type", "cooperation_types"),
    "sc_supplier_type": ("sc_supplier_type", "main_supply_types"),
    "sc_region": ("sc_region", "region"),
    "street": ("street", "address"),
    "sc_registered_capital": ("sc_registered_capital",),
    "sc_business_scope": ("sc_business_scope",),
    "sc_default_tax_rate_text": ("sc_default_tax_rate_text", "tax_rate", "source_tax_rate"),
    "sc_source_partner_code": ("sc_source_partner_code", "source_partner_code", "source_code"),
    "sc_source_document_state": ("sc_source_document_state", "source_document_state", "source_status"),
    "sc_source_push_result": ("sc_source_push_result", "source_push_result"),
    "sc_source_created_by": ("sc_source_created_by", "source_created_by", "source_operator", "creator", "create_user"),
    "sc_source_created_at": ("sc_source_created_at", "source_created_at", "source_time", "created_at", "create_time"),
}
TECHNICAL_CREATED_BY_VALUES = {"odoobot", "administrator", "admin", "system", "系统", "系统导入"}
TECHNICAL_CREATED_AT_PREFIXES = ("2026-05-08", "2026-05-09")


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text


def norm_text(value: object) -> str:
    return re.sub(r"\s+", "", clean(value)).lower()


def norm_vat(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", clean(value)).upper()


def is_valid_bank_account(value: object) -> bool:
    text = re.sub(r"\s+", "", clean(value))
    if not text or text in {"0", "1", ".", "/", "-", "--", "无", "无开户行"}:
        return False
    return bool(re.search(r"\d{6,}", text))


def split_semicolon(value: object) -> list[str]:
    text = clean(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[;；,，/|]+", text) if item.strip()]


def supplier_type_from_text(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"material", "labor", "subcontract", "service", "equipment", "other"}:
        return lowered
    if "劳务" in text:
        return "labor"
    if "分包" in text:
        return "subcontract"
    if "设备" in text:
        return "equipment"
    if "材料" in text:
        return "material"
    if "服务" in text:
        return "service"
    return "other"


def should_overwrite_field(field: str, current: object) -> bool:
    current_text = clean(current)
    if not current_text:
        return True
    if field == "sc_source_created_by":
        return current_text.strip().lower() in TECHNICAL_CREATED_BY_VALUES
    if field == "sc_source_created_at":
        # Runtime replay timestamps are technical load evidence, not the user's
        # source business entry time. Keep non-technical source values intact.
        return current_text.startswith(TECHNICAL_CREATED_AT_PREFIXES)
    return False


def is_technical_created_by(value: object) -> bool:
    text = clean(value).strip().lower()
    return bool(text and text in TECHNICAL_CREATED_BY_VALUES)


def is_technical_created_at(value: object) -> bool:
    text = clean(value)
    return bool(text and text.startswith(TECHNICAL_CREATED_AT_PREFIXES))


def is_login_like(value: object) -> bool:
    text = clean(value)
    if not text:
        return False
    if re.search(r"[\u4e00-\u9fff]", text):
        return False
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.@-]{1,63}", text))


def user_display_name_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    for user in Users.search([]):
        login = clean(user.login).lower()
        name = clean(user.name)
        if login and name and login != name.lower():
            mapping[login] = name
    if "sc.legacy.user.profile" in env.registry:  # noqa: F821
        Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
        for profile in Profile.search([]):
            for raw_login in (profile.source_login, profile.generated_login):
                login = clean(raw_login).lower()
                name = clean(profile.display_name) or clean(profile.user_id.name)
                if login and name and login != name.lower():
                    mapping.setdefault(login, name)
    return mapping


USER_DISPLAY_NAME_MAP = user_display_name_map()


def normalize_created_by_value(value: object) -> str:
    text = clean(value)
    if not text or is_technical_created_by(text):
        return ""
    mapped = USER_DISPLAY_NAME_MAP.get(text.lower())
    if mapped:
        return mapped
    if is_login_like(text):
        return ""
    return text


def first_value(row: dict[str, str], fields: tuple[str, ...]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


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
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})


def identity_for_row(row: dict[str, str]) -> tuple[str, str]:
    source = clean(
        row.get("legacy_partner_source")
        or row.get("partner_legacy_partner_source")
        or row.get("sc_legacy_partner_source")
    )
    legacy_id = clean(
        row.get("legacy_partner_id")
        or row.get("partner_legacy_partner_id")
        or row.get("sc_legacy_partner_id")
        or row.get("legacy_partner_key")
    )
    return source, legacy_id


def name_for_row(row: dict[str, str]) -> str:
    return clean(row.get("name") or row.get("partner_name") or row.get("sc_legacy_partner_name"))


ensure_allowed()

Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
PartnerBank = env["res.partner.bank"].sudo().with_context(active_test=False)  # noqa: F821
missing_partner_fields = [field for field in PROFILE_FIELD_SOURCES if field not in Partner._fields]
missing_bank_fields = [
    field
    for field in [
        "sc_legacy_external_id",
        "sc_legacy_partner_id",
        "sc_legacy_partner_source",
        "sc_legacy_partner_name",
        "sc_account_holder_name",
        "sc_bank_name",
        "sc_source_evidence",
        "sc_import_batch",
    ]
    if field not in PartnerBank._fields
]
if missing_partner_fields or missing_bank_fields:
    raise RuntimeError({"missing_partner_fields": missing_partner_fields, "missing_bank_fields": missing_bank_fields})

profile_rows, profile_source_counts = read_csvs(PROFILE_CSVS)
bank_rows, bank_source_counts = read_csvs(BANK_CSVS)
targets = Partner.search(["|", "|", ("customer_rank", ">", 0), ("supplier_rank", ">", 0), ("sc_source_fact_count", ">", 0)])

by_identity: dict[tuple[str, str], object] = {}
by_vat: dict[str, object] = {}
by_name: dict[str, object] = {}
identity_counts: Counter[tuple[str, str]] = Counter()
vat_counts: Counter[str] = Counter()
name_counts: Counter[str] = Counter()
for partner in targets:
    key = (clean(partner.legacy_partner_source), clean(partner.legacy_partner_id))
    if key[0] and key[1]:
        identity_counts[key] += 1
    vat = norm_vat(partner.vat or partner.legacy_credit_code or partner.legacy_tax_no)
    if vat:
        vat_counts[vat] += 1
    name = norm_text(partner.name)
    if name:
        name_counts[name] += 1
for partner in targets:
    key = (clean(partner.legacy_partner_source), clean(partner.legacy_partner_id))
    if key[0] and key[1] and identity_counts[key] == 1:
        by_identity[key] = partner
    vat = norm_vat(partner.vat or partner.legacy_credit_code or partner.legacy_tax_no)
    if vat and vat_counts[vat] == 1:
        by_vat[vat] = partner
    name = norm_text(partner.name)
    if name and name_counts[name] == 1:
        by_name[name] = partner


def match_partner(row: dict[str, str]):
    identity = identity_for_row(row)
    if identity in by_identity:
        return by_identity[identity], "legacy_identity"
    vat = norm_vat(first_value(row, ("vat", "legacy_credit_code", "legacy_tax_no", "tax_no")))
    if vat and vat in by_vat:
        return by_vat[vat], "vat"
    name = norm_text(name_for_row(row))
    if name and name in by_name:
        return by_name[name], "exact_name"
    return Partner.browse(), "not_found"


best_profile_rows: dict[int, tuple[dict[str, str], str, int]] = {}
profile_match_counts: Counter[str] = Counter()
CREATED_BY_FIELDS = PROFILE_FIELD_SOURCES["sc_source_created_by"]
CREATED_AT_FIELDS = PROFILE_FIELD_SOURCES["sc_source_created_at"]


def profile_row_score(row: dict[str, str]) -> tuple[int, int, int]:
    created_by = normalize_created_by_value(first_value(row, CREATED_BY_FIELDS))
    created_at = first_value(row, CREATED_AT_FIELDS)
    completeness = sum(1 for fields in PROFILE_FIELD_SOURCES.values() if first_value(row, fields))
    return (1 if created_by else 0, 1 if created_at else 0, completeness)


for index, row in enumerate(profile_rows, start=2):
    partner, method = match_partner(row)
    profile_match_counts[method] += 1
    if not partner:
        continue
    score = profile_row_score(row)
    current = best_profile_rows.get(partner.id)
    if current is None or score > current[2]:
        best_profile_rows[partner.id] = (row, method, score)

profile_changes: list[dict[str, object]] = []
rollback_rows: list[dict[str, object]] = []
field_update_counts: Counter[str] = Counter()
technical_clear_rows: list[dict[str, object]] = []
try:
    for partner_id, (row, method, _score) in sorted(best_profile_rows.items()):
        partner = Partner.browse(partner_id)
        vals: dict[str, object] = {}
        for field, source_fields in PROFILE_FIELD_SOURCES.items():
            if field == "sc_supplier_type":
                if partner.sc_supplier_type and partner.sc_supplier_type != "other":
                    continue
                value = supplier_type_from_text(first_value(row, source_fields))
            else:
                if not should_overwrite_field(field, partner[field]):
                    continue
                value = first_value(row, source_fields)
                if field == "sc_source_created_by":
                    value = normalize_created_by_value(value)
            if field in {"vat", "legacy_credit_code", "legacy_tax_no"} and not norm_vat(value):
                continue
            if field == "sc_bank_account" and value and not is_valid_bank_account(value):
                continue
            if value:
                vals[field] = value
        if not vals:
            continue
        rollback = {"partner_id": partner.id, "name": partner.name or "", "match_method": method}
        for field in vals:
            rollback[field] = partner[field] if partner[field] is not False else ""
            field_update_counts[field] += 1
        rollback_rows.append(rollback)
        if MODE == "write":
            partner.write(vals)
        profile_changes.append(
            {
                "partner_id": partner.id,
                "name": partner.name or "",
                "match_method": method,
                "updated_fields": ";".join(sorted(vals)),
            }
        )

    existing_bank_keys = set()
    for bank in PartnerBank.search([]):
        acc = re.sub(r"\s+", "", clean(bank.acc_number))
        if bank.partner_id and acc:
            existing_bank_keys.add((bank.partner_id.id, acc))
    bank_changes: list[dict[str, object]] = []
    bank_match_counts: Counter[str] = Counter()
    seen_bank_keys: set[tuple[int, str]] = set()
    for row in bank_rows:
        partner, method = match_partner(row)
        bank_match_counts[method] += 1
        if not partner:
            continue
        acc_number = re.sub(r"\s+", "", clean(row.get("acc_number") or row.get("bank_account") or row.get("sc_bank_account")))
        if not is_valid_bank_account(acc_number):
            continue
        key = (partner.id, acc_number)
        if key in existing_bank_keys or key in seen_bank_keys:
            continue
        seen_bank_keys.add(key)
        external_id = clean(row.get("sc_legacy_external_id") or row.get("external_id")) or f"profile_backfill_{partner.id}_{acc_number}"
        source, legacy_id = identity_for_row(row)
        vals = {
            "partner_id": partner.id,
            "acc_number": acc_number,
            "sc_legacy_external_id": external_id,
            "sc_legacy_partner_source": source,
            "sc_legacy_partner_id": legacy_id,
            "sc_legacy_partner_name": clean(row.get("sc_legacy_partner_name") or row.get("partner_name") or partner.name),
            "sc_account_holder_name": clean(row.get("sc_account_holder_name") or row.get("acc_holder_name") or partner.sc_account_name or partner.name),
            "sc_bank_name": clean(row.get("sc_bank_name") or row.get("bank_name") or partner.sc_bank_name),
            "sc_source_evidence": clean(row.get("sc_source_evidence") or row.get("source_evidence")),
            "sc_import_batch": clean(row.get("sc_import_batch")) or "partner_business_profile_backfill_v1",
        }
        vals = {field: value for field, value in vals.items() if value not in ("", None)}
        if MODE == "write":
            bank = PartnerBank.create(vals)
            bank_id = bank.id
        else:
            bank_id = ""
        bank_changes.append(
            {
                "bank_id": bank_id,
                "partner_id": partner.id,
                "partner_name": partner.name or "",
                "acc_number": acc_number,
                "sc_bank_name": vals.get("sc_bank_name", ""),
                "match_method": method,
            }
        )

    for partner in targets:
        vals: dict[str, object] = {}
        cleared: list[str] = []
        normalized_created_by = normalize_created_by_value(partner.sc_source_created_by)
        if partner.sc_source_created_by and normalized_created_by != clean(partner.sc_source_created_by):
            vals["sc_source_created_by"] = normalized_created_by or False
            cleared.append("sc_source_created_by")
        elif is_technical_created_by(partner.sc_source_created_by):
            vals["sc_source_created_by"] = False
            cleared.append("sc_source_created_by")
        if is_technical_created_at(partner.sc_source_created_at):
            vals["sc_source_created_at"] = False
            cleared.append("sc_source_created_at")
        if not vals:
            continue
        if MODE == "write":
            partner.write(vals)
        for field in cleared:
            field_update_counts[f"{field}_cleared_technical"] += 1
        technical_clear_rows.append(
            {
                "partner_id": partner.id,
                "name": partner.name or "",
                "cleared_fields": ";".join(cleared),
            }
        )

    if MODE == "write":
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

run_id = datetime.now(timezone.utc).strftime("partner_business_profile_backfill_%Y%m%dT%H%M%SZ")
output_root = ARTIFACT_ROOT / run_id
write_csv(
    output_root / "partner_business_profile_backfill_rows_v1.csv",
    ["partner_id", "name", "match_method", "updated_fields"],
    profile_changes,
)
rollback_fields = sorted({field for row in rollback_rows for field in row}) or ["partner_id", "name", "match_method"]
write_csv(output_root / "partner_business_profile_backfill_rollback_targets_v1.csv", rollback_fields, rollback_rows)
write_csv(
    output_root / "partner_business_profile_backfill_bank_rows_v1.csv",
    ["bank_id", "partner_id", "partner_name", "acc_number", "sc_bank_name", "match_method"],
    bank_changes,
)
write_csv(
    output_root / "partner_business_profile_backfill_technical_clear_rows_v1.csv",
    ["partner_id", "name", "cleared_fields"],
    technical_clear_rows,
)
summary = {
    "status": "PASS",
    "mode": "partner_business_profile_backfill",
    "write_mode": MODE,
    "database": env.cr.dbname,  # noqa: F821
    "target_partner_count": len(targets),
    "profile_input_rows": len(profile_rows),
    "bank_input_rows": len(bank_rows),
    "profile_source_counts": profile_source_counts,
    "bank_source_counts": bank_source_counts,
    "profile_match_counts": dict(sorted(profile_match_counts.items())),
    "bank_match_counts": dict(sorted(bank_match_counts.items())),
    "partner_rows_to_update": len(profile_changes),
    "bank_rows_to_create": len(bank_changes),
    "technical_rows_to_clear": len(technical_clear_rows),
    "field_update_counts": dict(sorted(field_update_counts.items())),
    "db_write": MODE == "write",
    "output_root": str(output_root),
}
write_json(output_root / "partner_business_profile_backfill_result_v1.json", summary)
print("PARTNER_BUSINESS_PROFILE_BACKFILL=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
