"""Build SCBS mapping reconciliation artifacts before fact import.

Run through Odoo shell:

    odoo shell -c /var/lib/odoo/odoo.conf -d sc_prod_sim \\
      < scripts/migration/scbs_mapping_reconciliation.py

The report is read-only. It does not create or update business records. It
summarizes the current business-entity, project, and partner mapping gates that
must pass before SCBS facts can be projected into formal business models.
"""

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


def amount(value) -> float:
    return round(float(value or 0.0), 2)


def grouped(model_name: str, domain: list[tuple], groupby: list[str], fields: list[str]) -> list[dict[str, object]]:
    return env[model_name].read_group(domain, fields, groupby, lazy=False)  # noqa: F821


def key_value(value) -> str:
    if isinstance(value, tuple):
        return str(value[1])
    if value is False or value is None:
        return ""
    return str(value)


def business_entity_rows() -> list[dict[str, object]]:
    rows = []
    data = grouped(
        "sc.legacy.business.entity.map",
        [("source_table", "=", "SCBS_BUSINESS_ENTITY_CANDIDATE")],
        ["mapping_state", "suggested_entity_type"],
        ["rows_total:sum", "amount_total:sum", "business_entity_id:count"],
    )
    for item in data:
        rows.append(
            {
                "dimension": "business_entity",
                "suggested_state": key_value(item.get("suggested_entity_type")),
                "mapping_state": key_value(item.get("mapping_state")),
                "match_method": "",
                "candidate_count": item.get("__count", 0),
                "mapped_target_count": item.get("business_entity_id_count", 0),
                "fact_rows": item.get("rows_total", 0),
                "amount_signal": amount(item.get("amount_total")),
            }
        )
    return rows


def project_rows() -> list[dict[str, object]]:
    rows = []
    data = grouped(
        "sc.legacy.project.map",
        [("source_table", "=", "SCBS_GCMC_PROJECT_CANDIDATE")],
        ["suggested_state", "mapping_state", "match_method"],
        ["rows_total:sum", "amount_total:sum", "project_id:count"],
    )
    for item in data:
        rows.append(
            {
                "dimension": "project",
                "suggested_state": key_value(item.get("suggested_state")),
                "mapping_state": key_value(item.get("mapping_state")),
                "match_method": key_value(item.get("match_method")),
                "candidate_count": item.get("__count", 0),
                "mapped_target_count": item.get("project_id_count", 0),
                "fact_rows": item.get("rows_total", 0),
                "amount_signal": amount(item.get("amount_total")),
            }
        )
    return rows


def partner_rows() -> list[dict[str, object]]:
    rows = []
    data = grouped(
        "sc.legacy.partner.map",
        [("source_table", "=", "SCBS_PARTNER_DUPLICATE_CANDIDATE")],
        ["suggested_state", "mapping_state", "match_method"],
        ["legacy_rows:sum", "active_rows:sum", "partner_id:count"],
    )
    for item in data:
        rows.append(
            {
                "dimension": "partner",
                "suggested_state": key_value(item.get("suggested_state")),
                "mapping_state": key_value(item.get("mapping_state")),
                "match_method": key_value(item.get("match_method")),
                "candidate_count": item.get("__count", 0),
                "mapped_target_count": item.get("partner_id_count", 0),
                "fact_rows": item.get("active_rows", 0),
                "amount_signal": "",
                "legacy_rows": item.get("legacy_rows", 0),
            }
        )
    return rows


