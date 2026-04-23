"""Build no-DB authorization packet for project v3 100-row candidate."""

from __future__ import annotations

import csv
import json
from pathlib import Path


CANDIDATE_CSV = Path("artifacts/migration/project_next_100_candidate_v3.csv")
DRY_RUN_JSON = Path("artifacts/migration/project_next_100_dry_run_result_v3.json")
OUTPUT_JSON = Path("artifacts/migration/project_v3_100_write_authorization_packet.json")

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


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


dry_run = json.loads(DRY_RUN_JSON.read_text(encoding="utf-8"))
fieldnames, rows = read_csv(CANDIDATE_CSV)
missing = [field for field in SAFE_FIELDS if field not in fieldnames]
extra = [field for field in fieldnames if field not in SAFE_FIELDS]

blockers = []
if dry_run.get("status") != "PASS":
    blockers.append("dry_run_not_pass")
if dry_run.get("summary", {}).get("create") != 100:
    blockers.append("create_count_not_100")
if dry_run.get("summary", {}).get("update") != 0:
    blockers.append("update_candidate_detected")
if dry_run.get("summary", {}).get("error") != 0:
    blockers.append("dry_run_errors_detected")
if len(rows) != 100:
    blockers.append("candidate_not_100_rows")
if missing:
    blockers.append("missing_safe_fields")
if extra:
    blockers.append("unsafe_extra_fields")

payload = {
    "status": "PASS" if not blockers else "PASS_WITH_BLOCKERS",
    "mode": "project_v3_100_write_authorization_packet_no_db",
    "candidate_csv": str(CANDIDATE_CSV),
    "dry_run_json": str(DRY_RUN_JSON),
    "payload_rows": len(rows),
    "blocked_rows": 0 if not blockers else len(rows),
    "blockers": blockers,
    "field_check": {
        "missing": missing,
        "extra": extra,
    },
    "write_authorization": "not_granted",
    "write_scope": {
        "model": "project.project",
        "operation": "create_only",
        "row_count": len(rows),
        "allowed_fields": SAFE_FIELDS,
        "forbidden_operations": ["update", "unlink", "workflow replay", "ACL/security changes"],
    },
    "authorization_boundary": "real project write requires separate explicit authorization after this packet",
    "next_step": "stop for explicit project v3 100-row write authorization",
}
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    "PROJECT_V3_100_WRITE_AUTH_PACKET="
    + json.dumps(
        {
            "status": payload["status"],
            "payload_rows": payload["payload_rows"],
            "blockers": payload["blockers"],
            "write_authorization": payload["write_authorization"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
