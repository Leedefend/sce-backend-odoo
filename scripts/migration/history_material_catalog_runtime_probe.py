#!/usr/bin/env python3
"""Read-only probe for historical material catalog visibility and controlled promotion."""

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
        "# History Material Catalog Runtime Probe v1",
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


ARTIFACT_ROOT = resolve_artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "history_material_catalog_runtime_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "history_material_catalog_runtime_probe_report_v1.md"

counts = {
    "material_category_rows": count_table("sc_legacy_material_category"),
    "material_category_with_parent": count_table("sc_legacy_material_category", "parent_id IS NOT NULL"),
    "material_detail_rows": count_table("sc_legacy_material_detail"),
    "material_detail_active_rows": count_table("sc_legacy_material_detail", "active"),
    "material_detail_with_category": count_table("sc_legacy_material_detail", "category_id IS NOT NULL"),
    "material_detail_with_project": count_table("sc_legacy_material_detail", "project_id IS NOT NULL"),
    "material_detail_with_code": count_table("sc_legacy_material_detail", "code IS NOT NULL AND code <> ''"),
    "material_detail_promoted": count_table("sc_legacy_material_detail", "promotion_state = 'promoted'"),
    "product_templates_from_legacy_material": count_table("product_template", "legacy_material_detail_id IS NOT NULL"),
}

distributions = {
    "top_uom": [
        {"uom_text": row[0], "rows": int(row[1])}
        for row in rows(
            """
            SELECT uom_text, COUNT(*)
            FROM sc_legacy_material_detail
            GROUP BY uom_text
            ORDER BY COUNT(*) DESC
            LIMIT 20
            """
        )
    ] if table_exists("sc_legacy_material_detail") else [],
}

samples = {
    "material_detail": [
        {
            "id": row[0],
            "legacy_material_id": row[1],
            "code": row[2],
            "name": row[3],
            "spec_model": row[4],
            "uom_text": row[5],
            "promotion_state": row[6],
        }
        for row in rows(
            """
            SELECT id, legacy_material_id, code, name, spec_model, uom_text, promotion_state
            FROM sc_legacy_material_detail
            WHERE active
            ORDER BY legacy_material_id
            LIMIT 5
            """
        )
    ] if table_exists("sc_legacy_material_detail") else [],
}

gaps = {
    "missing_material_category_surface": counts["material_category_rows"] == 0,
    "missing_material_detail_surface": counts["material_detail_rows"] == 0,
    "missing_category_linkage": counts["material_detail_rows"] > 0 and counts["material_detail_with_category"] == 0,
    "missing_promotion_fields": not (
        table_exists("sc_legacy_material_detail")
        and table_exists("product_template")
        and scalar("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'sc_legacy_material_detail' AND column_name = 'promotion_state'")
        and scalar("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'product_template' AND column_name = 'legacy_material_detail_id'")
    ),
}
failing_gaps = [key for key, value in gaps.items() if value]
decision = "history_material_catalog_runtime_ready" if not failing_gaps else "history_material_catalog_runtime_gap"

payload = {
    "status": "PASS",
    "mode": "history_material_catalog_runtime_probe",
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
    "HISTORY_MATERIAL_CATALOG_RUNTIME_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "database": payload["database"],
            "decision": decision,
            "gap_count": len(failing_gaps),
            "material_category_rows": counts["material_category_rows"],
            "material_detail_rows": counts["material_detail_rows"],
            "material_detail_promoted": counts["material_detail_promoted"],
            "db_writes": 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
