#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate and validate user decisions for project master review queues.

This script is offline and read-only. It turns the reconciliation package into
a decision template that can be filled by business users before any write
script is allowed to create aliases, pick duplicate carriers, or exclude rows.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


PACKAGE_ID = "user_project_master_reconciliation_20260520"
DEFAULT_INPUT_DIR = Path("/tmp/project_master_stabilization_host")
DEFAULT_OUTPUT = Path("artifacts/project_master_stabilization/user_project_master_review_decisions_20260520.csv")

DECISIONS = {
    "missing_project": {
        "alias_existing_project",
        "create_project",
        "exclude_from_user_baseline",
        "needs_more_evidence",
    },
    "duplicate_canonical": {
        "confirm_canonical_project",
        "choose_other_project",
        "needs_more_evidence",
    },
    "exact_without_business_evidence": {
        "keep_confirmed",
        "exclude_from_user_baseline",
        "needs_more_evidence",
    },
}

FIELDNAMES = [
    "review_id",
    "review_type",
    "source_project_name",
    "operation_strategy",
    "current_status",
    "recommended_action",
    "recommended_project_id",
    "recommended_project_name",
    "recommended_reason",
    "candidate_project_ids",
    "candidate_summary",
    "business_evidence",
    "allowed_decisions",
    "user_decision",
    "target_project_id",
    "target_project_name",
    "create_project_name",
    "reviewer",
    "reviewed_at",
    "review_note",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compact_evidence(value: str, limit: int = 8) -> str:
    parts = [part for part in (value or "").split(";") if part]
    return ";".join(parts[:limit])


def package_paths(input_dir: Path) -> dict[str, Path]:
    return {
        "missing": input_dir / f"{PACKAGE_ID}_missing_review.csv",
        "duplicates": input_dir / f"{PACKAGE_ID}_duplicate_canonical_review.csv",
        "no_evidence": input_dir / f"{PACKAGE_ID}_no_evidence_review.csv",
    }


def build_missing_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for idx, row in enumerate(rows, 1):
        source_name = row.get("source_project_name", "")
        output.append(
            {
                "review_id": f"missing-{idx:03d}",
                "review_type": "missing_project",
                "source_project_name": source_name,
                "operation_strategy": row.get("operation_strategy", ""),
                "current_status": row.get("status", ""),
                "recommended_action": row.get("proposed_action", ""),
                "business_evidence": row.get("text_evidence_tables", ""),
                "allowed_decisions": "|".join(sorted(DECISIONS["missing_project"])),
                "create_project_name": source_name,
                "review_note": row.get("review_note", ""),
            }
        )
    return output


def build_no_evidence_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for idx, row in enumerate(rows, 1):
        output.append(
            {
                "review_id": f"no-evidence-{idx:03d}",
                "review_type": "exact_without_business_evidence",
                "source_project_name": row.get("source_project_name", ""),
                "operation_strategy": row.get("operation_strategy", ""),
                "current_status": row.get("status", ""),
                "recommended_action": row.get("proposed_action", ""),
                "recommended_project_id": row.get("canonical_project_id", ""),
                "recommended_project_name": row.get("canonical_project_name", ""),
                "recommended_reason": row.get("canonical_reason", ""),
                "candidate_project_ids": row.get("canonical_project_id", ""),
                "candidate_summary": row.get("canonical_project_name", ""),
                "allowed_decisions": "|".join(sorted(DECISIONS["exact_without_business_evidence"])),
            }
        )
    return output


def build_duplicate_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("source_project_name", "")].append(row)

    output = []
    for idx, (source_name, candidates) in enumerate(grouped.items(), 1):
        recommended = next((row for row in candidates if row.get("recommended") == "True"), None)
        candidate_ids = [row.get("candidate_project_id", "") for row in candidates if row.get("candidate_project_id")]
        summaries = []
        evidence = []
        for row in candidates:
            project_id = row.get("candidate_project_id", "")
            name = row.get("candidate_project_name", "")
            total = row.get("candidate_evidence_total", "0")
            marker = "recommended" if row.get("recommended") == "True" else "candidate"
            summaries.append(f"{project_id}:{name}:evidence={total}:{marker}")
            if row.get("candidate_evidence_tables"):
                evidence.append(f"{project_id}[{compact_evidence(row.get('candidate_evidence_tables', ''))}]")
        output.append(
            {
                "review_id": f"duplicate-{idx:03d}",
                "review_type": "duplicate_canonical",
                "source_project_name": source_name,
                "operation_strategy": candidates[0].get("operation_strategy", "") if candidates else "",
                "current_status": "duplicate_with_canonical_candidate",
                "recommended_action": "confirm_canonical_project_before_write",
                "recommended_project_id": recommended.get("candidate_project_id", "") if recommended else "",
                "recommended_project_name": recommended.get("candidate_project_name", "") if recommended else "",
                "recommended_reason": recommended.get("recommend_reason", "") if recommended else "manual_review_required",
                "candidate_project_ids": "|".join(candidate_ids),
                "candidate_summary": " || ".join(summaries),
                "business_evidence": " || ".join(evidence),
                "allowed_decisions": "|".join(sorted(DECISIONS["duplicate_canonical"])),
                "target_project_id": recommended.get("candidate_project_id", "") if recommended else "",
                "target_project_name": recommended.get("candidate_project_name", "") if recommended else "",
            }
        )
    return output


