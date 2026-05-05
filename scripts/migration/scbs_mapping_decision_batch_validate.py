"""Validate all split SCBS decision workbooks listed in the manifest.

This script is read-only. It validates row-level decisions for each split
workbook and reports whether a batch is ready for dry-run/apply.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


VALID_DECISIONS = {"", "noop", "confirm", "ignore", "conflict"}


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


def manifest_path(artifacts: Path) -> Path:
    raw = os.getenv("SCBS_MAPPING_DECISION_MANIFEST")
    if raw:
        return Path(raw)
    return artifacts / "scbs_mapping_decision_split_workbooks_manifest_v1.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_workbook_path(raw_file: str, manifest: Path, artifacts: Path) -> Path:
    raw_path = Path(raw_file)
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.extend(
            [
                Path.cwd() / raw_path,
                manifest.parent / raw_path.name,
                artifacts / raw_path.name,
                Path("/mnt/artifacts/migration") / raw_path.name,
            ]
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else raw_path


def model_for_dimension(dimension: str):
    if dimension == "business_entity":
        return env["sc.legacy.business.entity.map"].sudo().with_context(active_test=False), "business_entity_id", "sc.business.entity"  # noqa: F821
    if dimension == "project":
        return env["sc.legacy.project.map"].sudo().with_context(active_test=False), "project_id", "project.project"  # noqa: F821
    if dimension == "partner":
        return env["sc.legacy.partner.map"].sudo().with_context(active_test=False), "partner_id", "res.partner"  # noqa: F821
    raise ValueError(f"unsupported dimension: {dimension}")


def find_mapping(row: dict[str, str]):
    dimension = (row.get("dimension") or "").strip()
    Model, _, _ = model_for_dimension(dimension)
    map_model = (row.get("map_model") or "").strip()
    if map_model and map_model != Model._name:
        raise ValueError(f"map_model_mismatch:{map_model}!={Model._name}")
    map_id = (row.get("map_id") or "").strip()
    if map_id:
        rec = Model.browse(int(map_id))
        if rec.exists():
            return rec
    source_table = (row.get("source_table") or "").strip()
    legacy_key = (row.get("legacy_key") or "").strip()
    if dimension == "business_entity":
        domain = [("source_table", "=", source_table), ("legacy_xmid", "=", legacy_key)]
    elif dimension == "project":
        domain = [("source_table", "=", source_table), ("legacy_gcmc", "=", legacy_key)]
    else:
        domain = [("source_table", "=", source_table), ("legacy_key", "=", legacy_key)]
    return Model.search(domain, limit=1)


def target_exists(target_model: str, target_id: str):
    if not target_id:
        return None
    target = env[target_model].sudo().with_context(active_test=False).browse(int(target_id))  # noqa: F821
    return target if target.exists() else None


def validate_row(row: dict[str, str]) -> tuple[str, str]:
    decision = (row.get("decision") or "").strip().lower()
    if decision not in VALID_DECISIONS:
        return "error", f"invalid_decision:{decision}"
    try:
        rec = find_mapping(row)
    except Exception as exc:
        return "error", str(exc)
    if not rec:
        return "error", "mapping_not_found"
    if decision in {"", "noop"}:
        return "blank", "no_decision"
    dimension = (row.get("dimension") or "").strip()
    _, target_field, target_model = model_for_dimension(dimension)
    if decision == "confirm":
        target_id = (row.get("decision_target_id") or row.get("target_id") or "").strip()
        target = target_exists(target_model, target_id)
        if not target:
            return "error", "confirm_requires_existing_target"
        if target_field == "partner_id":
            if rec.suggested_state == "tax_code_conflict" and not (row.get("decision_target_id") or "").strip():
                return "error", "tax_conflict_requires_explicit_decision_target_id"
            if target.company_id and target.company_id != rec.company_id:
                return "error", "target_partner_wrong_company"
        if target_field == "project_id" and target.company_id and target.company_id != rec.company_id:
            return "error", "target_project_wrong_company"
        if target_field == "business_entity_id" and target.company_id != rec.company_id:
            return "error", "target_business_entity_wrong_company"
    return "valid", ""


def validate_workbook(path: Path) -> dict[str, object]:
    rows = read_csv(path)
    counts: dict[str, int] = {}
    error_examples: list[str] = []
    for line, row in enumerate(rows, start=2):
        status, reason = validate_row(row)
        counts[status] = counts.get(status, 0) + 1
        if status == "error" and len(error_examples) < 5:
            error_examples.append(f"line {line}: {reason}")
    decided = counts.get("valid", 0)
    blank = counts.get("blank", 0)
    errors = counts.get("error", 0)
    if errors:
        batch_status = "HAS_ERRORS"
    elif decided and not blank:
        batch_status = "READY"
    elif decided and blank:
        batch_status = "PARTIAL"
    else:
        batch_status = "BLANK"
    return {
        "row_count": len(rows),
        "decided_rows": decided,
        "blank_rows": blank,
        "error_rows": errors,
        "batch_status": batch_status,
        "error_examples": "; ".join(error_examples),
    }


def main() -> None:
    artifacts = artifact_root()
    manifest = manifest_path(artifacts)
    result_json = artifacts / "scbs_mapping_decision_batch_validate_result_v1.json"
    summary_csv = artifacts / "scbs_mapping_decision_batch_validate_summary_v1.csv"

    manifest_rows = read_csv(manifest)
    summary_rows: list[dict[str, object]] = []
    for manifest_row in manifest_rows:
        workbook = resolve_workbook_path(manifest_row["file"], manifest, artifacts)
        if not workbook.exists():
            summary_rows.append(
                {
                    "suggested_action": manifest_row.get("suggested_action", ""),
                    "file": str(workbook),
                    "batch_status": "HAS_ERRORS",
                    "row_count": 0,
                    "decided_rows": 0,
                    "blank_rows": 0,
                    "error_rows": 1,
                    "manifest_mapping_rows": manifest_row.get("mapping_rows", ""),
                    "fact_rows": manifest_row.get("fact_rows", ""),
                    "fact_amount": manifest_row.get("fact_amount", ""),
                    "error_examples": "workbook_file_not_found",
                }
            )
            continue
        validation = validate_workbook(workbook)
        summary_rows.append(
            {
                "suggested_action": manifest_row.get("suggested_action", ""),
                "file": str(workbook),
                "batch_status": validation["batch_status"],
                "row_count": validation["row_count"],
                "decided_rows": validation["decided_rows"],
                "blank_rows": validation["blank_rows"],
                "error_rows": validation["error_rows"],
                "manifest_mapping_rows": manifest_row.get("mapping_rows", ""),
                "fact_rows": manifest_row.get("fact_rows", ""),
                "fact_amount": manifest_row.get("fact_amount", ""),
                "error_examples": validation["error_examples"],
            }
        )

    write_csv(
        summary_csv,
        [
            "suggested_action",
            "file",
            "batch_status",
            "row_count",
            "decided_rows",
            "blank_rows",
            "error_rows",
            "manifest_mapping_rows",
            "fact_rows",
            "fact_amount",
            "error_examples",
        ],
        summary_rows,
    )
    status_counts: dict[str, int] = {}
    for row in summary_rows:
        status = str(row["batch_status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    payload = {
        "status": "PASS" if not status_counts.get("HAS_ERRORS") else "HAS_ERRORS",
        "database": env.cr.dbname,  # noqa: F821
        "manifest_csv": str(manifest),
        "summary_csv": str(summary_csv),
        "batch_count": len(summary_rows),
        "status_counts": status_counts,
    }
    write_json(result_json, payload)
    print("SCBS_MAPPING_DECISION_BATCH_VALIDATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
