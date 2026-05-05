"""Refresh SCBS operation-strategy policy after business confirmation.

Confirmed policy:
- SCBS project-level business facts are new-system direct-operation facts,
  even when legacy names contain "联营".
- Any project that carries confirmed SCBS project facts must therefore be
  marked as direct.

Dry-run by default. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


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
    apply = os.getenv("APPLY") == "1"
    artifacts = artifact_root()
    plan_csv = artifacts / "scbs_operation_strategy_policy_refresh_plan_v1.csv"
    result_json = artifacts / "scbs_operation_strategy_policy_refresh_result_v1.json"

    Fact = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    facts = Fact.search(
        [
            ("import_batch", "=", "scbs_fact_staging_v1"),
            ("active", "=", True),
            ("mapping_gate_state", "=", "projection_ready"),
            ("project_id", "!=", False),
        ]
    )
    projects = facts.mapped("project_id")
    to_update = projects.filtered(lambda project: project.operation_strategy != "direct")

    rows: list[dict[str, object]] = []
    for project in to_update.sorted("id"):
        project_facts = facts.filtered(lambda fact, project=project: fact.project_id == project)
        rows.append(
            {
                "project_id": project.id,
                "project_name": project.display_name,
                "old_operation_strategy": project.operation_strategy or "",
                "target_operation_strategy": "direct",
                "fact_rows": len(project_facts),
                "fact_amount": sum(project_facts.mapped("amount_total")),
                "reason": "confirmed_scbs_project_facts_are_direct_operation",
            }
        )

    if apply and to_update:
        to_update.write({"operation_strategy": "direct"})
        env.cr.commit()  # noqa: F821

    payment_joint = env["sc.payment.execution"].sudo().search_count(  # noqa: F821
        [("legacy_source_model", "=", "sc.legacy.scbs.fact.staging"), ("operation_strategy", "=", "joint")]
    )
    contract_joint = env["sc.general.contract"].sudo().search_count(  # noqa: F821
        [("legacy_source_model", "=", "sc.legacy.scbs.fact.staging"), ("operation_strategy", "=", "joint")]
    )

    write_csv(
        plan_csv,
        rows,
        [
            "project_id",
            "project_name",
            "old_operation_strategy",
            "target_operation_strategy",
            "fact_rows",
            "fact_amount",
            "reason",
        ],
    )
    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "scbs_project_count": len(projects),
        "planned_project_updates": len(to_update),
        "payment_joint_rows_after": payment_joint,
        "contract_joint_rows_after": contract_joint,
        "plan_csv": str(plan_csv),
    }
    write_json(result_json, payload)
    print("SCBS_OPERATION_STRATEGY_POLICY_REFRESH=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
