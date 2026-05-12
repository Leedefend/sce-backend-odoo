#!/usr/bin/env python3
"""Backfill supplier contract visible amount from replay payload evidence.

The source is the accepted supplier-contract replay payload and the
``amount_trace=...`` token stored on runtime contract notes. The script does
not fabricate entry user/time values when the legacy payload did not carry
them.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists() or (candidate / "artifacts").exists():
            return candidate
    return Path.cwd()


REPO_ROOT = repo_root()
PAYLOAD_CSV = Path(
    os.getenv(
        "SUPPLIER_CONTRACT_AMOUNT_PAYLOAD_CSV",
        str(REPO_ROOT / "artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv"),
    )
)
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/contract_supplier_amount_backfill_v1"),
    )
)
MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}


def clean(value: object) -> str:
    if value is None or value is False:
        return ""
    return str(value).strip()


def money(value: object) -> Decimal:
    text = clean(value).replace(",", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def amount_from_note(note: object) -> Decimal:
    match = re.search(r"amount_trace=([^;\s]+)", clean(note))
    return money(match.group(1)) if match else Decimal("0")


def read_payload(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {clean(row.get("legacy_contract_id")): dict(row) for row in csv.DictReader(handle) if clean(row.get("legacy_contract_id"))}


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if MODE not in {"dry-run", "write"}:
    raise RuntimeError({"invalid_write_mode": MODE})
if env.cr.dbname not in ALLOWLIST:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821

payload_by_id = read_payload(PAYLOAD_CSV)
Contract = env["construction.contract"].sudo().with_context(active_test=False)  # noqa: F821
contracts = Contract.search([("type", "=", "in"), ("legacy_contract_id", "!=", False)])

updates: list[dict[str, object]] = []
skips: Counter[str] = Counter()

try:
    for contract in contracts:
        payload = payload_by_id.get(clean(contract.legacy_contract_id))
        amount = amount_from_note(contract.note)
        source = "note.amount_trace"
        if not amount and payload:
            amount = amount_from_note(payload.get("note"))
            source = "payload.note.amount_trace"
        if not amount:
            skips["missing_amount_trace"] += 1
            continue
        if abs(Decimal(str(contract.visible_contract_amount or 0)) - amount) <= Decimal("0.01"):
            skips["already_aligned"] += 1
            continue
        previous_legacy_amount = contract.legacy_contract_amount or 0.0
        previous_amount_untaxed = contract.amount_untaxed or 0.0
        vals = {
            "legacy_contract_amount": float(amount),
            "legacy_contract_amount_source": source,
        }
        if not contract.amount_untaxed:
            vals["amount_untaxed"] = float(amount)
        if MODE == "write":
            contract.write(vals)
        updates.append(
            {
                "contract_id": contract.id,
                "legacy_contract_id": contract.legacy_contract_id or "",
                "legacy_document_no": contract.legacy_document_no or "",
                "legacy_contract_no": contract.legacy_contract_no or "",
                "subject": contract.subject or "",
                "amount": str(amount),
                "amount_source": source,
                "previous_legacy_contract_amount": previous_legacy_amount,
                "previous_amount_untaxed": previous_amount_untaxed,
            }
        )
    if MODE == "write":
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

run_id = datetime.now(timezone.utc).strftime("contract_supplier_amount_backfill_%Y%m%dT%H%M%SZ")
output_root = ARTIFACT_ROOT / run_id
write_csv(
    output_root / "contract_supplier_amount_backfill_rows_v1.csv",
    [
        "contract_id",
        "legacy_contract_id",
        "legacy_document_no",
        "legacy_contract_no",
        "subject",
        "amount",
        "amount_source",
        "previous_legacy_contract_amount",
        "previous_amount_untaxed",
    ],
    updates,
)
summary = {
    "status": "PASS",
    "mode": "contract_supplier_amount_backfill_from_payload",
    "write_mode": MODE,
    "database": env.cr.dbname,  # noqa: F821
    "payload_csv": str(PAYLOAD_CSV),
    "payload_rows": len(payload_by_id),
    "target_contract_count": len(contracts),
    "updated_rows": len(updates),
    "skip_counts": dict(sorted(skips.items())),
    "db_write": MODE == "write",
    "output_root": str(output_root),
}
write_json(output_root / "contract_supplier_amount_backfill_result_v1.json", summary)
print("CONTRACT_SUPPLIER_AMOUNT_BACKFILL=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
