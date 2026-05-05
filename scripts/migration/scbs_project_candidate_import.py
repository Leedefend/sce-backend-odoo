"""Import SCBS GCMC project candidates into an Odoo review mapping table.

Run through Odoo shell:

    odoo shell -c /var/lib/odoo/odoo.conf -d sc_prod_sim \\
      < scripts/migration/scbs_project_candidate_import.py

Default mode is dry-run. To write, set:

    SCBS_PROJECT_CANDIDATE_IMPORT_MODE=write

The script consumes ``artifacts/migration/scbs_project_candidates_v1.csv``.
It creates or updates ``sc.legacy.project.map`` rows only. It never creates
``project.project`` rows and never rewrites existing project business facts.
"""

from __future__ import annotations

import csv
import json
import os
from difflib import SequenceMatcher
from pathlib import Path


def clean(value) -> str:
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def as_int(value) -> int:
    text = clean(value)
    return int(float(text)) if text else 0


def as_float(value) -> float:
    text = clean(value)
    if text in {"", "."}:
        return 0.0
    if text.startswith("."):
        text = "0" + text
    return float(text)


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/scbs_project_candidates_v1.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root(root: Path) -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([root / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821 - Odoo shell global
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_rows(path: Path) -> list[dict[str, str]]:
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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def all_project_candidates() -> list[tuple[int, str]]:
    Project = env["project.project"]  # noqa: F821
    projects = Project.with_context(active_test=False).search([])
    return [(project.id, clean(project.name)) for project in projects if clean(project.name)]


def exact_project(name: str):
    Project = env["project.project"]  # noqa: F821
    matches = Project.with_context(active_test=False).search([("name", "=", name)], limit=2)
    return matches if len(matches) == 1 else Project.browse()


def fuzzy_suggestions(name: str, candidates: list[tuple[int, str]]) -> list[dict[str, object]]:
    scored = []
    for project_id, project_name in candidates:
        ratio = SequenceMatcher(None, name, project_name).ratio()
        if name in project_name or project_name in name:
            ratio = max(ratio, 0.72)
        if ratio >= 0.55:
            scored.append({"project_id": project_id, "project_name": project_name, "score": round(ratio, 4)})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:5]


def default_mapping_state(suggested_state: str) -> str:
    return "conflict" if suggested_state == "not_real_project_review" else "candidate"


def base_confidence(suggested_state: str, project) -> float:
    if project:
        return 0.95
    if suggested_state == "project_candidate":
        return 0.72
    if suggested_state == "single_source_project_candidate":
        return 0.45
    return 0.2


def evidence(row: dict[str, str], fuzzy: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "source": "scbs_project_candidates_v1.csv",
            "suggested_state": clean(row.get("suggested_state")),
            "fuzzy_suggestions": fuzzy,
            "source_count": as_int(row.get("source_count")),
            "rows_total": as_int(row.get("rows_total")),
            "amount_total": as_float(row.get("amount_total")),
            "payment_rows": as_int(row.get("payment_rows")),
            "payment_amount": as_float(row.get("payment_amount")),
            "contract_rows": as_int(row.get("contract_rows")),
            "contract_amount": as_float(row.get("contract_amount")),
            "stock_rows": as_int(row.get("stock_rows")),
            "stock_amount": as_float(row.get("stock_amount")),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def main() -> None:
    ensure_allowed_db()
    mode = os.getenv("SCBS_PROJECT_CANDIDATE_IMPORT_MODE", "dry-run")
    write_mode = mode == "write"
    if mode not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_mode": mode, "expected": ["dry-run", "write"]})

    root = repo_root()
    artifacts = artifact_root(root)
    input_csv = root / "artifacts/migration/scbs_project_candidates_v1.csv"
    result_json = artifacts / "scbs_project_candidate_import_result_v1.json"
    rollback_csv = artifacts / "scbs_project_candidate_import_rollback_targets_v1.csv"
    preview_csv = artifacts / "scbs_project_candidate_import_preview_v1.csv"

    rows = read_rows(input_csv)
    company = env.company  # noqa: F821
    Mapping = env["sc.legacy.project.map"]  # noqa: F821
    project_candidates = all_project_candidates()

    preview_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    created_maps = 0
    updated_maps = 0

    allowed_states = {"project_candidate", "single_source_project_candidate", "not_real_project_review"}
    for index, row in enumerate(rows, start=2):
        legacy_gcmc = clean(row.get("legacy_gcmc"))
        suggested_state = clean(row.get("suggested_state"))
        if not legacy_gcmc:
            errors.append({"line": index, "error": "missing_legacy_gcmc"})
            continue
        if suggested_state not in allowed_states:
            errors.append({"line": index, "legacy_gcmc": legacy_gcmc, "error": "unexpected_suggested_state"})
            continue

        project = env["project.project"].browse()  # noqa: F821
        fuzzy = []
        if suggested_state != "not_real_project_review":
            project = exact_project(legacy_gcmc)
            fuzzy = [] if project else fuzzy_suggestions(legacy_gcmc, project_candidates)
        mapping = Mapping.search(
            [
                ("source_table", "=", "SCBS_GCMC_PROJECT_CANDIDATE"),
                ("legacy_gcmc", "=", legacy_gcmc),
            ],
            limit=1,
        )
        match_method = "exact" if project else "fuzzy" if fuzzy else "none"
        vals = {
            "source_table": "SCBS_GCMC_PROJECT_CANDIDATE",
            "source_domain": "SCBS",
            "legacy_gcmc": legacy_gcmc,
            "company_id": company.id,
            "project_id": project.id if project else False,
            "mapping_state": default_mapping_state(suggested_state),
            "suggested_state": suggested_state,
            "match_method": match_method,
            "confidence": base_confidence(suggested_state, project),
            "source_count": as_int(row.get("source_count")),
            "rows_total": as_int(row.get("rows_total")),
            "amount_total": as_float(row.get("amount_total")),
            "min_date": clean(row.get("min_date")) or False,
            "max_date": clean(row.get("max_date")) or False,
            "payment_rows": as_int(row.get("payment_rows")),
            "payment_amount": as_float(row.get("payment_amount")),
            "contract_rows": as_int(row.get("contract_rows")),
            "contract_amount": as_float(row.get("contract_amount")),
            "stock_rows": as_int(row.get("stock_rows")),
            "stock_amount": as_float(row.get("stock_amount")),
            "evidence": evidence(row, fuzzy),
        }
        preview_rows.append(
            {
                "legacy_gcmc": legacy_gcmc,
                "suggested_state": suggested_state,
                "map_action": "update" if mapping else "create",
                "mapping_state": vals["mapping_state"],
                "project_id": project.id if project else "",
                "project_name": project.name if project else "",
                "match_method": match_method,
                "confidence": vals["confidence"],
                "fuzzy_count": len(fuzzy),
                "rows_total": vals["rows_total"],
                "amount_total": vals["amount_total"],
            }
        )

        if not write_mode:
            continue

        if mapping:
            mapping.write(vals)
            updated_maps += 1
        else:
            mapping = Mapping.create(vals)
            created_maps += 1
        rollback_rows.append(
            {
                "model": "sc.legacy.project.map",
                "id": mapping.id,
                "legacy_gcmc": legacy_gcmc,
                "name": mapping.legacy_gcmc,
            }
        )

    preview_fields = [
        "legacy_gcmc",
        "suggested_state",
        "map_action",
        "mapping_state",
        "project_id",
        "project_name",
        "match_method",
        "confidence",
        "fuzzy_count",
        "rows_total",
        "amount_total",
    ]
    write_csv(preview_csv, preview_fields, preview_rows)
    write_csv(rollback_csv, ["model", "id", "legacy_gcmc", "name"], rollback_rows)

    if errors:
        payload = {
            "status": "FAIL",
            "mode": mode,
            "database": env.cr.dbname,  # noqa: F821
            "input_csv": str(input_csv),
            "errors": errors,
            "preview_csv": str(preview_csv),
        }
        write_json(result_json, payload)
        raise RuntimeError(payload)

    if write_mode:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "input_csv": str(input_csv),
        "candidate_rows": len(rows),
        "preview_rows": len(preview_rows),
        "created_maps": created_maps,
        "updated_maps": updated_maps,
        "preview_csv": str(preview_csv),
        "rollback_csv": str(rollback_csv),
        "mapping_count": Mapping.search_count([("source_table", "=", "SCBS_GCMC_PROJECT_CANDIDATE")]),
    }
    write_json(result_json, payload)
    print("SCBS_PROJECT_CANDIDATE_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
