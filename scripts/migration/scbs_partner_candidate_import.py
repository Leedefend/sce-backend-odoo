"""Import SCBS partner duplicate/conflict candidates into Odoo review mapping.

Run through Odoo shell:

    odoo shell -c /var/lib/odoo/odoo.conf -d sc_prod_sim \\
      < scripts/migration/scbs_partner_candidate_import.py

Default mode is dry-run. To write, set:

    SCBS_PARTNER_CANDIDATE_IMPORT_MODE=write

The script consumes ``artifacts/migration/scbs_partner_candidates_v1.csv``.
It creates or updates ``sc.legacy.partner.map`` rows only. It never creates,
merges, archives, or rewrites ``res.partner`` rows.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def clean(value) -> str:
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def null_clean(value) -> str:
    text = clean(value)
    return "" if text.upper() == "NULL" else text


def as_int(value) -> int:
    text = clean(value)
    return int(float(text)) if text else 0


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/scbs_partner_candidates_v1.csv").exists():
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


def legacy_key(name: str, tax_code: str, suggested_state: str) -> str:
    return "|".join([name.casefold(), tax_code.casefold(), suggested_state])


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


def default_mapping_state(suggested_state: str) -> str:
    return "conflict" if suggested_state == "tax_code_conflict" else "candidate"


def confidence(suggested_state: str, method: str, target_count: int) -> float:
    if suggested_state == "tax_code_conflict":
        return 0.1
    if method == "tax_code" and target_count == 1:
        return 0.9
    if method == "exact_name" and target_count == 1:
        return 0.65
    if method == "multiple":
        return 0.35
    return 0.2


def evidence(row: dict[str, str], target_ids: list[int]) -> str:
    return json.dumps(
        {
            "source": "scbs_partner_candidates_v1.csv",
            "suggested_state": clean(row.get("suggested_state")),
            "legacy_rows": as_int(row.get("legacy_rows")),
            "active_rows": as_int(row.get("active_rows")),
            "tax_code_count": as_int(row.get("tax_code_count")),
            "carrier_count": as_int(row.get("carrier_count")),
            "sample_carrier": null_clean(row.get("sample_carrier")),
            "max_carrier": null_clean(row.get("max_carrier")),
            "target_partner_ids": target_ids,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def main() -> None:
    ensure_allowed_db()
    mode = os.getenv("SCBS_PARTNER_CANDIDATE_IMPORT_MODE", "dry-run")
    write_mode = mode == "write"
    if mode not in {"dry-run", "write"}:
        raise RuntimeError({"invalid_mode": mode, "expected": ["dry-run", "write"]})

    root = repo_root()
    artifacts = artifact_root(root)
    input_csv = root / "artifacts/migration/scbs_partner_candidates_v1.csv"
    result_json = artifacts / "scbs_partner_candidate_import_result_v1.json"
    rollback_csv = artifacts / "scbs_partner_candidate_import_rollback_targets_v1.csv"
    preview_csv = artifacts / "scbs_partner_candidate_import_preview_v1.csv"

    rows = read_rows(input_csv)
    company = env.company  # noqa: F821
    Mapping = env["sc.legacy.partner.map"]  # noqa: F821

    allowed_states = {"duplicate_across_carriers", "duplicate_same_carrier_or_empty_tax", "tax_code_conflict"}
    preview_rows: list[dict[str, object]] = []
    rollback_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    created_maps = 0
    updated_maps = 0

    for index, row in enumerate(rows, start=2):
        name = clean(row.get("partner_name"))
        tax_code = null_clean(row.get("sample_tax_code"))
        suggested_state = clean(row.get("suggested_state"))
        if not name:
            errors.append({"line": index, "error": "missing_partner_name"})
            continue
        if suggested_state not in allowed_states:
            errors.append({"line": index, "partner_name": name, "error": "unexpected_suggested_state"})
            continue

        key = legacy_key(name, tax_code, suggested_state)
        targets, method = partner_matches(name, tax_code)
        target = targets if len(targets) == 1 and suggested_state != "tax_code_conflict" else env["res.partner"].browse()  # noqa: F821
        vals = {
            "source_table": "SCBS_PARTNER_DUPLICATE_CANDIDATE",
            "source_domain": "SCBS",
            "legacy_key": key,
            "legacy_partner_name": name,
            "legacy_tax_code": tax_code,
            "company_id": company.id,
            "partner_id": target.id if target else False,
            "mapping_state": default_mapping_state(suggested_state),
            "suggested_state": suggested_state,
            "match_method": method,
            "confidence": confidence(suggested_state, method, len(targets)),
            "legacy_rows": as_int(row.get("legacy_rows")),
            "active_rows": as_int(row.get("active_rows")),
            "tax_code_count": as_int(row.get("tax_code_count")),
            "carrier_count": as_int(row.get("carrier_count")),
            "sample_carrier": null_clean(row.get("sample_carrier")),
            "max_carrier": null_clean(row.get("max_carrier")),
            "target_partner_count": len(targets),
            "evidence": evidence(row, targets.ids),
        }
        mapping = Mapping.search(
            [
                ("source_table", "=", "SCBS_PARTNER_DUPLICATE_CANDIDATE"),
                ("legacy_key", "=", key),
            ],
            limit=1,
        )
        preview_rows.append(
            {
                "legacy_partner_name": name,
                "legacy_tax_code": tax_code,
                "suggested_state": suggested_state,
                "map_action": "update" if mapping else "create",
                "mapping_state": vals["mapping_state"],
                "partner_id": target.id if target else "",
                "match_method": method,
                "target_partner_count": len(targets),
                "legacy_rows": vals["legacy_rows"],
                "active_rows": vals["active_rows"],
            }
        )

        if not write_mode:
            continue
        if mapping:
            mapping.write(vals)
            updated_maps += 1
        else:
            mapping = Mapping.create(vals)
            created_maps += 1
        rollback_rows.append(
            {
                "model": "sc.legacy.partner.map",
                "id": mapping.id,
                "legacy_key": key,
                "name": mapping.legacy_partner_name,
            }
        )

    preview_fields = [
        "legacy_partner_name",
        "legacy_tax_code",
        "suggested_state",
        "map_action",
        "mapping_state",
        "partner_id",
        "match_method",
        "target_partner_count",
        "legacy_rows",
        "active_rows",
    ]
    write_csv(preview_csv, preview_fields, preview_rows)
    write_csv(rollback_csv, ["model", "id", "legacy_key", "name"], rollback_rows)

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
        "created_maps": created_maps,
        "updated_maps": updated_maps,
        "preview_csv": str(preview_csv),
        "rollback_csv": str(rollback_csv),
        "mapping_count": Mapping.search_count([("source_table", "=", "SCBS_PARTNER_DUPLICATE_CANDIDATE")]),
    }
    write_json(result_json, payload)
    print("SCBS_PARTNER_CANDIDATE_IMPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
