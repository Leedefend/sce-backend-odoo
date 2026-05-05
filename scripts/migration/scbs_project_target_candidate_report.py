"""Export target project candidates for SCBS project mapping decisions."""

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
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fact_stats_by_project_map() -> dict[int, dict[str, object]]:
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    groups = Staging.read_group(
        [("project_map_id", "!=", False), ("import_batch", "=", "scbs_fact_staging_v1")],
        ["project_map_id", "amount_total:sum", "__count"],
        ["project_map_id"],
        lazy=False,
    )
    stats: dict[int, dict[str, object]] = {}
    for row in groups:
        value = row.get("project_map_id")
        if not value:
            continue
        stats[value[0]] = {
            "fact_rows": row.get("__count", 0),
            "fact_amount": round(float(row.get("amount_total", 0.0) or 0.0), 2),
        }
    return stats


def project_identity(project) -> dict[str, object]:
    return {
        "candidate_project_id": project.id,
        "candidate_name": project.display_name,
        "candidate_active": project.active,
        "candidate_company": project.company_id.display_name if project.company_id else "",
        "candidate_stage": project.stage_id.display_name if getattr(project, "stage_id", False) else "",
    }


def fuzzy_from_evidence(mapping) -> list[dict[str, object]]:
    if not mapping.evidence:
        return []
    try:
        payload = json.loads(mapping.evidence)
    except Exception:
        return []
    return list(payload.get("fuzzy_suggestions") or [])


def suggested_action(mapping) -> str:
    if "测试" in (mapping.legacy_gcmc or ""):
        return "ignore_or_conflict_test_value"
    if mapping.suggested_state in {"not_real_project_review", "ignored_test_candidate"}:
        return "ignore_if_not_real_project"
    return "confirm_or_ignore_project"


def candidate_rows_for_mapping(mapping, fact_stat: dict[str, object]) -> list[dict[str, object]]:
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    candidates: dict[int, dict[str, object]] = {}

    def add(project, reason: str, rank: int, confidence: float) -> None:
        row = candidates.setdefault(project.id, project_identity(project))
        existing_rank = int(row.get("candidate_rank", 999))
        if rank < existing_rank:
            row.update({"match_reason": reason, "candidate_rank": rank, "confidence": confidence})
        else:
            row["match_reason"] = f"{row.get('match_reason', '')};{reason}".strip(";")

    if mapping.project_id:
        add(mapping.project_id, "current_mapping_target", 0, 1.0)
    exact_matches = Project.search([("name", "=", mapping.legacy_gcmc)], limit=20)
    for project in exact_matches:
        add(project, "name_exact", 1, 0.95)
    for suggestion in fuzzy_from_evidence(mapping):
        project = Project.browse(int(suggestion.get("project_id") or 0))
        if project.exists():
            add(project, "fuzzy_suggestion", 2, float(suggestion.get("score") or 0.0))

    rows = []
    for candidate in sorted(candidates.values(), key=lambda row: (int(row.get("candidate_rank", 999)), -float(row.get("confidence") or 0.0))):
        rows.append(
            {
                "map_id": mapping.id,
                "legacy_gcmc": mapping.legacy_gcmc,
                "suggested_state": mapping.suggested_state,
                "mapping_state": mapping.mapping_state,
                "map_match_method": mapping.match_method,
                "suggested_action": suggested_action(mapping),
                "fact_rows": fact_stat.get("fact_rows", mapping.rows_total or 0),
                "fact_amount": fact_stat.get("fact_amount", round(mapping.amount_total or 0.0, 2)),
                **candidate,
            }
        )
    if not rows:
        rows.append(
            {
                "map_id": mapping.id,
                "legacy_gcmc": mapping.legacy_gcmc,
                "suggested_state": mapping.suggested_state,
                "mapping_state": mapping.mapping_state,
                "map_match_method": mapping.match_method,
                "suggested_action": suggested_action(mapping),
                "fact_rows": fact_stat.get("fact_rows", mapping.rows_total or 0),
                "fact_amount": fact_stat.get("fact_amount", round(mapping.amount_total or 0.0, 2)),
                "candidate_rank": "",
                "match_reason": "no_target_candidate_found",
                "confidence": 0.0,
                "candidate_project_id": "",
                "candidate_name": "",
                "candidate_active": "",
                "candidate_company": "",
                "candidate_stage": "",
            }
        )
    return rows


def main() -> None:
    artifacts = artifact_root()
    report_csv = artifacts / "scbs_project_target_candidate_report_v1.csv"
    result_json = artifacts / "scbs_project_target_candidate_report_result_v1.json"
    Mapping = env["sc.legacy.project.map"].sudo().with_context(active_test=False)  # noqa: F821
    fact_stats = fact_stats_by_project_map()
    mappings = Mapping.search(
        [
            ("id", "in", list(fact_stats)),
            ("source_domain", "=", "SCBS"),
            ("mapping_state", "!=", "confirmed"),
        ]
    )
    rows: list[dict[str, object]] = []
    for mapping in mappings:
        rows.extend(candidate_rows_for_mapping(mapping, fact_stats.get(mapping.id, {})))
    rows.sort(key=lambda row: (str(row["suggested_action"]), -float(row["fact_amount"] or 0.0), int(row["map_id"]), int(row["candidate_rank"] or 999)))
    fieldnames = [
        "map_id",
        "legacy_gcmc",
        "suggested_state",
        "mapping_state",
        "map_match_method",
        "suggested_action",
        "fact_rows",
        "fact_amount",
        "candidate_rank",
        "match_reason",
        "confidence",
        "candidate_project_id",
        "candidate_name",
        "candidate_active",
        "candidate_company",
        "candidate_stage",
    ]
    write_csv(report_csv, fieldnames, rows)
    summary: dict[str, dict[str, int | float]] = {}
    for row in rows:
        action = str(row["suggested_action"])
        bucket = summary.setdefault(action, {"candidate_rows": 0, "mapping_rows": 0, "with_candidate": 0, "fact_rows": 0, "fact_amount": 0.0})
        bucket["candidate_rows"] = int(bucket["candidate_rows"]) + 1
        if row.get("candidate_project_id"):
            bucket["with_candidate"] = int(bucket["with_candidate"]) + 1
    for action, bucket in summary.items():
        map_ids = {row["map_id"] for row in rows if row["suggested_action"] == action}
        bucket["mapping_rows"] = len(map_ids)
        bucket["fact_rows"] = sum(int(fact_stats.get(int(map_id), {}).get("fact_rows", 0) or 0) for map_id in map_ids)
        bucket["fact_amount"] = round(sum(float(fact_stats.get(int(map_id), {}).get("fact_amount", 0.0) or 0.0) for map_id in map_ids), 2)
    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "report_csv": str(report_csv),
        "candidate_rows": len(rows),
        "mapping_rows": len({row["map_id"] for row in rows}),
        "summary": summary,
    }
    write_json(result_json, payload)
    print("SCBS_PROJECT_TARGET_CANDIDATE_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
