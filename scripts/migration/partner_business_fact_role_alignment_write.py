#!/usr/bin/env python3
"""Align customer/supplier roles from runtime business facts.

Run through Odoo shell. Default mode is dry-run; set
MIGRATION_WRITE_MODE=write to persist.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


MODE = os.getenv("MIGRATION_WRITE_MODE", "dry-run")
DEMOTE_NO_FACT = os.getenv("PARTNER_FACT_ALIGNMENT_DEMOTE_NO_FACT", "1") not in {"0", "false", "False"}
ALLOWLIST = {
    item.strip()
    for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo,sc_prod_sim,sc_migration_fresh").split(",")
    if item.strip()
}
REPO_ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", Path.cwd()))
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/partner_business_fact_role_alignment_v1"),
    )
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if MODE not in {"dry-run", "write"}:
    raise RuntimeError({"invalid_write_mode": MODE})
if env.cr.dbname not in ALLOWLIST:  # noqa: F821
    raise RuntimeError({"db_name_not_allowed": env.cr.dbname, "allowlist": sorted(ALLOWLIST)})  # noqa: F821

try:
    summary = env["res.partner"].sudo().action_sc_align_partner_roles_from_business_facts(  # noqa: F821
        demote_no_fact=DEMOTE_NO_FACT
    )
    summary.update(
        {
            "mode": "partner_business_fact_role_alignment",
            "write_mode": MODE,
            "database": env.cr.dbname,  # noqa: F821
            "db_write": MODE == "write",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
    )
    if MODE == "write":
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821
except Exception:
    env.cr.rollback()  # noqa: F821
    raise

run_id = datetime.now(timezone.utc).strftime("partner_business_fact_role_alignment_%Y%m%dT%H%M%SZ")
output_root = ARTIFACT_ROOT / run_id
summary["output_root"] = str(output_root)
write_json(output_root / "partner_business_fact_role_alignment_result_v1.json", summary)
print("PARTNER_BUSINESS_FACT_ROLE_ALIGNMENT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
