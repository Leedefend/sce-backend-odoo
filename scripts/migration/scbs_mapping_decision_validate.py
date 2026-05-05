"""Validate SCBS mapping decisions and simulate fact projection gates."""

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


def target_exists(target_model: str, target_id: str):
    if not target_id:
        return None
    target = env[target_model].sudo().with_context(active_test=False).browse(int(target_id))  # noqa: F821
    return target if target.exists() else None


def validate_decision(row: dict[str, str]) -> tuple[dict[str, object], tuple[str, int] | None, str | None]:
    line = int(row["_line"])
    dimension = (row.get("dimension") or "").strip()
    decision = (row.get("decision") or "").strip().lower()
    result = {
        "line": line,
        "dimension": dimension,
        "map_id": row.get("map_id", ""),
        "legacy_name": row.get("legacy_name", ""),
        "suggested_action": row.get("suggested_action", ""),
        "decision": decision,
        "status": "valid",
        "reason": "",
    }
    if decision not in VALID_DECISIONS:
        result.update({"status": "error", "reason": f"invalid_decision:{decision}"})
        return result, None, None
    try:
        rec = find_mapping(row)
    except Exception as exc:
        result.update({"status": "error", "reason": str(exc)})
        return result, None, None
    if not rec:
        result.update({"status": "error", "reason": "mapping_not_found"})
        return result, None, None

    _, target_field, target_model = model_for_dimension(dimension)
    if decision in {"", "noop"}:
        result.update({"status": "blank", "reason": "no_decision"})
        return result, (dimension, rec.id), None
    if decision == "confirm":
        target_id = (row.get("decision_target_id") or row.get("target_id") or "").strip()
        target = target_exists(target_model, target_id)
        if not target:
            result.update({"status": "error", "reason": "confirm_requires_existing_target"})
            return result, (dimension, rec.id), None
        if target_field == "partner_id":
            partner_company = target.company_id
            if partner_company and partner_company != rec.company_id:
                result.update({"status": "error", "reason": "target_partner_wrong_company"})
                return result, (dimension, rec.id), None
            if rec.suggested_state == "tax_code_conflict" and not row.get("decision_target_id", "").strip():
                result.update({"status": "error", "reason": "tax_conflict_requires_explicit_decision_target_id"})
                return result, (dimension, rec.id), None
        if target_field == "project_id":
            project_company = target.company_id
            if project_company and project_company != rec.company_id:
                result.update({"status": "error", "reason": "target_project_wrong_company"})
                return result, (dimension, rec.id), None
        if target_field == "business_entity_id" and target.company_id != rec.company_id:
            result.update({"status": "error", "reason": "target_business_entity_wrong_company"})
            return result, (dimension, rec.id), None
        result["target_id"] = target.id
        result["target_name"] = target.display_name
        return result, (dimension, rec.id), "confirmed"
    return result, (dimension, rec.id), decision


def current_state_for_dimension(dimension: str, map_id: int) -> str:
    Model, _, _ = model_for_dimension(dimension)
    rec = Model.browse(map_id)
    return rec.mapping_state if rec.exists() else "missing"


def simulated_state(dimension: str, map_id: int, decisions: dict[tuple[str, int], str]) -> str:
    return decisions.get((dimension, map_id)) or current_state_for_dimension(dimension, map_id)


def simulate_gate(decisions: dict[tuple[str, int], str]) -> tuple[dict[str, dict[str, float]], list[dict[str, object]]]:
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    rows = Staging.search([("import_batch", "=", "scbs_fact_staging_v1"), ("active", "=", True)])
    summary: dict[str, dict[str, float]] = {}
    examples: list[dict[str, object]] = []
    for rec in rows:
        states: list[str] = []
        dimension_states = {"business_entity": "", "project": "", "partner": ""}
        missing_required = False
        for dimension, legacy_value, map_record in [
            ("business_entity", rec.legacy_xmid, rec.business_entity_map_id),
            ("project", rec.legacy_gcmc, rec.project_map_id),
            ("partner", rec.legacy_partner_name, rec.partner_map_id),
        ]:
            if not legacy_value:
                continue
            if not map_record:
                missing_required = True
                dimension_states[dimension] = "missing"
                continue
            state = simulated_state(dimension, map_record.id, decisions)
            dimension_states[dimension] = state
            states.append(state)
        if "conflict" in states:
            gate = "conflict"
        elif missing_required:
            gate = "blocked"
        elif states and all(state == "confirmed" for state in states):
            gate = "projection_ready"
        else:
            gate = "staging_ready"
        bucket = summary.setdefault(gate, {"rows": 0, "amount_total": 0.0})
        bucket["rows"] += 1
        bucket["amount_total"] = round(bucket["amount_total"] + float(rec.amount_total or 0.0), 2)
        if gate != "projection_ready" and len(examples) < 100:
            examples.append(
                {
                    "source_table": rec.source_table,
                    "legacy_record_id": rec.legacy_record_id,
                    "fact_family": rec.fact_family,
                    "amount_total": rec.amount_total,
                    "simulated_gate": gate,
                    "business_entity_state": dimension_states["business_entity"],
                    "project_state": dimension_states["project"],
                    "partner_state": dimension_states["partner"],
                }
            )
    return summary, examples


def main() -> None:
    artifacts = artifact_root()
    source_csv = input_csv_path(artifacts)
    result_json = artifacts / "scbs_mapping_decision_validate_result_v1.json"
    validation_csv = artifacts / "scbs_mapping_decision_validate_rows_v1.csv"
    simulation_csv = artifacts / "scbs_mapping_decision_projection_simulation_v1.csv"
    examples_csv = artifacts / "scbs_mapping_decision_projection_blocked_examples_v1.csv"

    rows = read_rows(source_csv)
    decisions: dict[tuple[str, int], str] = {}
    validation_rows: list[dict[str, object]] = []
    counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    for index, row in enumerate(rows, start=2):
        row["_line"] = str(index)
        validation, key, simulated = validate_decision(row)
        validation_rows.append(validation)
        counts[str(validation["status"])] = counts.get(str(validation["status"]), 0) + 1
        decision_counts[str(validation["decision"] or "blank")] = decision_counts.get(str(validation["decision"] or "blank"), 0) + 1
        if key and simulated and validation["status"] == "valid":
            decisions[key] = simulated

    gate_summary, examples = simulate_gate(decisions)
    write_csv(
        validation_csv,
        ["line", "dimension", "map_id", "legacy_name", "suggested_action", "decision", "status", "reason", "target_id", "target_name"],
        validation_rows,
    )
    simulation_rows = [
        {"simulated_gate": gate, "rows": value["rows"], "amount_total": value["amount_total"]}
        for gate, value in sorted(gate_summary.items())
    ]
    write_csv(simulation_csv, ["simulated_gate", "rows", "amount_total"], simulation_rows)
    write_csv(
        examples_csv,
        [
            "source_table",
            "legacy_record_id",
            "fact_family",
            "amount_total",
            "simulated_gate",
            "business_entity_state",
            "project_state",
            "partner_state",
        ],
        examples,
    )
    payload = {
        "status": "PASS" if counts.get("error", 0) == 0 else "HAS_ERRORS",
        "database": env.cr.dbname,  # noqa: F821
        "source_csv": str(source_csv),
        "validation_csv": str(validation_csv),
        "simulation_csv": str(simulation_csv),
        "examples_csv": str(examples_csv),
        "counts": counts,
        "decision_counts": decision_counts,
        "simulated_gate_summary": gate_summary,
    }
    write_json(result_json, payload)
    print("SCBS_MAPPING_DECISION_VALIDATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
