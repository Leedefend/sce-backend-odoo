#!/usr/bin/env python3
"""Screen residual legacy business facts against specialized fact carriers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/business_fact_residual_screen/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/business_fact_residual_screen/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    summary = payload["summary"]
    lines = [
        "# Business Fact Residual Assetization Screen v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Summary",
        "",
        f"- residual rows: `{summary['residual_rows']}`",
        f"- residual tables: `{summary['residual_table_count']}`",
        f"- specialized source tables: `{summary['specialized_source_table_count']}`",
        f"- rows exactly matched by specialized source table: `{summary['exact_specialized_source_table_rows']}`",
        f"- rows related to specialized source table: `{summary['related_specialized_source_table_rows']}`",
        f"- rows still residual-only by source table family: `{summary['residual_only_source_table_rows']}`",
        f"- next assetization candidate rows: `{summary['next_assetization_candidate_rows']}`",
        f"- next assetization candidate tables: `{summary['next_assetization_candidate_tables']}`",
        "",
        "## Top Residual-Only Candidates",
        "",
        "| source | family | table | rows | project | partner | amount rows | amount abs sum | band |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["top_residual_only_candidates"]:
        lines.append(
            "| {source_database} | {family} | {source_table} | {rows} | {project_rows} | {partner_rows} | "
            "{amount_rows} | {amount_abs_sum:.2f} | {assetization_band} |".format(**row)
        )
    lines.extend(["", "## Candidate Field Samples", ""])
    for row in payload["candidate_samples"]:
        lines.append(f"### {row['source_database']} / {row['source_table']}")
        lines.append("")
        lines.append(f"- field keys: `{', '.join(row['payload_keys'][:30])}`")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(row["samples"], ensure_ascii=False, indent=2, sort_keys=True))
        lines.append("```")
        lines.append("")
    lines.extend(
        [
            "",
            "## Specialized Carrier Tables",
            "",
            "```json",
            json.dumps(payload["specialized_source_tables"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            f"`{payload['decision']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def fetch_specialized_source_tables() -> dict[str, list[str]]:
    source_tables: dict[str, set[str]] = {}
    for model_name in sorted(env.registry.models):  # noqa: F821
        if not model_name.startswith("sc.legacy.") or model_name == "sc.legacy.business.fact.residual":
            continue
        model = env[model_name].sudo()  # noqa: F821
        if "source_table" not in model._fields:
            continue
        env.cr.execute(  # noqa: F821
            f"""
            SELECT source_table, COUNT(*)
            FROM {model._table}
            WHERE source_table IS NOT NULL AND source_table <> ''
            GROUP BY source_table
            """
        )
        for source_table, count in env.cr.fetchall():  # noqa: F821
            if count:
                source_tables.setdefault(str(source_table), set()).add(model_name)
    return {key: sorted(value) for key, value in sorted(source_tables.items())}


DETAIL_SUFFIXES = (
    "_CB",
    "_ZB",
    "_JX",
    "_LW",
    "_FB",
    "_ZL",
    "_QD",
    "_MX",
    "_DETAIL",
    "_TASK",
)


def normalize_source_table(value: object) -> str:
    table = str(value or "").strip()
    for suffix in (".parent_derived", ".department_derived", "_derived"):
        if table.lower().endswith(suffix.lower()):
            table = table[: -len(suffix)]
    changed = True
    while changed:
        changed = False
        for suffix in DETAIL_SUFFIXES:
            if table.upper().endswith(suffix):
                table = table[: -len(suffix)]
                changed = True
                break
    return table.upper()


def band_for(
    row: dict[str, object],
    specialized_tables: dict[str, list[str]],
    normalized_specialized_tables: dict[str, list[str]],
) -> str:
    if row["source_table"] in specialized_tables:
        return "exact_specialized_source_table"
    if normalize_source_table(row["source_table"]) in normalized_specialized_tables:
        return "related_specialized_source_table"
    if not row["active_rows"]:
        return "inactive_reference_only"
    if row["amount_rows"] and (row["project_rows"] or row["partner_rows"]):
        return "next_assetization_candidate"
    if row["project_rows"] or row["partner_rows"] or row["document_no_rows"]:
        return "context_candidate"
    return "raw_context_only"


def payload_sample(raw_payload: object) -> dict[str, Any]:
    try:
        payload = json.loads(str(raw_payload or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {key: payload.get(key) for key in sorted(payload)[:40]}


def fetch_candidate_samples(candidates: list[dict[str, object]], limit: int = 12) -> list[dict[str, object]]:
    result = []
    for candidate in candidates[:limit]:
        env.cr.execute(  # noqa: F821
            """
            SELECT legacy_record_id, document_no, document_date, project_legacy_id, project_name,
                   partner_legacy_id, partner_name, amount_total, raw_payload
            FROM sc_legacy_business_fact_residual
            WHERE source_database = %s AND source_table = %s
            ORDER BY active DESC, ABS(COALESCE(amount_total, 0)) DESC, legacy_record_id
            LIMIT 3
            """,
            [candidate["source_database"], candidate["source_table"]],
        )
        samples = []
        payload_keys: set[str] = set()
        for row in env.cr.dictfetchall():  # noqa: F821
            sample_payload = payload_sample(row["raw_payload"])
            payload_keys.update(sample_payload)
            samples.append(
                {
                    "legacy_record_id": row["legacy_record_id"],
                    "document_no": row["document_no"],
                    "document_date": row["document_date"].isoformat() if row["document_date"] else None,
                    "project_legacy_id": row["project_legacy_id"],
                    "project_name": row["project_name"],
                    "partner_legacy_id": row["partner_legacy_id"],
                    "partner_name": row["partner_name"],
                    "amount_total": float(row["amount_total"] or 0),
                    "payload_sample": sample_payload,
                }
            )
        result.append(
            {
                "source_database": candidate["source_database"],
                "family": candidate["family"],
                "source_table": candidate["source_table"],
                "assetization_band": candidate["assetization_band"],
                "payload_keys": sorted(payload_keys),
                "samples": samples,
            }
        )
    return result


artifact_root = resolve_artifact_root()
output_json = artifact_root / "business_fact_residual_assetization_screen_v1.json"
output_report = artifact_root / "business_fact_residual_assetization_screen_v1.md"

specialized_source_tables = fetch_specialized_source_tables()
normalized_specialized_source_tables: dict[str, list[str]] = {}
for source_table, model_names in specialized_source_tables.items():
    normalized = normalize_source_table(source_table)
    normalized_specialized_source_tables.setdefault(normalized, [])
    normalized_specialized_source_tables[normalized].extend(model_names)
normalized_specialized_source_tables = {
    key: sorted(set(value)) for key, value in sorted(normalized_specialized_source_tables.items())
}
env.cr.execute(  # noqa: F821
    """
    SELECT
      source_database,
      family,
      source_table,
      COUNT(*) AS rows,
      SUM(CASE WHEN active THEN 1 ELSE 0 END) AS active_rows,
      SUM(CASE WHEN COALESCE(document_no, '') <> '' THEN 1 ELSE 0 END) AS document_no_rows,
      SUM(CASE WHEN COALESCE(project_legacy_id, '') <> '' OR COALESCE(project_name, '') <> '' THEN 1 ELSE 0 END)
        AS project_rows,
      SUM(CASE WHEN COALESCE(partner_legacy_id, '') <> '' OR COALESCE(partner_name, '') <> '' THEN 1 ELSE 0 END)
        AS partner_rows,
      SUM(CASE WHEN COALESCE(amount_total, 0) <> 0 THEN 1 ELSE 0 END) AS amount_rows,
      COALESCE(SUM(ABS(amount_total)), 0) AS amount_abs_sum,
      MAX(business_signal_score) AS max_business_signal_score
    FROM sc_legacy_business_fact_residual
    GROUP BY source_database, family, source_table
    ORDER BY COUNT(*) DESC, source_database, source_table
    """
)
table_rows = []
for row in env.cr.dictfetchall():  # noqa: F821
    item = {
        "source_database": row["source_database"],
        "family": row["family"] or "",
        "source_table": row["source_table"],
        "rows": int(row["rows"] or 0),
        "active_rows": int(row["active_rows"] or 0),
        "document_no_rows": int(row["document_no_rows"] or 0),
        "project_rows": int(row["project_rows"] or 0),
        "partner_rows": int(row["partner_rows"] or 0),
        "amount_rows": int(row["amount_rows"] or 0),
        "amount_abs_sum": float(row["amount_abs_sum"] or 0),
        "max_business_signal_score": int(row["max_business_signal_score"] or 0),
    }
    item["specialized_models"] = specialized_source_tables.get(item["source_table"], [])
    item["normalized_source_table"] = normalize_source_table(item["source_table"])
    item["related_specialized_models"] = normalized_specialized_source_tables.get(item["normalized_source_table"], [])
    item["assetization_band"] = band_for(item, specialized_source_tables, normalized_specialized_source_tables)
    table_rows.append(item)

band_counts: dict[str, int] = {}
band_row_counts: dict[str, int] = {}
family_counts: dict[str, dict[str, int]] = {}
for row in table_rows:
    band = row["assetization_band"]
    family = row["family"]
    band_counts[band] = band_counts.get(band, 0) + 1
    band_row_counts[band] = band_row_counts.get(band, 0) + row["rows"]
    family_counts.setdefault(family, {"tables": 0, "rows": 0, "next_assetization_candidate_rows": 0})
    family_counts[family]["tables"] += 1
    family_counts[family]["rows"] += row["rows"]
    if band == "next_assetization_candidate":
        family_counts[family]["next_assetization_candidate_rows"] += row["rows"]

top_residual_only_candidates = sorted(
    [
        row
        for row in table_rows
        if row["assetization_band"] not in {"exact_specialized_source_table", "related_specialized_source_table"}
    ],
    key=lambda row: (
        row["assetization_band"] != "next_assetization_candidate",
        -row["rows"],
        -row["amount_abs_sum"],
        row["source_database"],
        row["source_table"],
    ),
)[:50]
candidate_samples = fetch_candidate_samples(top_residual_only_candidates)

payload = {
    "status": "PASS",
    "mode": "business_fact_residual_assetization_screen",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "summary": {
        "residual_rows": sum(row["rows"] for row in table_rows),
        "residual_table_count": len(table_rows),
        "specialized_source_table_count": len(specialized_source_tables),
        "normalized_specialized_source_table_count": len(normalized_specialized_source_tables),
        "exact_specialized_source_table_rows": band_row_counts.get("exact_specialized_source_table", 0),
        "related_specialized_source_table_rows": band_row_counts.get("related_specialized_source_table", 0),
        "specialized_source_table_matched_rows": band_row_counts.get("exact_specialized_source_table", 0)
        + band_row_counts.get("related_specialized_source_table", 0),
        "residual_only_source_table_rows": sum(row["rows"] for row in table_rows)
        - band_row_counts.get("exact_specialized_source_table", 0)
        - band_row_counts.get("related_specialized_source_table", 0),
        "next_assetization_candidate_rows": band_row_counts.get("next_assetization_candidate", 0),
        "next_assetization_candidate_tables": band_counts.get("next_assetization_candidate", 0),
        "band_counts": band_counts,
        "band_row_counts": band_row_counts,
    },
    "family_counts": dict(sorted(family_counts.items(), key=lambda item: (-item[1]["rows"], item[0]))),
    "specialized_source_tables": specialized_source_tables,
    "normalized_specialized_source_tables": normalized_specialized_source_tables,
    "top_residual_only_candidates": top_residual_only_candidates,
    "candidate_samples": candidate_samples,
    "decision": "business_fact_residual_assetization_screen_ready",
}
write_json(output_json, payload)
write_report(output_report, payload)
print(
    "BUSINESS_FACT_RESIDUAL_ASSETIZATION_SCREEN="
    + json.dumps(
        {
            "status": payload["status"],
            "residual_rows": payload["summary"]["residual_rows"],
            "residual_table_count": payload["summary"]["residual_table_count"],
            "exact_specialized_source_table_rows": payload["summary"]["exact_specialized_source_table_rows"],
            "related_specialized_source_table_rows": payload["summary"]["related_specialized_source_table_rows"],
            "specialized_source_table_matched_rows": payload["summary"]["specialized_source_table_matched_rows"],
            "residual_only_source_table_rows": payload["summary"]["residual_only_source_table_rows"],
            "next_assetization_candidate_rows": payload["summary"]["next_assetization_candidate_rows"],
            "next_assetization_candidate_tables": payload["summary"]["next_assetization_candidate_tables"],
            "artifact_root": str(artifact_root),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
