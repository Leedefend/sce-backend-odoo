#!/usr/bin/env python3
"""Recompute stored uppercase amount text for payment requests."""

from __future__ import annotations

import json
import os
from pathlib import Path

from odoo.addons.smart_construction_core.models.core.payment_request import _amount_to_chinese_upper


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def scalar(sql: str, params: tuple[object, ...] | None = None) -> int:
    env.cr.execute(sql, params or ())  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "").split(",") if item.strip()}
if allowlist and env.cr.dbname not in allowlist:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed_for_payment_request_recompute": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821

Request = env["payment.request"].sudo()  # noqa: F821
total = Request.search_count([])
filled_before = Request.search_count([("amount_uppercase", "!=", False)])
bad_leading_zero_before = scalar(
    "SELECT COUNT(*) FROM payment_request WHERE amount_uppercase LIKE %s",
    ("零壹%",),
)

updated = 0
batch_size = 2000
ids = Request.search([]).ids
for offset in range(0, len(ids), batch_size):
    rows = Request.browse(ids[offset : offset + batch_size]).read(["amount", "amount_uppercase"])
    for row in rows:
        expected = _amount_to_chinese_upper(row.get("amount"))
        if row.get("amount_uppercase") == expected:
            continue
        env.cr.execute(  # noqa: F821
            """
            UPDATE payment_request
               SET amount_uppercase = %s
             WHERE id = %s
            """,
            (expected, row["id"]),
        )
        updated += env.cr.rowcount  # noqa: F821

env.cr.commit()  # noqa: F821

filled_after = Request.search_count([("amount_uppercase", "!=", False)])
bad_leading_zero_after = scalar(
    "SELECT COUNT(*) FROM payment_request WHERE amount_uppercase LIKE %s",
    ("零壹%",),
)

payload = {
    "status": "PASS" if bad_leading_zero_after == 0 and filled_after == total else "FAIL",
    "mode": "payment_request_amount_uppercase_recompute_write",
    "database": env.cr.dbname,  # noqa: F821
    "total": total,
    "filled_before": filled_before,
    "filled_after": filled_after,
    "bad_leading_zero_before": bad_leading_zero_before,
    "bad_leading_zero_after": bad_leading_zero_after,
    "updated_rows": updated,
    "decision": "stored_payment_request_amount_uppercase_is_a_derived_display_field_and_must_be_recomputed_after_formula_changes",
}
write_json(artifact_root() / "payment_request_amount_uppercase_recompute_write_result_v1.json", payload)
print("PAYMENT_REQUEST_AMOUNT_UPPERCASE_RECOMPUTE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
