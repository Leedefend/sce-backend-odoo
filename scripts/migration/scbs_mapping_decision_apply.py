"""Apply approved SCBS mapping decisions from the decision workbook.

The script is dry-run by default. It never creates target companies, projects,
partners, or business entities; confirmation requires an existing target ID.
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


def input_csv_path(artifacts: Path) -> Path:
    raw = os.getenv("SCBS_MAPPING_DECISION_CSV")
    if raw:
        return Path(raw)
    return artifacts / "scbs_mapping_decision_workbook_v1.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
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


def validate_target(target_model: str, target_id: str):
    if not target_id:
        return None
    target = env[target_model].sudo().with_context(active_test=False).browse(int(target_id))  # noqa: F821
    return target if target.exists() else None


def apply_row(row: dict[str, str], dry_run: bool) -> dict[str, object]:
    decision = (row.get("decision") or "").strip().lower()
    if decision not in VALID_DECISIONS:
        return {"status": "error", "reason": f"invalid_decision:{decision}"}
    if decision in {"", "noop"}:
        return {"status": "skipped", "reason": "noop"}

    dimension = (row.get("dimension") or "").strip()
    try:
        rec = find_mapping(row)
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}
    if not rec:
        return {"status": "error", "reason": "mapping_not_found"}

    _, target_field, target_model = model_for_dimension(dimension)
    note = (row.get("decision_note") or "").strip()

    if decision == "confirm":
        target_id = (row.get("decision_target_id") or row.get("target_id") or "").strip()
        target = validate_target(target_model, target_id)
        if not target:
            return {"status": "error", "reason": "confirm_requires_existing_target"}
        if dry_run:
            return {"status": "would_confirm", "target_id": target.id, "target_name": target.display_name}
        values = {target_field: target.id}
        if "match_method" in rec._fields:
            values["match_method"] = "manual"
        if note:
            values["note"] = ((rec.note or "") + "\n" + note).strip()
        rec.write(values)
        rec.action_confirm()
        return {"status": "confirmed", "target_id": target.id, "target_name": target.display_name}

    if dry_run:
        return {"status": f"would_{decision}"}
    if note:
        rec.write({"note": ((rec.note or "") + "\n" + note).strip()})
    if decision == "ignore":
        rec.action_ignore()
        return {"status": "ignored"}
    rec.action_mark_conflict()
    return {"status": "conflict"}


def main() -> None:
    artifacts = artifact_root()
    source_csv = input_csv_path(artifacts)
    mode = os.getenv("SCBS_MAPPING_DECISION_APPLY_MODE", "dry-run")
    dry_run = mode != "write"
    result_json = artifacts / "scbs_mapping_decision_apply_result_v1.json"
    preview_csv = artifacts / "scbs_mapping_decision_apply_preview_v1.csv"

    rows = read_rows(source_csv)
    result_rows: list[dict[str, object]] = []
    counts: dict[str, int] = {}
    for index, row in enumerate(rows, start=2):
        result = apply_row(row, dry_run=dry_run)
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
        result_rows.append(
            {
                "line": index,
                "dimension": row.get("dimension", ""),
                "map_id": row.get("map_id", ""),
                "legacy_key": row.get("legacy_key", ""),
                "legacy_name": row.get("legacy_name", ""),
                "decision": row.get("decision", ""),
                "status": status,
                "reason": result.get("reason", ""),
                "target_id": result.get("target_id", ""),
                "target_name": result.get("target_name", ""),
            }
        )

    write_csv(
        preview_csv,
        ["line", "dimension", "map_id", "legacy_key", "legacy_name", "decision", "status", "reason", "target_id", "target_name"],
        result_rows,
    )
    payload = {
        "status": "PASS" if not any(row["status"] == "error" for row in result_rows) else "HAS_ERRORS",
        "database": env.cr.dbname,  # noqa: F821
        "mode": mode,
        "dry_run": dry_run,
        "source_csv": str(source_csv),
        "preview_csv": str(preview_csv),
        "counts": counts,
    }
    write_json(result_json, payload)
    print("SCBS_MAPPING_DECISION_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
