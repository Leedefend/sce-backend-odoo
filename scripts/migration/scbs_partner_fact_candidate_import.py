"""Create partner mapping candidates for SCBS fact counterparties not covered by duplicate/conflict matrix.

Run through Odoo shell. Default mode is dry-run; set
``SCBS_PARTNER_FACT_CANDIDATE_IMPORT_MODE=write`` to create/update
``sc.legacy.partner.map`` candidates. This script does not create or merge
``res.partner`` rows.
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


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_prod_sim,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821 - Odoo shell global
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def partner_key(name: str, tax_code: str) -> str:
    return "|".join([name.casefold(), tax_code.casefold(), "fact_partner_candidate"])


def partner_matches(name: str, tax_code: str):
    Partner = env["res.partner"]  # noqa: F821
    if tax_code:
        vat_matches = Partner.with_context(active_test=False).search(
            ["|", ("vat", "=", tax_code), ("legacy_tax_no", "=", tax_code)],
            limit=3,
        )
        if len(vat_matches) == 1:
            return vat_matches, "tax_code"
        if len(vat_matches) > 1:
            return vat_matches, "multiple"
    name_matches = Partner.with_context(active_test=False).search([("name", "=", name)], limit=3)
    if len(name_matches) == 1:
        return name_matches, "exact_name"
    if len(name_matches) > 1:
        return name_matches, "multiple"
    return Partner.browse(), "none"


def confidence(method: str, target_count: int) -> float:
    if method == "tax_code" and target_count == 1:
        return 0.9
    if method == "exact_name" and target_count == 1:
        return 0.65
    if method == "multiple":
        return 0.35
    return 0.25


def fetch_missing_candidates() -> list[dict[str, object]]:
    env.cr.execute(  # noqa: F821
        """
        SELECT s.legacy_partner_name,
               COALESCE(NULLIF(MAX(s.legacy_partner_tax_code), ''), '') AS legacy_tax_code,
               COUNT(*) AS fact_rows,
               ROUND(SUM(s.amount_total)::numeric, 2) AS amount_total,
               STRING_AGG(DISTINCT s.source_table, ', ' ORDER BY s.source_table) AS source_tables,
               STRING_AGG(DISTINCT s.fact_family, ', ' ORDER BY s.fact_family) AS fact_families
          FROM sc_legacy_scbs_fact_staging s
          LEFT JOIN sc_legacy_partner_map m
            ON m.source_domain = 'SCBS'
           AND m.legacy_partner_name = s.legacy_partner_name
         WHERE s.import_batch = 'scbs_fact_staging_v1'
           AND s.legacy_partner_name IS NOT NULL
           AND s.legacy_partner_name <> ''
           AND m.id IS NULL
         GROUP BY s.legacy_partner_name
         ORDER BY SUM(s.amount_total) DESC, COUNT(*) DESC
        """
    )
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def main() -> None:
    ensure_allowed_db()
    mode = os.getenv("SCBS_PARTNER_FACT_CANDIDATE_IMPORT_MODE", "dry-run")
    write_mode = mode == "write"
    if mode not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_mode": mode, "expected": ["dry-run", "write"]})

    artifacts = artifact_root()
    result_json = artifacts / "scbs_partner_fact_candidate_import_result_v1.json"
    preview_csv = artifacts / "scbs_partner_fact_candidate_import_preview_v1.csv"
    rollback_csv = artifacts / "scbs_partner_fact_candidate_import_rollback_targets_v1.csv"

    Mapping = env["sc.legacy.partner.map"]  # noqa: F821
    rows = fetch_missing_candidates()
    preview_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    created = 0
    updated = 0

    for row in rows:
        name = str(row["legacy_partner_name"] or "").strip()
        tax_code = str(row["legacy_tax_code"] or "").strip()
        key = partner_key(name, tax_code)
        targets, method = partner_matches(name, tax_code)
        target = targets if len(targets) == 1 else env["res.partner"].browse()  # noqa: F821
        mapping = Mapping.search([("source_table", "=", "SCBS_FACT_PARTNER_CANDIDATE"), ("legacy_key", "=", key)], limit=1)
        vals = {
            "source_table": "SCBS_FACT_PARTNER_CANDIDATE",
            "source_domain": "SCBS",
            "legacy_key": key,
            "legacy_partner_name": name,
            "legacy_tax_code": tax_code,
            "company_id": env.company.id,  # noqa: F821
            "partner_id": target.id if target else False,
            "mapping_state": "candidate",
            "suggested_state": "fact_partner_candidate",
            "match_method": method,
            "confidence": confidence(method, len(targets)),
            "legacy_rows": int(row["fact_rows"] or 0),
            "active_rows": int(row["fact_rows"] or 0),
            "tax_code_count": 1 if tax_code else 0,
            "carrier_count": 0,
            "target_partner_count": len(targets),
            "evidence": json.dumps(
                {
                    "source": "scbs_fact_staging_v1",
                    "source_tables": row["source_tables"],
                    "fact_families": row["fact_families"],
                    "fact_rows": int(row["fact_rows"] or 0),
                    "amount_total": float(row["amount_total"] or 0),
                    "target_partner_ids": targets.ids,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
        preview_rows.append(
            {
                "legacy_partner_name": name,
                "legacy_tax_code": tax_code,
                "action": "update" if mapping else "create",
                "partner_id": target.id if target else "",
                "match_method": method,
                "target_partner_count": len(targets),
                "fact_rows": row["fact_rows"],
                "amount_total": row["amount_total"],
            }
        )
        if not write_mode:
            continue
        if mapping:
            mapping.write(vals)
            updated += 1
        else:
            mapping = Mapping.create(vals)
            created += 1
        rollback_rows.append(
            {
                "model": "sc.legacy.partner.map",
                "id": mapping.id,
                "legacy_key": key,
                "name": name,
            }
        )

    write_csv(
        preview_csv,
        [
            "legacy_partner_name",
            "legacy_tax_code",
            "action",
            "partner_id",
            "match_method",
            "target_partner_count",
            "fact_rows",
            "amount_total",
        ],
        preview_rows,
    )
    write_csv(rollback_csv, ["model", "id", "legacy_key", "name"], rollback_rows)
    if write_mode:
        env.cr.commit()  # noqa: F821
    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "candidate_rows": len(rows),
        "created_maps": created,
        "updated_maps": updated,
        "mapping_count": Mapping.search_count([("source_table", "=", "SCBS_FACT_PARTNER_CANDIDATE")]),
        "preview_csv": str(preview_csv),
        "rollback_csv": str(rollback_csv),
    }
    write_json(result_json, payload)
    print("SCBS_PARTNER_FACT_CANDIDATE_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
