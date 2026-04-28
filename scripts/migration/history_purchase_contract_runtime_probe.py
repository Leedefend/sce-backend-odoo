#!/usr/bin/env python3
"""Read-only probe for historical purchase/general contract runtime visibility."""

from __future__ import annotations

import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core/__manifest__.py").exists():
            return candidate
    return Path.cwd()


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(repo_root() / "artifacts/migration")
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# History Purchase Contract Runtime Probe v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Decision",
        "",
        f"`{payload['decision']}`",
        "",
        "## Counts",
        "",
        "```json",
        json.dumps(payload["counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gaps",
        "",
        "```json",
        json.dumps(payload["gaps"], ensure_ascii=False, indent=2),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def table_exists(table_name: str) -> bool:
    env.cr.execute("SELECT to_regclass(%s)", [table_name])  # noqa: F821
    return bool(env.cr.fetchone()[0])  # noqa: F821


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def rows(sql: str, params: list[object] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


def count_table(table_name: str, where: str = "TRUE") -> int:
    if not table_exists(table_name):
        return 0
    return int(scalar(f"SELECT COUNT(*) FROM {table_name} WHERE {where}") or 0)


def sum_table(table_name: str, column_name: str, where: str = "TRUE") -> float:
    if not table_exists(table_name):
        return 0.0
    return float(scalar(f"SELECT COALESCE(SUM({column_name}), 0) FROM {table_name} WHERE {where}") or 0.0)


ARTIFACT_ROOT = resolve_artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "history_purchase_contract_runtime_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_purchase_contract_runtime_probe_report_v1.md"

counts = {
    "purchase_contract_rows": count_table("sc_legacy_purchase_contract_fact"),
    "purchase_contract_active_rows": count_table("sc_legacy_purchase_contract_fact", "active"),
    "purchase_contract_with_project": count_table("sc_legacy_purchase_contract_fact", "project_id IS NOT NULL"),
    "purchase_contract_with_partner_text": count_table("sc_legacy_purchase_contract_fact", "partner_name IS NOT NULL AND partner_name <> ''"),
    "purchase_contract_with_credit_code": count_table("sc_legacy_purchase_contract_fact", "credit_code IS NOT NULL AND credit_code <> ''"),
    "purchase_contract_with_amount": count_table("sc_legacy_purchase_contract_fact", "total_amount <> 0"),
    "purchase_contract_amount": sum_table("sc_legacy_purchase_contract_fact", "total_amount", "active"),
    "purchase_contract_strong_anchor_candidates": count_table(
        "sc_legacy_purchase_contract_fact",
        "active AND project_id IS NOT NULL AND partner_name IS NOT NULL AND partner_name <> '' AND total_amount <> 0",
    ),
}

distributions = {
    "by_contract_type": [
        {"contract_type": row[0], "rows": int(row[1]), "amount": float(row[2] or 0)}
        for row in rows(
            """
            SELECT contract_type, COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM sc_legacy_purchase_contract_fact
            WHERE active
            GROUP BY contract_type
            ORDER BY COUNT(*) DESC
            LIMIT 20
            """
        )
    ] if table_exists("sc_legacy_purchase_contract_fact") else [],
    "by_sign_status": [
        {"sign_status": row[0], "rows": int(row[1]), "amount": float(row[2] or 0)}
        for row in rows(
            """
            SELECT sign_status, COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM sc_legacy_purchase_contract_fact
            WHERE active
            GROUP BY sign_status
            ORDER BY COUNT(*) DESC
            LIMIT 20
            """
        )
    ] if table_exists("sc_legacy_purchase_contract_fact") else [],
}

samples = {
    "purchase_contract": [
        {
            "id": row[0],
            "legacy_record_id": row[1],
            "contract_no": row[2],
            "contract_name": row[3],
            "project_id": row[4],
            "partner_name": row[5],
            "amount": float(row[6] or 0),
        }
        for row in rows(
            """
            SELECT id, legacy_record_id, contract_no, contract_name, project_id, partner_name, total_amount
            FROM sc_legacy_purchase_contract_fact
            WHERE active
            ORDER BY submitted_time DESC NULLS LAST, id DESC
            LIMIT 5
            """
        )
    ] if table_exists("sc_legacy_purchase_contract_fact") else [],
}

gaps = {
    "missing_purchase_contract_surface": counts["purchase_contract_rows"] == 0,
    "purchase_contract_project_link_gap": counts["purchase_contract_rows"] > 0 and counts["purchase_contract_with_project"] == 0,
    "purchase_contract_partner_text_gap": counts["purchase_contract_rows"] > 0 and counts["purchase_contract_with_partner_text"] == 0,
}
failing_gaps = [key for key, value in gaps.items() if value]
decision = "history_purchase_contract_runtime_ready" if not failing_gaps else "history_purchase_contract_runtime_gap"

payload = {
    "status": "PASS",
    "mode": "history_purchase_contract_runtime_probe",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "counts": counts,
    "distributions": distributions,
    "samples": samples,
    "gaps": gaps,
    "decision": decision,
}

write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print(
    "HISTORY_PURCHASE_CONTRACT_RUNTIME_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": decision,
            "gap_count": len(failing_gaps),
            "purchase_contract_rows": counts["purchase_contract_rows"],
            "strong_anchor_candidates": counts["purchase_contract_strong_anchor_candidates"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
