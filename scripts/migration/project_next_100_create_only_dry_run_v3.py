"""Build and dry-run the next non-overlapping 100-row project candidate v3."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


RAW_PROJECT_CSV = Path("tmp/raw/project/project.csv")
MATERIALIZED_PROJECT_CSVS = [
    Path("artifacts/migration/project_create_only_post_write_snapshot_v1.csv"),
    Path("artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv"),
    Path("artifacts/migration/project_v2_100_post_write_snapshot.csv"),
]
OUTPUT_CSV = Path("artifacts/migration/project_next_100_candidate_v3.csv")
OUTPUT_JSON = Path("artifacts/migration/project_next_100_dry_run_result_v3.json")

SAFE_FIELDS = [
    "legacy_project_id",
    "legacy_parent_id",
    "name",
    "short_name",
    "project_environment",
    "legacy_company_id",
    "legacy_company_name",
    "legacy_specialty_type_id",
    "specialty_type_name",
    "legacy_price_method",
    "business_nature",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_is_shared_base",
    "legacy_sort",
    "legacy_attachment_ref",
    "project_overview",
    "legacy_project_nature",
    "legacy_is_material_library",
    "other_system_id",
    "other_system_code",
]

SOURCE_TO_SAFE = {
    "ID": "legacy_project_id",
    "PID": "legacy_parent_id",
    "XMMC": "name",
    "SHORT_NAME": "short_name",
    "PROJECT_ENV": "project_environment",
    "COMPANYID": "legacy_company_id",
    "COMPANYNAME": "legacy_company_name",
    "SPECIALTY_TYPE_ID": "legacy_specialty_type_id",
    "SPECIALTY_TYPE_NAME": "specialty_type_name",
    "PRICE_METHOD": "legacy_price_method",
    "NATURE": "business_nature",
    "DETAIL_ADDRESS": "detail_address",
    "PROFILE": "project_profile",
    "AREA": "project_area",
    "IS_SHARED_BASE": "legacy_is_shared_base",
    "SORT": "legacy_sort",
    "FJ": "legacy_attachment_ref",
    "PROJECTOVERVIEW": "project_overview",
    "PROJECT_NATURE": "legacy_project_nature",
    "IS_MACHINTERIAL_LIBRARY": "legacy_is_material_library",
    "OTHER_SYSTEM_ID": "other_system_id",
    "OTHER_SYSTEM_CODE": "other_system_code",
}

NULL_VALUES = {"", "null", "none", "n/a", "na"}
SINGLE_LINE_FIELDS = set(SAFE_FIELDS) - {"project_profile", "project_overview"}


def clean_value(value, *, single_line=True):
    raw = "" if value is None else str(value)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if raw.lower() in NULL_VALUES:
        return ""
    if single_line:
        raw = raw.replace("\n", " ")
        raw = re.sub(r"[ \t]+", " ", raw)
    return raw


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def existing_project_ids():
    ids = set()
    source_counts = {}
    for path in MATERIALIZED_PROJECT_CSVS:
        path_count = 0
        for row in read_csv(path):
            legacy_id = clean_value(row.get("legacy_project_id"), single_line=True)
            if legacy_id:
                ids.add(legacy_id)
                path_count += 1
        source_counts[str(path)] = path_count
    return ids, source_counts


def to_safe_row(raw):
    safe_row = {target: "" for target in SAFE_FIELDS}
    for source, target in SOURCE_TO_SAFE.items():
        safe_row[target] = clean_value(raw.get(source), single_line=target in SINGLE_LINE_FIELDS)
    return safe_row


existing_ids, materialized_source_counts = existing_project_ids()
raw_rows = read_csv(RAW_PROJECT_CSV)
selected = []
skipped_existing = 0
seen = set()

for raw in raw_rows:
    safe = to_safe_row(raw)
    legacy_id = safe["legacy_project_id"]
    if not legacy_id:
        continue
    if legacy_id in existing_ids:
        skipped_existing += 1
        continue
    if legacy_id in seen:
        continue
    selected.append(safe)
    seen.add(legacy_id)
    if len(selected) == 100:
        break

write_csv(OUTPUT_CSV, SAFE_FIELDS, selected)

id_counts = Counter(row["legacy_project_id"] for row in selected if row["legacy_project_id"])
results = []
errors = []
creates = 0

for index, row in enumerate(selected, start=2):
    row_errors = []
    if not row["legacy_project_id"]:
        row_errors.append("missing legacy_project_id")
    if not row["name"]:
        row_errors.append("missing name")
    if row["legacy_project_id"] in existing_ids:
        row_errors.append("already_materialized")
    if row["legacy_project_id"] and id_counts[row["legacy_project_id"]] > 1:
        row_errors.append("duplicate legacy_project_id in input")
    action = "error" if row_errors else "create"
    if action == "create":
        creates += 1
    for error in row_errors:
        errors.append({"line": index, "legacy_project_id": row["legacy_project_id"], "error": error})
    results.append(
        {
            "line": index,
            "legacy_project_id": row["legacy_project_id"],
            "name": row["name"],
            "action": action,
            "errors": row_errors,
        }
    )

payload = {
    "status": "PASS" if len(selected) == 100 and not errors else "FAIL",
    "mode": "project_next_100_create_only_dry_run_v3_no_db_no_orm",
    "raw_project_rows": len(raw_rows),
    "materialized_source_counts": materialized_source_counts,
    "already_materialized_project_rows": len(existing_ids),
    "skipped_existing_rows": skipped_existing,
    "candidate_csv": str(OUTPUT_CSV),
    "row_count": len(selected),
    "safe_field_count": len(SAFE_FIELDS),
    "summary": {
        "create": creates,
        "update": 0,
        "error": len({item["line"] for item in errors}),
    },
    "errors": errors,
    "results": results,
    "next_step": "open write authorization packet for this v3 100-row project create-only candidate",
}
write_json(OUTPUT_JSON, payload)
print(
    "PROJECT_NEXT_100_DRY_RUN_V3="
    + json.dumps(
        {
            "status": payload["status"],
            "raw_project_rows": payload["raw_project_rows"],
            "already_materialized_project_rows": payload["already_materialized_project_rows"],
            "row_count": payload["row_count"],
            "create": payload["summary"]["create"],
            "error": payload["summary"]["error"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
