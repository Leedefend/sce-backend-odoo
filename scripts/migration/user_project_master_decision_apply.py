# -*- coding: utf-8 -*-
"""Apply the user-confirmed project master review decisions.

The decision CSV is the business-reviewed closure for the unresolved rows from
the project master reconciliation package. This script only mutates
``project.project`` master data: names, operation strategy, active state, and
the implied project category. It never relinks contracts, payments, SCBS rows,
or other business facts.

Default mode is dry-run. Set APPLY=1 to write.
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_SOURCE = "migration_assets/10_master/project/user_project_name_strategy_20260520.csv"
DEFAULT_DECISIONS = "migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv"
SOURCE_TAG = "user_project_master_decision_20260521"
EXPECTED_SOURCE_COUNTS = {"direct": 41, "joint": 693}
EXPECTED_DECISION_COUNTS = {
    "alias_existing_project": 1,
    "confirm_canonical_project": 10,
    "exclude_from_user_baseline": 18,
}


def repo_root() -> Path:
    candidates = [
        Path.cwd(),
        Path("/mnt/extra-addons"),
        Path("/home/odoo/workspace/sce-backend-odoo"),
    ]
    for candidate in candidates:
        if (candidate / "addons").exists() and (candidate / "migration_assets").exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT") or "/tmp/project_master_stabilization")
    root.mkdir(parents=True, exist_ok=True)
    return root


def asset_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    if raw.startswith("migration_assets/") and Path("/mnt/migration_assets").exists():
        return Path("/mnt/migration_assets") / raw[len("migration_assets/") :]
    return repo_root() / path


def source_path() -> Path:
    return asset_path(os.getenv("MIGRATION_USER_PROJECT_STRATEGY_CSV") or DEFAULT_SOURCE)


def decision_path() -> Path:
    return asset_path(os.getenv("PROJECT_MASTER_REVIEW_DECISION_CSV") or DEFAULT_DECISIONS)


def normalize_name(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", "", text)
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("－", "-").replace("—", "-").replace("–", "-")
    return text.rstrip(".")


def project_name(project) -> str:
    name = project.with_context(lang="zh_CN").name
    if isinstance(name, dict):
        return name.get("zh_CN") or name.get("en_US") or next(iter(name.values()), "") or ""
    return str(name or "")


def project_name_by_lang(project, lang: str) -> str:
    name = project.with_context(lang=lang).name
    if isinstance(name, dict):
        return name.get(lang) or name.get("zh_CN") or name.get("en_US") or next(iter(name.values()), "") or ""
    return str(name or "")


def project_name_needs_write(project, desired_name: str) -> bool:
    return any(project_name_by_lang(project, lang) != desired_name for lang in ("zh_CN", "en_US"))


def write_project(project, vals: dict[str, object]) -> None:
    name = vals.pop("name", None)
    if vals:
        project.with_context(tracking_disable=True).write(vals)
    if name:
        for lang in ("zh_CN", "en_US"):
            project.with_context(lang=lang, tracking_disable=True).write({"name": name})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise RuntimeError(f"CSV missing: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_source_rows(path: Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv(path)
    if not rows:
        raise RuntimeError("source CSV is empty")
    required = {"project_name", "operation_strategy"}
    missing = required - set(rows[0].keys())
    if missing:
        raise RuntimeError(f"source CSV missing headers: {sorted(missing)}")
    counts = Counter(row.get("operation_strategy") for row in rows)
    if dict(counts) != EXPECTED_SOURCE_COUNTS:
        raise RuntimeError(f"source strategy counts mismatch: {dict(counts)} != {EXPECTED_SOURCE_COUNTS}")
    by_key: dict[str, dict[str, str]] = {}
    duplicates = []
    for row in rows:
        key = normalize_name(row.get("project_name"))
        if not key:
            raise RuntimeError("source CSV has blank project_name")
        if key in by_key:
            duplicates.append(row.get("project_name", ""))
        by_key[key] = row
    if duplicates:
        raise RuntimeError(f"source CSV has duplicate normalized names: {duplicates[:20]}")
    return rows, by_key


def load_decisions(path: Path) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv(path)
    if not rows:
        raise RuntimeError("decision CSV is empty")
    errors: list[str] = []
    by_key: dict[str, dict[str, str]] = {}
    for row in rows:
        review_id = row.get("review_id") or "<blank>"
        decision = (row.get("user_decision") or "").strip()
        review_type = (row.get("review_type") or "").strip()
        key = normalize_name(row.get("source_project_name"))
        require(bool(key), f"{review_id}: source_project_name is required", errors)
        require(bool(row.get("reviewer", "").strip()), f"{review_id}: reviewer is required", errors)
        require(bool(row.get("reviewed_at", "").strip()), f"{review_id}: reviewed_at is required", errors)
        require(decision in {"alias_existing_project", "confirm_canonical_project", "exclude_from_user_baseline"}, f"{review_id}: unsupported decision={decision}", errors)
        require(review_type in {"duplicate_canonical", "missing_project", "exact_without_business_evidence"}, f"{review_id}: unsupported review_type={review_type}", errors)
        if decision == "confirm_canonical_project":
            require(review_type == "duplicate_canonical", f"{review_id}: confirm_canonical_project only applies to duplicate rows", errors)
            require(row.get("target_project_id", "").strip() == row.get("recommended_project_id", "").strip(), f"{review_id}: target_project_id must equal recommended_project_id", errors)
        if decision == "alias_existing_project":
            require(review_type == "missing_project", f"{review_id}: alias_existing_project only applies to missing rows", errors)
            require(bool(row.get("target_project_id", "").strip()), f"{review_id}: target_project_id is required", errors)
        if key in by_key:
            errors.append(f"{review_id}: duplicate decision source name={row.get('source_project_name')}")
        by_key[key] = row
    counts = Counter(row.get("user_decision") for row in rows)
    if dict(counts) != EXPECTED_DECISION_COUNTS:
        errors.append(f"decision counts mismatch: {dict(counts)} != {EXPECTED_DECISION_COUNTS}")
    if errors:
        raise RuntimeError({"decision_errors": errors[:100], "error_count": len(errors)})
    return rows, by_key


def build_project_index():
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    projects = Project.search([], order="id")
    by_name = defaultdict(lambda: Project.browse())
    by_id = {}
    for project in projects:
        by_name[normalize_name(project_name(project))] |= project
        by_id[project.id] = project
    return Project, projects, by_name, by_id


def parse_ids(value: str) -> list[int]:
    ids = []
    for item in (value or "").split("|"):
        item = item.strip()
        if not item:
            continue
        try:
            ids.append(int(item))
        except ValueError as exc:
            raise RuntimeError(f"invalid project id in candidate list: {item}") from exc
    return ids


def operation_strategy_for(source_by_key: dict[str, dict[str, str]], row: dict[str, str]) -> str:
    key = normalize_name(row.get("source_project_name"))
    source = source_by_key.get(key)
    strategy = (source or row).get("operation_strategy", "").strip()
    if strategy not in {"direct", "joint"}:
        raise RuntimeError(f"invalid operation_strategy for {row.get('source_project_name')}: {strategy}")
    return strategy


def plan_record(
    *,
    source_name: str,
    source_strategy: str,
    project,
    outcome: str,
    action: str,
    reason: str,
    target_name: str = "",
) -> dict[str, object]:
    return {
        "source_project_name": source_name,
        "source_operation_strategy": source_strategy,
        "project_id": project.id if project else "",
        "current_project_name": project_name(project) if project else "",
        "target_project_name": target_name or source_name,
        "current_operation_strategy": (project.operation_strategy or "") if project else "",
        "active": bool(project.active) if project else "",
        "outcome": outcome,
        "action": action,
        "reason": reason,
    }


def main() -> None:
    apply = os.getenv("APPLY") == "1"
    archive_excluded = os.getenv("ARCHIVE_EXCLUDED", "1") != "0"
    archive_out_of_baseline = os.getenv("ARCHIVE_OUT_OF_BASELINE") == "1"
    source = source_path()
    decisions = decision_path()
    source_rows, source_by_key = load_source_rows(source)
    decision_rows, decisions_by_key = load_decisions(decisions)
    Project, all_projects, projects_by_name, projects_by_id = build_project_index()

    plan_rows: list[dict[str, object]] = []
    accepted_project_ids: set[int] = set()
    excluded_project_ids: set[int] = set()
    errors: list[str] = []

    def accept_project(project, source_name: str, strategy: str, reason: str, target_name: str = "") -> None:
        accepted_project_ids.add(project.id)
        desired_name = target_name or source_name
        vals = {}
        if project_name_needs_write(project, desired_name):
            vals["name"] = desired_name
        if (project.operation_strategy or "") != strategy:
            vals["operation_strategy"] = strategy
        if not project.active:
            vals["active"] = True
        action = "write_accept" if vals else "keep_accept"
        plan_rows.append(
            plan_record(
                source_name=source_name,
                source_strategy=strategy,
                project=project,
                outcome="accepted_user_baseline",
                action=action,
                reason=reason,
                target_name=desired_name,
            )
        )
        if apply and vals:
            write_project(project, vals)

    for row in source_rows:
        key = normalize_name(row.get("project_name"))
        if key in decisions_by_key:
            continue
        strategy = row.get("operation_strategy", "").strip()
        projects = projects_by_name.get(key, Project.browse())
        if len(projects) != 1:
            errors.append(f"unresolved exact source without decision: {row.get('project_name')} matches={projects.ids}")
            continue
        accept_project(projects[0], row["project_name"].strip(), strategy, "exact_business_evidence")

    for row in decision_rows:
        source_name = row.get("source_project_name", "").strip()
        strategy = operation_strategy_for(source_by_key, row)
        decision = row.get("user_decision", "").strip()
        review_type = row.get("review_type", "").strip()
        if decision == "confirm_canonical_project":
            target_id = int(row["target_project_id"])
            project = projects_by_id.get(target_id)
            if not project:
                errors.append(f"{row.get('review_id')}: target project missing: {target_id}")
                continue
            accept_project(project, source_name, strategy, "duplicate_canonical_user_confirmed")
            for candidate_id in parse_ids(row.get("candidate_project_ids", "")):
                if candidate_id != target_id:
                    excluded_project_ids.add(candidate_id)
        elif decision == "alias_existing_project":
            target_id = int(row["target_project_id"])
            project = projects_by_id.get(target_id)
            if not project:
                errors.append(f"{row.get('review_id')}: target project missing: {target_id}")
                continue
            target_name = row.get("create_project_name", "").strip() or source_name
            accept_project(project, source_name, strategy, "missing_alias_user_confirmed", target_name=target_name)
        elif decision == "exclude_from_user_baseline":
            candidate_ids = parse_ids(row.get("candidate_project_ids", ""))
            for candidate_id in candidate_ids:
                excluded_project_ids.add(candidate_id)
            plan_rows.append(
                plan_record(
                    source_name=source_name,
                    source_strategy=strategy,
                    project=False,
                    outcome="excluded_user_baseline",
                    action="no_project_write" if not candidate_ids else "archive_existing_candidates",
                    reason=f"{review_type}_user_excluded",
                )
            )

    excluded_project_ids -= accepted_project_ids
    for project_id in sorted(excluded_project_ids):
        project = projects_by_id.get(project_id)
        if not project:
            errors.append(f"excluded project missing: {project_id}")
            continue
        action = "archive_excluded" if project.active and archive_excluded else "keep_excluded_inactive"
        plan_rows.append(
            plan_record(
                source_name="",
                source_strategy="",
                project=project,
                outcome="excluded_project_candidate",
                action=action,
                reason="user_decision_excluded_or_noncanonical_candidate",
                target_name=project_name(project),
            )
        )
        if apply and project.active and archive_excluded:
            project.with_context(tracking_disable=True).write({"active": False})

    if archive_out_of_baseline:
        protected_project_ids = accepted_project_ids | excluded_project_ids
        for project in all_projects:
            if project.id in protected_project_ids or not project.active:
                continue
            action = "archive_out_of_user_baseline"
            plan_rows.append(
                plan_record(
                    source_name="",
                    source_strategy="",
                    project=project,
                    outcome="out_of_user_baseline_active_project",
                    action=action,
                    reason="active_project_not_in_user_confirmed_baseline",
                    target_name=project_name(project),
                )
            )
            if apply:
                project.with_context(tracking_disable=True).write({"active": False})

    if errors:
        raise RuntimeError({"planning_errors": errors[:100], "error_count": len(errors)})

    if apply:
        env.cr.commit()  # noqa: F821

    root = artifact_root()
    plan_csv = root / "user_project_master_decision_apply_plan_20260521.csv"
    result_json = root / "user_project_master_decision_apply_result_20260521.json"
    fieldnames = [
        "source_project_name",
        "source_operation_strategy",
        "project_id",
        "current_project_name",
        "target_project_name",
        "current_operation_strategy",
        "active",
        "outcome",
        "action",
        "reason",
    ]
    write_csv(plan_csv, plan_rows, fieldnames)

    payload = {
        "status": "APPLIED" if apply else "DRY_RUN",
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source),
        "decision_csv": str(decisions),
        "source_rows": len(source_rows),
        "decision_rows": len(decision_rows),
        "accepted_project_count": len(accepted_project_ids),
        "excluded_project_count": len(excluded_project_ids),
        "outcome_counts": dict(Counter(row["outcome"] for row in plan_rows)),
        "action_counts": dict(Counter(row["action"] for row in plan_rows)),
        "archive_excluded": archive_excluded,
        "archive_out_of_baseline": archive_out_of_baseline,
        "plan_csv": str(plan_csv),
        "result_json": str(result_json),
        "boundary": "project.project master data only; no project_id, legacy_project_id, contract, payment, SCBS, or other business fact relink",
    }
    write_json(result_json, payload)
    print("USER_PROJECT_MASTER_DECISION_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