def unresolved_examples() -> list[dict[str, object]]:
    examples = []
    for rec in env["sc.legacy.business.entity.map"].search(  # noqa: F821
        [("source_table", "=", "SCBS_BUSINESS_ENTITY_CANDIDATE"), ("mapping_state", "!=", "confirmed")],
        order="amount_total desc",
        limit=10,
    ):
        examples.append(
            {
                "dimension": "business_entity",
                "legacy_key": rec.legacy_xmid,
                "legacy_name": rec.legacy_xmmc,
                "mapping_state": rec.mapping_state,
                "amount_signal": amount(rec.amount_total),
                "fact_rows": rec.rows_total,
            }
        )
    for rec in env["sc.legacy.project.map"].search(  # noqa: F821
        [("source_table", "=", "SCBS_GCMC_PROJECT_CANDIDATE"), ("mapping_state", "!=", "confirmed")],
        order="amount_total desc",
        limit=10,
    ):
        examples.append(
            {
                "dimension": "project",
                "legacy_key": rec.legacy_gcmc,
                "legacy_name": rec.legacy_gcmc,
                "mapping_state": rec.mapping_state,
                "amount_signal": amount(rec.amount_total),
                "fact_rows": rec.rows_total,
            }
        )
    for rec in env["sc.legacy.partner.map"].search(  # noqa: F821
        [("source_table", "=", "SCBS_PARTNER_DUPLICATE_CANDIDATE"), ("mapping_state", "!=", "confirmed")],
        order="active_rows desc",
        limit=10,
    ):
        examples.append(
            {
                "dimension": "partner",
                "legacy_key": rec.legacy_key,
                "legacy_name": rec.legacy_partner_name,
                "mapping_state": rec.mapping_state,
                "amount_signal": "",
                "fact_rows": rec.active_rows,
            }
        )
    return examples


def gate_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    by_dimension: dict[str, dict[str, object]] = {}
    for row in rows:
        dimension = str(row["dimension"])
        bucket = by_dimension.setdefault(
            dimension,
            {
                "candidate_count": 0,
                "confirmed_count": 0,
                "conflict_count": 0,
                "unconfirmed_count": 0,
                "mapped_target_count": 0,
                "fact_rows": 0,
                "amount_signal": 0.0,
            },
        )
        count = int(row.get("candidate_count") or 0)
        bucket["candidate_count"] += count
        bucket["mapped_target_count"] += int(row.get("mapped_target_count") or 0)
        bucket["fact_rows"] += int(row.get("fact_rows") or 0)
        if row.get("amount_signal") != "":
            bucket["amount_signal"] = amount(float(bucket["amount_signal"]) + float(row.get("amount_signal") or 0))
        if row.get("mapping_state") == "confirmed":
            bucket["confirmed_count"] += count
        else:
            bucket["unconfirmed_count"] += count
        if row.get("mapping_state") == "conflict":
            bucket["conflict_count"] += count
    return by_dimension


def apply_target_counts(gates: dict[str, dict[str, object]]) -> None:
    target_domains = {
        "business_entity": (
            "sc.legacy.business.entity.map",
            [("source_table", "=", "SCBS_BUSINESS_ENTITY_CANDIDATE"), ("business_entity_id", "!=", False)],
        ),
        "project": (
            "sc.legacy.project.map",
            [("source_table", "=", "SCBS_GCMC_PROJECT_CANDIDATE"), ("project_id", "!=", False)],
        ),
        "partner": (
            "sc.legacy.partner.map",
            [("source_table", "=", "SCBS_PARTNER_DUPLICATE_CANDIDATE"), ("partner_id", "!=", False)],
        ),
    }
    for dimension, (model_name, domain) in target_domains.items():
        if dimension in gates:
            gates[dimension]["mapped_target_count"] = env[model_name].search_count(domain)  # noqa: F821


