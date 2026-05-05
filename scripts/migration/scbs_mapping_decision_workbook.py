"""Export SCBS mapping rows that need business decisions."""

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


def fact_stats_by_dimension() -> dict[tuple[str, int], dict[str, object]]:
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    specs = [
        ("business_entity", "business_entity_map_id"),
        ("project", "project_map_id"),
        ("partner", "partner_map_id"),
    ]
    stats: dict[tuple[str, int], dict[str, object]] = {}
    for dimension, group_field in specs:
        groups = Staging.read_group(
            [(group_field, "!=", False), ("import_batch", "=", "scbs_fact_staging_v1"), ("active", "=", True)],
            [group_field, "amount_total:sum", "__count"],
            [group_field],
            lazy=False,
        )
        for row in groups:
            value = row.get(group_field)
            if not value:
                continue
            stats[(dimension, value[0])] = {
                "fact_rows": row.get("__count", 0),
                "fact_amount": round(float(row.get("amount_total", 0.0) or 0.0), 2),
            }
    return stats


def target_name(record, field_name: str) -> str:
    target = record[field_name]
    return target.display_name if target else ""


def looks_like_non_counterparty_label(name: str) -> bool:
    normalized = (name or "").strip()
    if not normalized:
        return False
    keywords = ["工资", "库房", "食堂", "备用金", "押金", "保证金", "代付", "暂估", "内部"]
    return any(keyword in normalized for keyword in keywords)


def suggested_action(dimension: str, mapping_state: str, suggested_state: str, match_method: str, legacy_name: str) -> str:
    if mapping_state == "confirmed":
        return "noop"
    if "测试" in (legacy_name or ""):
        return "ignore_or_conflict_test_value"
    if dimension == "partner" and looks_like_non_counterparty_label(legacy_name):
        return "review_non_counterparty_label"
    if dimension == "partner" and suggested_state == "tax_code_conflict":
        return "manual_partner_required"
    if dimension == "partner" and match_method == "multiple":
        return "choose_target_partner"
    if dimension == "project" and suggested_state in {"not_real_project_review", "ignored_test_candidate"}:
        return "ignore_if_not_real_project"
    if dimension == "business_entity":
        return "confirm_or_ignore_business_entity"
    if dimension == "project":
        return "confirm_or_ignore_project"
    return "confirm_or_ignore_partner"


def workbook_rows() -> list[dict[str, object]]:
    stats = fact_stats_by_dimension()
    rows: list[dict[str, object]] = []

    EntityMap = env["sc.legacy.business.entity.map"].sudo().with_context(active_test=False)  # noqa: F821
    for rec in EntityMap.search([("source_domain", "=", "SCBS"), ("mapping_state", "!=", "confirmed")]):
        fact_stat = stats.get(("business_entity", rec.id), {})
        if not fact_stat:
            continue
        rows.append(
            {
                "dimension": "business_entity",
                "map_model": rec._name,
                "map_id": rec.id,
                "source_table": rec.source_table,
                "legacy_key": rec.legacy_xmid,
                "legacy_name": rec.legacy_xmmc,
                "mapping_state": rec.mapping_state,
                "suggested_state": rec.suggested_entity_type,
                "match_method": "",
                "target_id": rec.business_entity_id.id or "",
                "target_name": target_name(rec, "business_entity_id"),
                "fact_rows": fact_stat.get("fact_rows", rec.rows_total or 0),
                "fact_amount": fact_stat.get("fact_amount", round(rec.amount_total or 0.0, 2)),
                "suggested_action": suggested_action("business_entity", rec.mapping_state, rec.suggested_entity_type, "", rec.legacy_xmmc),
                "decision": "",
                "decision_target_id": "",
                "decision_note": "",
            }
        )

    ProjectMap = env["sc.legacy.project.map"].sudo().with_context(active_test=False)  # noqa: F821
    for rec in ProjectMap.search([("source_domain", "=", "SCBS"), ("mapping_state", "!=", "confirmed")]):
        fact_stat = stats.get(("project", rec.id), {})
        if not fact_stat:
            continue
        rows.append(
            {
                "dimension": "project",
                "map_model": rec._name,
                "map_id": rec.id,
                "source_table": rec.source_table,
                "legacy_key": rec.legacy_gcmc,
                "legacy_name": rec.legacy_gcmc,
                "mapping_state": rec.mapping_state,
                "suggested_state": rec.suggested_state,
                "match_method": rec.match_method,
                "target_id": rec.project_id.id or "",
                "target_name": target_name(rec, "project_id"),
                "fact_rows": fact_stat.get("fact_rows", rec.rows_total or 0),
                "fact_amount": fact_stat.get("fact_amount", round(rec.amount_total or 0.0, 2)),
                "suggested_action": suggested_action("project", rec.mapping_state, rec.suggested_state, rec.match_method, rec.legacy_gcmc),
                "decision": "",
                "decision_target_id": "",
                "decision_note": "",
            }
        )

    PartnerMap = env["sc.legacy.partner.map"].sudo().with_context(active_test=False)  # noqa: F821
    for rec in PartnerMap.search([("source_domain", "=", "SCBS"), ("mapping_state", "!=", "confirmed")]):
        fact_stat = stats.get(("partner", rec.id), {})
        if not fact_stat:
            continue
        rows.append(
            {
                "dimension": "partner",
                "map_model": rec._name,
                "map_id": rec.id,
                "source_table": rec.source_table,
                "legacy_key": rec.legacy_key,
                "legacy_name": rec.legacy_partner_name,
                "mapping_state": rec.mapping_state,
                "suggested_state": rec.suggested_state,
                "match_method": rec.match_method,
                "target_id": rec.partner_id.id or "",
                "target_name": target_name(rec, "partner_id"),
                "fact_rows": fact_stat.get("fact_rows", rec.active_rows or rec.legacy_rows or 0),
                "fact_amount": fact_stat.get("fact_amount", 0.0),
                "suggested_action": suggested_action("partner", rec.mapping_state, rec.suggested_state, rec.match_method, rec.legacy_partner_name),
                "decision": "",
                "decision_target_id": "",
                "decision_note": "",
            }
        )

    rows.sort(key=lambda row: (-float(row["fact_amount"] or 0.0), row["dimension"], str(row["legacy_name"])))
    return rows


