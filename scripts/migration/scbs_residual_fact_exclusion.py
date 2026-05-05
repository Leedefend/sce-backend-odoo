"""Archive residual non-business SCBS staging facts.

After project/entity/partner/material fact bootstrap, remaining non-projection
rows are dirty labels such as test values or non-real project carriers. They
should stay auditable in staging but be excluded from the active projection
pool.

Dry-run by default. Set ``SCBS_RESIDUAL_FACT_EXCLUSION_APPLY=1`` to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


BATCH = "scbs_residual_fact_exclusion_v1"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    artifacts = artifact_root()
    apply = os.getenv("SCBS_RESIDUAL_FACT_EXCLUSION_APPLY") == "1"
    plan_csv = artifacts / "scbs_residual_fact_exclusion_plan_v1.csv"
    result_json = artifacts / "scbs_residual_fact_exclusion_result_v1.json"

    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)
    domain = [
        ("import_batch", "=", "scbs_fact_staging_v1"),
        ("active", "=", True),
        ("mapping_gate_state", "!=", "projection_ready"),
    ]
    records = Staging.search(domain, order="fact_family, source_table, amount_total desc, legacy_record_id")

    rows: list[dict[str, object]] = []
    for rec in records:
        reason = "residual_non_projection_fact"
        if rec.business_entity_mapping_state in {"conflict", "ignored"}:
            reason = "residual_business_entity_label"
        elif rec.project_mapping_state in {"conflict", "ignored"}:
            reason = "residual_non_real_or_test_project"
        elif rec.partner_mapping_state in {"conflict", "ignored"}:
            reason = "residual_partner_label"
        rows.append(
            {
                "staging_id": rec.id,
                "source_table": rec.source_table,
                "legacy_record_id": rec.legacy_record_id,
                "fact_family": rec.fact_family,
                "amount_total": rec.amount_total,
                "mapping_gate_state": rec.mapping_gate_state,
                "legacy_xmmc": rec.legacy_xmmc,
                "business_entity_state": rec.business_entity_mapping_state,
                "legacy_gcmc": rec.legacy_gcmc,
                "project_state": rec.project_mapping_state,
                "legacy_partner_name": rec.legacy_partner_name,
                "partner_state": rec.partner_mapping_state,
                "exclusion_reason": reason,
            }
        )

    if apply and records:
        for rec in records:
            rec.write({"active": False, "note": ((rec.note or "") + f"\n{BATCH}: excluded from active projection pool").strip()})
        env.cr.commit()

    result = {
        "mode": "apply" if apply else "dry_run",
        "planned_rows": len(rows),
        "excluded_rows": len(rows) if apply else 0,
        "plan_csv": str(plan_csv),
        "result_json": str(result_json),
    }
    write_csv(
        plan_csv,
        rows,
        [
            "staging_id",
            "source_table",
            "legacy_record_id",
            "fact_family",
            "amount_total",
            "mapping_gate_state",
            "legacy_xmmc",
            "business_entity_state",
            "legacy_gcmc",
            "project_state",
            "legacy_partner_name",
            "partner_state",
            "exclusion_reason",
        ],
    )
    write_json(result_json, result)
    print("SCBS_RESIDUAL_FACT_EXCLUSION=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