def apply_detail_target_counts(rows: list[dict[str, object]]) -> None:
    for row in rows:
        dimension = row["dimension"]
        if dimension == "business_entity":
            row["mapped_target_count"] = env["sc.legacy.business.entity.map"].search_count(  # noqa: F821
                [
                    ("source_table", "=", "SCBS_BUSINESS_ENTITY_CANDIDATE"),
                    ("suggested_entity_type", "=", row["suggested_state"]),
                    ("mapping_state", "=", row["mapping_state"]),
                    ("business_entity_id", "!=", False),
                ]
            )
        elif dimension == "project":
            row["mapped_target_count"] = env["sc.legacy.project.map"].search_count(  # noqa: F821
                [
                    ("source_table", "=", "SCBS_GCMC_PROJECT_CANDIDATE"),
                    ("suggested_state", "=", row["suggested_state"]),
                    ("mapping_state", "=", row["mapping_state"]),
                    ("match_method", "=", row["match_method"]),
                    ("project_id", "!=", False),
                ]
            )
        elif dimension == "partner":
            row["mapped_target_count"] = env["sc.legacy.partner.map"].search_count(  # noqa: F821
                [
                    ("source_table", "=", "SCBS_PARTNER_DUPLICATE_CANDIDATE"),
                    ("suggested_state", "=", row["suggested_state"]),
                    ("mapping_state", "=", row["mapping_state"]),
                    ("match_method", "=", row["match_method"]),
                    ("partner_id", "!=", False),
                ]
            )


def markdown(payload: dict[str, object], summary_rows: list[dict[str, object]], examples: list[dict[str, object]]) -> str:
    lines = [
        "# SCBS Mapping Reconciliation",
        "",
        f"Database: `{payload['database']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Gate Summary",
        "",
        "| Dimension | Candidates | Confirmed | Unconfirmed | Conflicts | Mapped targets | Fact rows | Amount signal |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for dimension, row in payload["gate_summary"].items():
        lines.append(
            "| {dimension} | {candidate_count} | {confirmed_count} | {unconfirmed_count} | {conflict_count} | "
            "{mapped_target_count} | {fact_rows} | {amount_signal:.2f} |".format(dimension=dimension, **row)
        )
    lines.extend(
        [
            "",
            "## Detailed Split",
            "",
            "| Dimension | Suggested state | Mapping state | Match method | Candidates | Mapped targets | Fact rows | Amount signal |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {dimension} | {suggested_state} | {mapping_state} | {match_method} | {candidate_count} | "
            "{mapped_target_count} | {fact_rows} | {amount_signal} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Largest Unresolved Examples",
            "",
            "| Dimension | Legacy key | Legacy name | State | Fact rows | Amount signal |",
            "| --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in examples:
        lines.append(
            "| {dimension} | `{legacy_key}` | {legacy_name} | {mapping_state} | {fact_rows} | {amount_signal} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "Formal fact projection is blocked until required mapping rows are confirmed. "
            "Staging import can proceed only if it preserves raw legacy keys and mapping state.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    artifacts = artifact_root()
    result_json = artifacts / "scbs_mapping_reconciliation_result_v1.json"
    summary_csv = artifacts / "scbs_mapping_reconciliation_summary_v1.csv"
    examples_csv = artifacts / "scbs_mapping_reconciliation_unresolved_examples_v1.csv"
    report_md = artifacts / "scbs_mapping_reconciliation_report_v1.md"

    summary_rows = business_entity_rows() + project_rows() + partner_rows()
    apply_detail_target_counts(summary_rows)
    examples = unresolved_examples()
    gates = gate_summary(summary_rows)
    apply_target_counts(gates)
    status = "BLOCK_FORMAL_FACT_PROJECTION" if any(row["unconfirmed_count"] for row in gates.values()) else "PASS"
    payload = {
        "status": status,
        "database": env.cr.dbname,  # noqa: F821
        "gate_summary": gates,
        "summary_csv": str(summary_csv),
        "unresolved_examples_csv": str(examples_csv),
        "report_md": str(report_md),
    }
    write_json(result_json, payload)
    write_csv(
        summary_csv,
        [
            "dimension",
            "suggested_state",
            "mapping_state",
            "match_method",
            "candidate_count",
            "mapped_target_count",
            "fact_rows",
            "amount_signal",
            "legacy_rows",
        ],
        summary_rows,
    )
    write_csv(
        examples_csv,
        ["dimension", "legacy_key", "legacy_name", "mapping_state", "fact_rows", "amount_signal"],
        examples,
    )
    report_md.write_text(markdown(payload, summary_rows, examples), encoding="utf-8")
    print("SCBS_MAPPING_RECONCILIATION=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