def summarize(rows: list[dict[str, object]], keys: list[str]) -> list[dict[str, object]]:
    summary: dict[tuple[str, ...], dict[str, object]] = {}
    for row in rows:
        bucket_key = tuple(str(row.get(key, "")) for key in keys)
        bucket = summary.setdefault(
            bucket_key,
            {**{key: row.get(key, "") for key in keys}, "mapping_rows": 0, "fact_rows": 0, "fact_amount": 0.0, "with_target": 0},
        )
        bucket["mapping_rows"] = int(bucket["mapping_rows"]) + 1
        bucket["fact_rows"] = int(bucket["fact_rows"]) + int(row.get("fact_rows") or 0)
        bucket["fact_amount"] = round(float(bucket["fact_amount"]) + float(row.get("fact_amount") or 0.0), 2)
        if row.get("target_id"):
            bucket["with_target"] = int(bucket["with_target"]) + 1
    return sorted(
        summary.values(),
        key=lambda item: (-float(item["fact_amount"] or 0.0), str(item.get("dimension", "")), str(item.get("suggested_action", ""))),
    )


def priority_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    priority_order = {
        "manual_partner_required": 1,
        "review_non_counterparty_label": 2,
        "choose_target_partner": 3,
        "ignore_or_conflict_test_value": 4,
        "ignore_if_not_real_project": 5,
        "confirm_or_ignore_business_entity": 6,
        "confirm_or_ignore_project": 7,
        "confirm_or_ignore_partner": 8,
    }
    enriched: list[dict[str, object]] = []
    for row in rows:
        action = str(row.get("suggested_action", ""))
        priority = priority_order.get(action, 99)
        enriched.append({**row, "review_priority": priority})
    enriched.sort(key=lambda row: (int(row["review_priority"]), -float(row.get("fact_amount") or 0.0), str(row.get("legacy_name", ""))))
    return enriched


def main() -> None:
    artifacts = artifact_root()
    workbook_csv = artifacts / "scbs_mapping_decision_workbook_v1.csv"
    action_summary_csv = artifacts / "scbs_mapping_decision_action_summary_v1.csv"
    priority_csv = artifacts / "scbs_mapping_decision_priority_top_v1.csv"
    result_json = artifacts / "scbs_mapping_decision_workbook_result_v1.json"
    rows = workbook_rows()
    fieldnames = [
        "dimension",
        "map_model",
        "map_id",
        "source_table",
        "legacy_key",
        "legacy_name",
        "mapping_state",
        "suggested_state",
        "match_method",
        "target_id",
        "target_name",
        "fact_rows",
        "fact_amount",
        "suggested_action",
        "decision",
        "decision_target_id",
        "decision_note",
    ]
    write_csv(workbook_csv, fieldnames, rows)
    action_summary = summarize(rows, ["dimension", "suggested_action"])
    write_csv(
        action_summary_csv,
        ["dimension", "suggested_action", "mapping_rows", "fact_rows", "fact_amount", "with_target"],
        action_summary,
    )
    priority = priority_rows(rows)
    write_csv(priority_csv, ["review_priority", *fieldnames], priority[:200])
    summary: dict[str, dict[str, float]] = {}
    for row in rows:
        bucket = summary.setdefault(str(row["dimension"]), {"rows": 0, "fact_rows": 0, "fact_amount": 0.0})
        bucket["rows"] += 1
        bucket["fact_rows"] += int(row["fact_rows"] or 0)
        bucket["fact_amount"] = round(bucket["fact_amount"] + float(row["fact_amount"] or 0.0), 2)
    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "workbook_csv": str(workbook_csv),
        "action_summary_csv": str(action_summary_csv),
        "priority_csv": str(priority_csv),
        "review_rows": len(rows),
        "summary": summary,
        "action_summary": action_summary,
    }
    write_json(result_json, payload)
    print("SCBS_MAPPING_DECISION_WORKBOOK=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
