"""Confirm strong single-candidate SCBS project mappings.

Input is the refreshed project target candidate report. A project mapping is
confirmed only when exactly one candidate has:

- confidence >= 0.80;
- legacy project name contained in candidate name, or candidate name contained
  in legacy project name, after bracket normalization;
- current mapping is still candidate and has no target project.

Dry-run by default. Set ``SCBS_STRONG_PROJECT_CONFIRM_APPLY=1`` to write.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

from odoo import fields


BATCH = "scbs_strong_project_candidate_confirm_v1"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path.cwd() / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path("artifacts/migration")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def normalize_name(value: str) -> str:
    return (value or "").strip().replace("（", "(").replace("）", ")").replace(" ", "")


def is_strong(row: dict[str, str]) -> bool:
    if not row.get("candidate_project_id"):
        return False
    try:
        confidence = float(row.get("confidence") or 0.0)
    except Exception:
        return False
    legacy = normalize_name(row.get("legacy_gcmc", ""))
    candidate = normalize_name(row.get("candidate_name", ""))
    return confidence >= 0.80 and bool(legacy and candidate) and (legacy in candidate or candidate in legacy)


def main() -> None:
    artifacts = artifact_root()
    apply = os.getenv("SCBS_STRONG_PROJECT_CONFIRM_APPLY") == "1"
    source_csv = Path(os.getenv("SCBS_PROJECT_TARGET_CANDIDATE_CSV") or artifacts / "scbs_project_target_candidate_report_v1.csv")
    plan_csv = artifacts / "scbs_strong_project_candidate_confirm_plan_v1.csv"
    result_json = artifacts / "scbs_strong_project_candidate_confirm_result_v1.json"

    report_rows = read_csv(source_csv)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in report_rows:
        if row.get("mapping_state") == "candidate" and row.get("suggested_action") == "confirm_or_ignore_project":
            grouped[row["map_id"]].append(row)

    ProjectMap = env["sc.legacy.project.map"].sudo()
    Project = env["project.project"].sudo().with_context(active_test=False)

    plan_rows: list[dict[str, object]] = []
    skipped_multiple_strong = 0
    skipped_stale = 0
    confirmed = 0

    for map_id, rows in grouped.items():
        strong = [row for row in rows if is_strong(row)]
        if not strong:
            continue
        if len(strong) != 1:
            skipped_multiple_strong += 1
            continue
        row = strong[0]
        mapping = ProjectMap.browse(int(map_id))
        target = Project.browse(int(row["candidate_project_id"]))
        if not mapping.exists() or not target.exists() or mapping.mapping_state != "candidate" or mapping.project_id:
            skipped_stale += 1
            continue
        plan_rows.append(
            {
                "map_id": mapping.id,
                "legacy_gcmc": mapping.legacy_gcmc,
                "fact_rows": mapping.rows_total,
                "amount_total": mapping.amount_total,
                "candidate_project_id": target.id,
                "candidate_name": target.display_name,
                "confidence": row.get("confidence", ""),
                "action": "confirm",
            }
        )
        if apply:
            mapping.write(
                {
                    "project_id": target.id,
                    "mapping_state": "confirmed",
                    "match_method": "fuzzy",
                    "reviewer_id": env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                    "note": ((mapping.note or "") + f"\n{BATCH}: strong single candidate {target.display_name}").strip(),
                }
            )
            confirmed += 1

    result = {
        "mode": "apply" if apply else "dry_run",
        "source_csv": str(source_csv),
        "planned_rows": len(plan_rows),
        "confirmed": confirmed,
        "skipped_multiple_strong": skipped_multiple_strong,
        "skipped_stale": skipped_stale,
        "plan_csv": str(plan_csv),
        "result_json": str(result_json),
    }
    write_csv(
        plan_csv,
        plan_rows,
        ["map_id", "legacy_gcmc", "fact_rows", "amount_total", "candidate_project_id", "candidate_name", "confidence", "action"],
    )
    write_json(result_json, result)

    if apply:
        env.cr.commit()

    print("SCBS_STRONG_PROJECT_CONFIRM=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
