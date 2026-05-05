"""Export SCBS business-entity mapping consolidation candidates."""

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


def fact_stats_by_entity_map() -> dict[int, dict[str, object]]:
    Staging = env["sc.legacy.scbs.fact.staging"].sudo().with_context(active_test=False)  # noqa: F821
    groups = Staging.read_group(
        [("business_entity_map_id", "!=", False), ("import_batch", "=", "scbs_fact_staging_v1")],
        ["business_entity_map_id", "amount_total:sum", "__count"],
        ["business_entity_map_id"],
        lazy=False,
    )
    stats: dict[int, dict[str, object]] = {}
    for row in groups:
        value = row.get("business_entity_map_id")
        if not value:
            continue
        stats[value[0]] = {
            "fact_rows": row.get("__count", 0),
            "fact_amount": round(float(row.get("amount_total", 0.0) or 0.0), 2),
        }
    return stats


def suggested_action(mapping, same_name_count: int) -> str:
    name = mapping.legacy_xmmc or ""
    if "测试" in name:
        return "ignore_or_conflict_test_value"
    if name == "公司综合平台":
        return "confirm_or_ignore_platform_entity"
    if same_name_count > 1:
        return "review_same_name_legacy_ids"
    return "confirm_or_ignore_business_entity"


def main() -> None:
    artifacts = artifact_root()
    detail_csv = artifacts / "scbs_business_entity_consolidation_detail_v1.csv"
    summary_csv = artifacts / "scbs_business_entity_consolidation_summary_v1.csv"
    result_json = artifacts / "scbs_business_entity_consolidation_report_result_v1.json"
    Mapping = env["sc.legacy.business.entity.map"].sudo().with_context(active_test=False)  # noqa: F821
    fact_stats = fact_stats_by_entity_map()
    mappings = Mapping.search(
        [
            ("id", "in", list(fact_stats)),
            ("source_domain", "=", "SCBS"),
            ("mapping_state", "!=", "confirmed"),
        ]
    )
    by_name: dict[str, list] = {}
    for mapping in mappings:
        by_name.setdefault(mapping.legacy_xmmc or "", []).append(mapping)

    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for name, group in by_name.items():
        same_name_count = len(group)
        target_entity_ids = sorted({rec.business_entity_id.id for rec in group if rec.business_entity_id})
        group_fact_rows = sum(int(fact_stats.get(rec.id, {}).get("fact_rows", 0) or 0) for rec in group)
        group_fact_amount = round(sum(float(fact_stats.get(rec.id, {}).get("fact_amount", 0.0) or 0.0) for rec in group), 2)
        action = suggested_action(group[0], same_name_count)
        summary_rows.append(
            {
                "legacy_name": name,
                "suggested_action": action,
                "mapping_rows": same_name_count,
                "target_entity_ids": ",".join(str(item) for item in target_entity_ids),
                "target_entity_count": len(target_entity_ids),
                "fact_rows": group_fact_rows,
                "fact_amount": group_fact_amount,
            }
        )
        for rec in group:
            fact_stat = fact_stats.get(rec.id, {})
            detail_rows.append(
                {
                    "legacy_name": name,
                    "map_id": rec.id,
                    "source_table": rec.source_table,
                    "legacy_xmid": rec.legacy_xmid,
                    "mapping_state": rec.mapping_state,
                    "suggested_entity_type": rec.suggested_entity_type,
                    "business_entity_id": rec.business_entity_id.id or "",
                    "business_entity_name": rec.business_entity_id.display_name if rec.business_entity_id else "",
                    "partner_id": rec.partner_id.id or "",
                    "partner_name": rec.partner_id.display_name if rec.partner_id else "",
                    "fact_rows": fact_stat.get("fact_rows", rec.rows_total or 0),
                    "fact_amount": fact_stat.get("fact_amount", round(rec.amount_total or 0.0, 2)),
                    "group_mapping_rows": same_name_count,
                    "group_target_entity_count": len(target_entity_ids),
                    "suggested_action": action,
                    "decision": "",
                    "decision_target_id": "",
                    "decision_note": "",
                }
            )

    detail_rows.sort(key=lambda row: (-float(row["fact_amount"] or 0.0), str(row["legacy_name"]), str(row["legacy_xmid"])))
    summary_rows.sort(key=lambda row: (-float(row["fact_amount"] or 0.0), str(row["legacy_name"])))
    write_csv(
        detail_csv,
        [
            "legacy_name",
            "map_id",
            "source_table",
            "legacy_xmid",
            "mapping_state",
            "suggested_entity_type",
            "business_entity_id",
            "business_entity_name",
            "partner_id",
            "partner_name",
            "fact_rows",
            "fact_amount",
            "group_mapping_rows",
            "group_target_entity_count",
            "suggested_action",
            "decision",
            "decision_target_id",
            "decision_note",
        ],
        detail_rows,
    )
    write_csv(
        summary_csv,
        ["legacy_name", "suggested_action", "mapping_rows", "target_entity_ids", "target_entity_count", "fact_rows", "fact_amount"],
        summary_rows,
    )
    action_summary: dict[str, dict[str, int | float]] = {}
    for row in summary_rows:
        action = str(row["suggested_action"])
        bucket = action_summary.setdefault(action, {"legacy_names": 0, "mapping_rows": 0, "fact_rows": 0, "fact_amount": 0.0})
        bucket["legacy_names"] = int(bucket["legacy_names"]) + 1
        bucket["mapping_rows"] = int(bucket["mapping_rows"]) + int(row["mapping_rows"])
        bucket["fact_rows"] = int(bucket["fact_rows"]) + int(row["fact_rows"])
        bucket["fact_amount"] = round(float(bucket["fact_amount"]) + float(row["fact_amount"]), 2)
    payload = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "detail_csv": str(detail_csv),
        "summary_csv": str(summary_csv),
        "mapping_rows": len(detail_rows),
        "legacy_names": len(summary_rows),
        "action_summary": action_summary,
    }
    write_json(result_json, payload)
    print("SCBS_BUSINESS_ENTITY_CONSOLIDATION_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
