"""Audit legal role_key values, freeze mapping, and write first three L3 rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


RUN_ID = "ITER-2026-04-14-L3-ROLE-KEY-AUDIT-MAPPED-WRITE"
SOURCE_SEMANTIC = "historical_project_member_l3_sample"
SAMPLE_SIZE = 3
ROLE_SOURCE_EVIDENCE = "migration_l3_role_key_audit_mapped_write_v1"
BUSINESS_REVIEWER = "system_migration_task"

ARTIFACT_ROOT = Path("/mnt/artifacts") if Path("/mnt/artifacts").exists() else Path("artifacts")
MIGRATION_DIR = ARTIFACT_ROOT / "migration"
CHECKLIST_CSV = MIGRATION_DIR / "project_member_l3_business_review_checklist_v1.csv"
ROLE_AUDIT_JSON = MIGRATION_DIR / "project_member_l3_role_key_audit_v1.json"
MAPPING_RULE_JSON = MIGRATION_DIR / "project_member_l3_role_key_mapping_rule_v1.json"
WRITE_RESULT_JSON = MIGRATION_DIR / "project_member_l3_mapped_write_result_v1.json"
POST_AUDIT_JSON = MIGRATION_DIR / "project_member_l3_mapped_write_post_audit_v1.json"
ROLLBACK_CSV = MIGRATION_DIR / "project_member_l3_mapped_write_rollback_targets_v1.csv"


def clean(value):
    return ("" if value is None else str(value)).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def ensure_odoo_env():
    if "env" not in globals():
        raise RuntimeError({"odoo_env_required": True})
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821


def load_first_three_rows():
    fields, rows = read_csv(CHECKLIST_CSV)
    required = {"review_rank", "pair_key", "project_id", "project_name", "user_id", "user_name"}
    missing = sorted(required - set(fields))
    if missing:
        raise RuntimeError({"missing_checklist_columns": missing})
    selected = sorted(rows, key=lambda row: int(clean(row.get("review_rank")) or "0"))[:SAMPLE_SIZE]
    if len(selected) != SAMPLE_SIZE:
        raise RuntimeError({"sample_size_not_3": len(selected)})
    ranks = [int(clean(row["review_rank"])) for row in selected]
    if ranks != [1, 2, 3]:
        raise RuntimeError({"first_three_review_ranks_not_selected": ranks})
    return selected


def selection_pairs(model):
    field = model._fields["role_key"]
    selection = field.selection
    if callable(selection):
        selection = selection(model)
    return [{"role_key": key, "label": label} for key, label in selection]


def audit_role_surface(selected):
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    legal_selection = selection_pairs(responsibility)
    legal_keys = [row["role_key"] for row in legal_selection]
    existing_records = responsibility.search([])
    role_distribution = Counter(record.role_key for record in existing_records if record.role_key)
    user_ids = sorted({int(clean(row["user_id"])) for row in selected})
    project_ids = sorted({int(clean(row["project_id"])) for row in selected})
    sample_user_distribution = Counter(
        record.role_key
        for record in responsibility.search([("user_id", "in", user_ids)])
        if record.role_key
    )
    sample_project_records = responsibility.search([("project_id", "in", project_ids)])
    sample_project_existing = [
        {
            "responsibility_id": record.id,
            "project_id": record.project_id.id,
            "user_id": record.user_id.id,
            "role_key": record.role_key or "",
        }
        for record in sample_project_records
    ]
    payload = {
        "status": "PASS",
        "run_id": RUN_ID,
        "model": "project.responsibility",
        "field": "role_key",
        "legal_selection": legal_selection,
        "legal_role_keys": legal_keys,
        "existing_distribution": dict(sorted(role_distribution.items())),
        "existing_total": sum(role_distribution.values()),
        "sample_user_ids": user_ids,
        "sample_project_ids": project_ids,
        "sample_user_distribution": dict(sorted(sample_user_distribution.items())),
        "sample_project_existing_responsibilities": sample_project_existing,
        "db_writes": 0,
    }
    write_json(ROLE_AUDIT_JSON, payload)
    return payload


def freeze_mapping(audit):
    distribution = audit["existing_distribution"]
    legal = set(audit["legal_role_keys"])
    ranked = sorted(
        ((role_key, count) for role_key, count in distribution.items() if role_key in legal),
        key=lambda item: (-item[1], item[0]),
    )
    label_map = {row["role_key"]: row["label"] for row in audit["legal_selection"]}
    if ranked:
        role_key, count = ranked[0]
        mapping_rule = "choose_highest_frequency_existing_legal_role_key_in_target_distribution"
        mapping_basis = "existing_distribution"
    else:
        role_key, count = "manager", 0
        if role_key not in legal:
            raise RuntimeError({"fallback_role_key_not_legal": role_key, "legal_role_keys": audit["legal_role_keys"]})
        mapping_rule = "fallback_to_project_level_primary_role_from_model_selection_when_distribution_empty"
        mapping_basis = "model_field_selection_fallback"
    payload = {
        "status": "FROZEN",
        "run_id": RUN_ID,
        "source_business_semantic": SOURCE_SEMANTIC,
        "target_model": "project.responsibility",
        "target_field": "role_key",
        "mapped_role_key": role_key,
        "mapped_role_label": label_map.get(role_key, ""),
        "mapping_rule": mapping_rule,
        "mapping_basis": mapping_basis,
        "mapping_evidence": {
            "selected_role_key_existing_count": count,
            "existing_distribution": distribution,
            "legal_role_keys": audit["legal_role_keys"],
        },
        "sample_size": SAMPLE_SIZE,
        "no_acl_record_rule_change": True,
        "no_model_selection_change": True,
    }
    write_json(MAPPING_RULE_JSON, payload)
    return payload


def create_rows(selected, mapping):
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    role_key = mapping["mapped_role_key"]
    created = []
    conflicts = []
    for row in selected:
        project_id = int(clean(row["project_id"]))
        user_id = int(clean(row["user_id"]))
        existing = responsibility.search(
            [("project_id", "=", project_id), ("user_id", "=", user_id), ("role_key", "=", role_key)],
            limit=1,
        )
        if existing:
            if existing.note and RUN_ID in existing.note:
                created.append(
                    {
                        "responsibility_id": existing.id,
                        "project_id": project_id,
                        "project_name": clean(row["project_name"]),
                        "user_id": user_id,
                        "user_name": clean(row["user_name"]),
                        "role_key": existing.role_key or "",
                        "role_label": mapping["mapped_role_label"],
                        "pair_key": clean(row["pair_key"]),
                        "write_action_result": "recovered_existing_created_by_run_id",
                    }
                )
                continue
            conflicts.append({"responsibility_id": existing.id, "pair_key": clean(row["pair_key"]), "role_key": role_key})
            continue
        rec = responsibility.create(
            {
                "project_id": project_id,
                "user_id": user_id,
                "role_key": role_key,
                "is_primary": False,
                "note": (
                    f"{RUN_ID}; pair_key={clean(row['pair_key'])}; "
                    f"source_business_semantic={SOURCE_SEMANTIC}; "
                    f"mapping_rule={mapping['mapping_rule']}; "
                    f"role_source_evidence={ROLE_SOURCE_EVIDENCE}; "
                    f"business_reviewer={BUSINESS_REVIEWER}"
                ),
            }
        )
        created.append(
            {
                "responsibility_id": rec.id,
                "project_id": project_id,
                "project_name": clean(row["project_name"]),
                "user_id": user_id,
                "user_name": clean(row["user_name"]),
                "role_key": rec.role_key or "",
                "role_label": mapping["mapped_role_label"],
                "pair_key": clean(row["pair_key"]),
                "write_action_result": "created",
            }
        )
    if conflicts:
        raise RuntimeError({"existing_project_responsibility_conflicts": conflicts})
    return created


def audit_created(created, mapping):
    responsibility = env["project.responsibility"].sudo()  # noqa: F821
    ids = [row["responsibility_id"] for row in created]
    records = responsibility.browse(ids).exists()
    rows = []
    for record in records:
        rows.append(
            {
                "responsibility_id": record.id,
                "project_id": record.project_id.id,
                "user_id": record.user_id.id,
                "role_key": record.role_key or "",
                "rollback_eligible": bool(record.note and RUN_ID in record.note),
            }
        )
    blocking_reasons = []
    if len(rows) != SAMPLE_SIZE:
        blocking_reasons.append("matched_records_not_3")
    if any(row["role_key"] != mapping["mapped_role_key"] for row in rows):
        blocking_reasons.append("role_key_mismatch")
    if any(not row["rollback_eligible"] for row in rows):
        blocking_reasons.append("rollback_eligibility_missing")
    payload = {
        "status": "PASS" if not blocking_reasons else "FAIL",
        "run_id": RUN_ID,
        "mapped_role_key": mapping["mapped_role_key"],
        "matched_records": len(rows),
        "rollback_eligible_rows": sum(1 for row in rows if row["rollback_eligible"]),
        "db_writes": 0,
        "blocking_reasons": blocking_reasons,
        "rows": rows,
    }
    write_json(POST_AUDIT_JSON, payload)
    return payload


def main():
    ensure_odoo_env()
    selected = load_first_three_rows()
    audit = audit_role_surface(selected)
    mapping = freeze_mapping(audit)
    created = []
    try:
        created = create_rows(selected, mapping)
        if len(created) != SAMPLE_SIZE:
            raise RuntimeError({"created_count_not_3": len(created)})
        env.cr.commit()  # noqa: F821
    except Exception as exc:
        env.cr.rollback()  # noqa: F821
        payload = {
            "status": "FAIL",
            "run_id": RUN_ID,
            "mapped_role_key": mapping.get("mapped_role_key"),
            "created": 0,
            "db_writes": 0,
            "error": repr(exc),
        }
        write_json(WRITE_RESULT_JSON, payload)
        write_csv(
            ROLLBACK_CSV,
            ["run_id", "responsibility_id", "project_id", "user_id", "role_key", "pair_key", "write_action_result"],
            [],
        )
        write_json(
            POST_AUDIT_JSON,
            {
                "status": "FAIL",
                "run_id": RUN_ID,
                "mapped_role_key": mapping.get("mapped_role_key"),
                "matched_records": 0,
                "rollback_eligible_rows": 0,
                "db_writes": 0,
                "blocking_reasons": ["write_failed"],
                "error": repr(exc),
            },
        )
        print("PROJECT_MEMBER_L3_ROLE_KEY_AUDIT_MAPPED_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        raise
    write_csv(
        ROLLBACK_CSV,
        [
            "run_id",
            "responsibility_id",
            "project_id",
            "project_name",
            "user_id",
            "user_name",
            "role_key",
            "role_label",
            "pair_key",
            "write_action_result",
        ],
        [{"run_id": RUN_ID, **row} for row in created],
    )
    write_result = {
        "status": "PASS",
        "run_id": RUN_ID,
        "mapped_role_key": mapping["mapped_role_key"],
        "mapped_role_label": mapping["mapped_role_label"],
        "mapping_rule": mapping["mapping_rule"],
        "sample_rows": SAMPLE_SIZE,
        "created": len(created),
        "updated": 0,
        "db_writes": len(created),
        "created_rows": created,
        "rollback_targets": str(ROLLBACK_CSV),
    }
    write_json(WRITE_RESULT_JSON, write_result)
    post_audit = audit_created(created, mapping)
    print("PROJECT_MEMBER_L3_ROLE_KEY_AUDIT_MAPPED_WRITE=" + json.dumps({
        "status": write_result["status"],
        "mapped_role_key": write_result["mapped_role_key"],
        "created": write_result["created"],
        "db_writes": write_result["db_writes"],
        "post_audit_status": post_audit["status"],
    }, ensure_ascii=False, sort_keys=True))
    if post_audit["status"] != "PASS":
        raise RuntimeError({"post_audit_failed": post_audit})


main()
