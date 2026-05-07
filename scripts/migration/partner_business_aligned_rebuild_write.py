#!/usr/bin/env python3
"""Write the gated business-aligned partner payload through Odoo shell.

Default mode is dry-run. Set MIGRATION_WRITE_MODE=write to commit.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", Path.cwd()))
PAYLOAD = Path(
    os.getenv(
        "PARTNER_BUSINESS_ALIGNED_GATE_CSV",
        str(
            REPO_ROOT
            / "artifacts/migration/partner_business_aligned_rebuild_v1/"
            / "fact_based_partner_rebuild_business_aligned_gate_v1.csv"
        ),
    )
)
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/partner_business_aligned_rebuild_write_v1"),
    )
)
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}
SAFE_FIELDS = [
    "name",
    "company_type",
    "customer_rank",
    "supplier_rank",
    "sc_supplier_type",
    "sc_region",
    "street",
    "sc_registered_capital",
    "sc_business_scope",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
    "vat",
    "legacy_partner_id",
    "legacy_partner_source",
    "legacy_partner_name",
    "legacy_credit_code",
    "legacy_tax_no",
    "legacy_source_evidence",
]
ROLLBACK_FIELDS = [
    "partner_id",
    "mode_action",
    "match_method",
    "gate_action",
    "partner_key",
    *SAFE_FIELDS,
]


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_allowed() -> None:
    if env.cr.dbname not in ALLOWLIST:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821
    if MODE not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_write_mode": MODE})


def row_to_vals(row: dict[str, str]) -> dict[str, object]:
    vals: dict[str, object] = {
        "name": clean(row.get("name")),
        "company_type": clean(row.get("company_type")) or "company",
        "customer_rank": int(clean(row.get("customer_rank")) or "0"),
        "supplier_rank": int(clean(row.get("supplier_rank")) or "0"),
        "sc_supplier_type": clean(row.get("sc_supplier_type")) or False,
        "sc_region": clean(row.get("sc_region")) or False,
        "street": clean(row.get("street")) or False,
        "sc_registered_capital": clean(row.get("sc_registered_capital")) or False,
        "sc_business_scope": clean(row.get("sc_business_scope")) or False,
        "sc_account_name": clean(row.get("sc_account_name")) or False,
        "sc_bank_name": clean(row.get("sc_bank_name")) or False,
        "sc_bank_account": clean(row.get("sc_bank_account")) or False,
        "vat": clean(row.get("vat")) or False,
        "legacy_partner_id": clean(row.get("legacy_partner_id")),
        "legacy_partner_source": clean(row.get("legacy_partner_source")),
        "legacy_partner_name": clean(row.get("name")),
        "legacy_credit_code": clean(row.get("legacy_credit_code")) or False,
        "legacy_tax_no": clean(row.get("vat")) or False,
        "legacy_source_evidence": clean(row.get("legacy_source_evidence")) or False,
    }
    return {key: value for key, value in vals.items() if key in SAFE_FIELDS}


def snapshot_row(rec, row: dict[str, str], mode_action: str, match_method: str) -> dict[str, object]:
    data = {
        "partner_id": rec.id,
        "mode_action": mode_action,
        "match_method": match_method,
        "gate_action": clean(row.get("gate_action")),
        "partner_key": clean(row.get("partner_key")),
    }
    for field in SAFE_FIELDS:
        value = rec[field] if field in rec._fields else ""
        data[field] = value.id if hasattr(value, "id") else (value if value is not False else "")
    return data


def find_partner(Partner, row: dict[str, str]):
    legacy_source = clean(row.get("legacy_partner_source"))
    legacy_id = clean(row.get("legacy_partner_id"))
    if legacy_source and legacy_id:
        matches = Partner.search([("legacy_partner_source", "=", legacy_source), ("legacy_partner_id", "=", legacy_id)])
        if len(matches) == 1:
            return matches, "legacy_identity"
        if len(matches) > 1:
            return matches, "ambiguous_legacy_identity"
    vat = clean(row.get("vat"))
    if vat:
        matches = Partner.search([("vat", "=", vat)])
        if len(matches) == 1:
            return matches, "vat"
        if len(matches) > 1:
            return matches, "ambiguous_vat"
    name = clean(row.get("name"))
    if name:
        matches = Partner.search([("name", "=", name)])
        if len(matches) == 1:
            return matches, "exact_name"
        if len(matches) > 1:
            return matches, "ambiguous_exact_name"
    return Partner.browse(), "not_found"


ensure_allowed()

Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
missing_fields = [field for field in SAFE_FIELDS if field not in Partner._fields]
if missing_fields:
    raise RuntimeError({"missing_partner_fields": missing_fields})

rows = read_csv(PAYLOAD)
result_rows: list[dict[str, object]] = []
rollback_rows: list[dict[str, object]] = []
action_counts: Counter[str] = Counter()

try:
    for row in rows:
        gate_action = clean(row.get("gate_action"))
        if gate_action == "blocked_review":
            action_counts["skip_blocked_review"] += 1
            continue
        partner, match_method = find_partner(Partner, row)
        if match_method.startswith("ambiguous"):
            action_counts["skip_ambiguous_target"] += 1
            result_rows.append(
                {
                    "partner_key": clean(row.get("partner_key")),
                    "name": clean(row.get("name")),
                    "gate_action": gate_action,
                    "result_action": "skip_ambiguous_target",
                    "match_method": match_method,
                    "matched_partner_ids": ";".join(str(item) for item in partner.ids),
                }
            )
            continue
        if gate_action == "update_only_candidate" and not partner:
            action_counts["skip_update_only_not_found"] += 1
            result_rows.append(
                {
                    "partner_key": clean(row.get("partner_key")),
                    "name": clean(row.get("name")),
                    "gate_action": gate_action,
                    "result_action": "skip_update_only_not_found",
                    "match_method": match_method,
                    "matched_partner_ids": "",
                }
            )
            continue
        vals = row_to_vals(row)
        if not clean(vals.get("name")):
            action_counts["skip_missing_name"] += 1
            continue
        if partner:
            mode_action = "update"
            rollback_rows.append(snapshot_row(partner, row, mode_action, match_method))
            if MODE == "write":
                partner.write(vals)
            target_id = partner.id
        else:
            mode_action = "create"
            if MODE == "write":
                partner = Partner.create(vals)
                target_id = partner.id
                rollback_rows.append(snapshot_row(partner, row, mode_action, match_method))
            else:
                target_id = ""
        action_counts[f"{MODE}_{mode_action}"] += 1
        result_rows.append(
            {
                "partner_key": clean(row.get("partner_key")),
                "name": clean(row.get("name")),
                "gate_action": gate_action,
                "result_action": f"{MODE}_{mode_action}",
                "match_method": match_method,
                "matched_partner_ids": str(target_id),
            }
        )
    if MODE == "write":
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

run_id = datetime.now(UTC).strftime("partner_business_aligned_rebuild_write_%Y%m%dT%H%M%SZ")
output_root = ARTIFACT_ROOT / run_id
write_csv(
    output_root / "partner_business_aligned_rebuild_write_rows_v1.csv",
    ["partner_key", "name", "gate_action", "result_action", "match_method", "matched_partner_ids"],
    result_rows,
)
write_csv(output_root / "partner_business_aligned_rebuild_rollback_targets_v1.csv", ROLLBACK_FIELDS, rollback_rows)
summary = {
    "status": "PASS",
    "mode": "partner_business_aligned_rebuild_write",
    "write_mode": MODE,
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "result_rows": len(result_rows),
    "rollback_rows": len(rollback_rows),
    "action_counts": dict(sorted(action_counts.items())),
    "payload": str(PAYLOAD),
    "output_root": str(output_root),
    "db_write": MODE == "write",
}
write_json(output_root / "partner_business_aligned_rebuild_write_result_v1.json", summary)
print("PARTNER_BUSINESS_ALIGNED_REBUILD_WRITE=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