def build_template(input_dir: Path, output_csv: Path, summary_json: Path) -> dict[str, object]:
    paths = package_paths(input_dir)
    rows = []
    rows.extend(build_duplicate_rows(read_csv(paths["duplicates"])))
    rows.extend(build_missing_rows(read_csv(paths["missing"])))
    rows.extend(build_no_evidence_rows(read_csv(paths["no_evidence"])))
    write_csv(output_csv, rows)
    payload = {
        "status": "PASS",
        "mode": "user_project_master_review_decision_template",
        "input_dir": str(input_dir),
        "output_csv": str(output_csv),
        "row_count": len(rows),
        "review_type_counts": dict(Counter(row["review_type"] for row in rows)),
        "readonly": True,
        "write_boundary": "Template only. No project creation, alias write, merge, project_id relink, or business fact mutation.",
    }
    write_json(summary_json, payload)
    return payload


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_decision_row(row: dict[str, str]) -> list[str]:
    errors: list[str] = []
    review_id = row.get("review_id") or "<blank>"
    review_type = row.get("review_type", "")
    decision = row.get("user_decision", "").strip()
    allowed = DECISIONS.get(review_type)
    require(bool(allowed), errors, f"{review_id}: unknown review_type={review_type}")
    if not allowed:
        return errors
    require(bool(decision), errors, f"{review_id}: user_decision is required")
    require(decision in allowed, errors, f"{review_id}: invalid user_decision={decision}")

    candidate_ids = {item for item in row.get("candidate_project_ids", "").split("|") if item}
    target_id = row.get("target_project_id", "").strip()
    create_name = row.get("create_project_name", "").strip()

    if review_type == "duplicate_canonical":
        if decision == "confirm_canonical_project":
            require(target_id == row.get("recommended_project_id", "").strip(), errors, f"{review_id}: target must equal recommended_project_id")
        if decision == "choose_other_project":
            require(target_id in candidate_ids, errors, f"{review_id}: target_project_id must be one of candidate_project_ids")
    elif review_type == "missing_project":
        if decision == "alias_existing_project":
            require(bool(target_id), errors, f"{review_id}: alias_existing_project requires target_project_id")
        if decision == "create_project":
            require(bool(create_name), errors, f"{review_id}: create_project requires create_project_name")
    elif review_type == "exact_without_business_evidence":
        if decision == "keep_confirmed":
            require(target_id in {"", row.get("recommended_project_id", "").strip()}, errors, f"{review_id}: keep_confirmed cannot choose another target")

    if decision not in {"needs_more_evidence"}:
        require(bool(row.get("reviewer", "").strip()), errors, f"{review_id}: reviewer is required")
        require(bool(row.get("reviewed_at", "").strip()), errors, f"{review_id}: reviewed_at is required")
    return errors


def validate_decisions(path: Path, summary_json: Path) -> dict[str, object]:
    rows = read_csv(path)
    errors = []
    for row in rows:
        errors.extend(validate_decision_row(row))
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "mode": "user_project_master_review_decision_validate",
        "input_csv": str(path),
        "row_count": len(rows),
        "decision_counts": dict(Counter(row.get("user_decision", "") for row in rows)),
        "error_count": len(errors),
        "errors": errors[:100],
        "readonly": True,
    }
    write_json(summary_json, payload)
    print("USER_PROJECT_MASTER_REVIEW_DECISION_VALIDATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if errors:
        raise SystemExit(1)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--summary-json", default="")
    parser.add_argument("--validate-decisions", default="")
    args = parser.parse_args()

    out = Path(args.out)
    summary_json = Path(args.summary_json) if args.summary_json else out.with_suffix(".json")
    if args.validate_decisions:
        validate_decisions(Path(args.validate_decisions), summary_json)
        return 0

    payload = build_template(Path(args.input_dir), out, summary_json)
    print("USER_PROJECT_MASTER_REVIEW_DECISION_TEMPLATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
