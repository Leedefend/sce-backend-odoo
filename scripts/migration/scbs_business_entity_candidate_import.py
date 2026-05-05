"""Import SCBS business-entity candidates into Odoo staging models.

Run through Odoo shell:

    odoo shell -c /var/lib/odoo/odoo.conf -d sc_prod_sim \\
      < scripts/migration/scbs_business_entity_candidate_import.py

Default mode is dry-run. To write, set:

    SCBS_BUSINESS_ENTITY_IMPORT_MODE=write

The script consumes ``artifacts/migration/scbs_business_entity_candidates_v1.csv``.
It creates or updates candidate ``sc.business.entity`` and
``sc.legacy.business.entity.map`` rows only. It never creates ``res.company`` and
never projects SCBS facts into formal business documents.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def clean(value) -> str:
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def as_int(value) -> int:
    text = clean(value)
    return int(float(text)) if text else 0


def as_float(value) -> float:
    text = clean(value)
    if text in {"", "."}:
        return 0.0
    if text.startswith("."):
        text = "0" + text
    return float(text)


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/scbs_business_entity_candidates_v1.csv").exists():
            return candidate
    return Path.cwd()


def artifact_root(root: Path) -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([root / "artifacts/migration", Path("/mnt/artifacts/migration"), Path("/tmp")])
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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def partner_candidate(name: str):
    Partner = env["res.partner"]  # noqa: F821
    if not name:
        return Partner.browse()
    matches = Partner.search([("name", "=", name), ("active", "=", True)], limit=2)
    return matches if len(matches) == 1 else Partner.browse()


def entity_type(suggested_state: str, name: str) -> str:
    if suggested_state == "platform_candidate" or name == "公司综合平台":
        return "platform"
    if "劳务" in name:
        return "labor"
    if "商贸" in name or "建材销售" in name:
        return "trade"
    return "unknown"


def evidence(row: dict[str, str]) -> str:
    return json.dumps(
        {
            "source": "scbs_business_entity_candidates_v1.csv",
            "suggested_state": clean(row.get("suggested_state")),
            "source_count": as_int(row.get("source_count")),
            "rows_total": as_int(row.get("rows_total")),
            "partner_rows": as_int(row.get("partner_rows")),
            "payment_rows": as_int(row.get("payment_rows")),
            "payment_amount": as_float(row.get("payment_amount")),
            "contract_rows": as_int(row.get("contract_rows")),
            "contract_amount": as_float(row.get("contract_amount")),
            "stock_rows": as_int(row.get("stock_rows")),
            "stock_amount": as_float(row.get("stock_amount")),
            "fund_rows": as_int(row.get("fund_rows")),
            "fund_balance": as_float(row.get("fund_balance")),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def main() -> None:
    ensure_allowed_db()
    mode = os.getenv("SCBS_BUSINESS_ENTITY_IMPORT_MODE", "dry-run")
    write_mode = mode == "write"
    if mode not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_mode": mode, "expected": ["dry-run", "write"]})

    root = repo_root()
    artifacts = artifact_root(root)
    input_csv = root / "artifacts/migration/scbs_business_entity_candidates_v1.csv"
    result_json = artifacts / "scbs_business_entity_candidate_import_result_v1.json"
    rollback_csv = artifacts / "scbs_business_entity_candidate_import_rollback_targets_v1.csv"
    preview_csv = artifacts / "scbs_business_entity_candidate_import_preview_v1.csv"

    rows = read_rows(input_csv)
    company = env.company  # noqa: F821
    Entity = env["sc.business.entity"]  # noqa: F821
    Mapping = env["sc.legacy.business.entity.map"]  # noqa: F821

    preview_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    created_entities = 0
    updated_entities = 0
    created_maps = 0
    updated_maps = 0

    for index, row in enumerate(rows, start=2):
        legacy_xmid = clean(row.get("legacy_xmid"))
        legacy_xmmc = clean(row.get("legacy_xmmc"))
        suggested_state = clean(row.get("suggested_state"))
        if not legacy_xmid or not legacy_xmmc:
            errors.append({"line": index, "error": "missing legacy_xmid_or_xmmc"})
            continue
        if suggested_state not in {"business_entity_candidate", "platform_candidate"}:
            errors.append({"line": index, "legacy_xmid": legacy_xmid, "error": "unexpected_suggested_state"})
            continue

        target_entity_type = entity_type(suggested_state, legacy_xmmc)
        partner = partner_candidate(legacy_xmmc)
        entity = Entity.search(
            [
                ("company_id", "=", company.id),
                ("legacy_xmid", "=", legacy_xmid),
            ],
            limit=1,
        )
        mapping = Mapping.search(
            [
                ("source_table", "=", "SCBS_BUSINESS_ENTITY_CANDIDATE"),
                ("legacy_xmid", "=", legacy_xmid),
            ],
            limit=1,
        )
        entity_vals = {
            "name": legacy_xmmc,
            "company_id": company.id,
            "entity_type": target_entity_type,
            "mapping_state": "candidate",
            "legacy_xmid": legacy_xmid,
            "legacy_xmmc": legacy_xmmc,
            "legacy_company_id": clean(row.get("legacy_company_id")),
            "legacy_company_name": clean(row.get("legacy_company_name")),
        }
        if partner:
            entity_vals["partner_id"] = partner.id

        map_vals = {
            "source_table": "SCBS_BUSINESS_ENTITY_CANDIDATE",
            "source_domain": "SCBS",
            "legacy_xmid": legacy_xmid,
            "legacy_xmmc": legacy_xmmc,
            "legacy_company_id": clean(row.get("legacy_company_id")),
            "legacy_company_name": clean(row.get("legacy_company_name")),
            "company_id": company.id,
            "suggested_entity_type": target_entity_type,
            "mapping_state": "candidate",
            "source_count": as_int(row.get("source_count")),
            "rows_total": as_int(row.get("rows_total")),
            "amount_total": as_float(row.get("payment_amount"))
            + as_float(row.get("contract_amount"))
            + as_float(row.get("stock_amount"))
            + as_float(row.get("fund_balance")),
            "confidence": 0.9 if suggested_state == "business_entity_candidate" else 0.75,
            "evidence": evidence(row),
        }
        if partner:
            map_vals["partner_id"] = partner.id

        preview_rows.append(
            {
                "legacy_xmid": legacy_xmid,
                "legacy_xmmc": legacy_xmmc,
                "suggested_state": suggested_state,
                "entity_action": "update" if entity else "create",
                "map_action": "update" if mapping else "create",
                "partner_id": partner.id if partner else "",
                "entity_type": target_entity_type,
                "rows_total": as_int(row.get("rows_total")),
                "amount_total": map_vals["amount_total"],
            }
        )

        if not write_mode:
            continue

        if entity:
            entity.write(entity_vals)
            updated_entities += 1
        else:
            entity = Entity.create(entity_vals)
            created_entities += 1

        map_vals["business_entity_id"] = entity.id
        if mapping:
            mapping.write(map_vals)
            updated_maps += 1
        else:
            mapping = Mapping.create(map_vals)
            created_maps += 1
        rollback_rows.extend(
            [
                {
                    "model": "sc.legacy.business.entity.map",
                    "id": mapping.id,
                    "legacy_xmid": legacy_xmid,
                    "name": mapping.legacy_xmmc,
                },
                {
                    "model": "sc.business.entity",
                    "id": entity.id,
                    "legacy_xmid": legacy_xmid,
                    "name": entity.name,
                },
            ]
        )

    preview_fields = [
        "legacy_xmid",
        "legacy_xmmc",
        "suggested_state",
        "entity_action",
        "map_action",
        "partner_id",
        "entity_type",
        "rows_total",
        "amount_total",
    ]
    write_csv(preview_csv, preview_fields, preview_rows)
    write_csv(rollback_csv, ["model", "id", "legacy_xmid", "name"], rollback_rows)

    if errors:
        payload = {
            "status": "FAIL",
            "mode": mode,
            "database": env.cr.dbname,  # noqa: F821
            "input_csv": str(input_csv),
            "errors": errors,
            "preview_csv": str(preview_csv),
        }
        write_json(result_json, payload)
        raise RuntimeError(payload)

    if write_mode:
        env.cr.commit()  # noqa: F821

    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "input_csv": str(input_csv),
        "candidate_rows": len(rows),
        "preview_rows": len(preview_rows),
        "created_entities": created_entities,
        "updated_entities": updated_entities,
        "created_maps": created_maps,
        "updated_maps": updated_maps,
        "preview_csv": str(preview_csv),
        "rollback_csv": str(rollback_csv),
        "business_entity_count": Entity.search_count([("legacy_xmid", "!=", False)]),
        "mapping_count": Mapping.search_count([("source_table", "=", "SCBS_BUSINESS_ENTITY_CANDIDATE")]),
    }
    write_json(result_json, payload)
    print("SCBS_BUSINESS_ENTITY_CANDIDATE_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
