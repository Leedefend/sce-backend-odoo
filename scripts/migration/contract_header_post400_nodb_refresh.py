import csv
import json
from pathlib import Path


ARTIFACT_DIR = Path("/mnt/artifacts/migration")
INPUT_CSV = ARTIFACT_DIR / "contract_header_bounded_dry_run_rows_v1.csv"
FIRST_WRITE_JSON = ARTIFACT_DIR / "contract_header_slice200_write_result_v1.json"
NEXT_WRITE_JSON = ARTIFACT_DIR / "contract_header_next200_write_result_v1.json"
FIRST_ROLLBACK_CSV = ARTIFACT_DIR / "contract_header_slice200_rollback_targets_v1.csv"
NEXT_ROLLBACK_CSV = ARTIFACT_DIR / "contract_header_next200_rollback_targets_v1.csv"
RESULT_JSON = ARTIFACT_DIR / "contract_header_post400_nodb_refresh_result_v1.json"
REMAINING_CSV = ARTIFACT_DIR / "contract_header_remaining_after_400_v1.csv"
NEXT_SLICE_CSV = ARTIFACT_DIR / "contract_header_next_slice200_after_400_v1.csv"

DATABASE = "sc_demo"
EXPECTED_INPUT_ROWS = 1332
EXPECTED_WRITTEN_ROWS = 400
EXPECTED_REMAINING_ROWS = 932
NEXT_SLICE_LIMIT = 200


def read_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


errors = []
if env.cr.dbname != DATABASE:
    errors.append({"kind": "wrong_database", "expected": DATABASE, "actual": env.cr.dbname})

input_rows = read_csv_rows(INPUT_CSV)
first_rollback_rows = read_csv_rows(FIRST_ROLLBACK_CSV)
next_rollback_rows = read_csv_rows(NEXT_ROLLBACK_CSV)
first_write = read_json(FIRST_WRITE_JSON)
next_write = read_json(NEXT_WRITE_JSON)
rollback_rows = first_rollback_rows + next_rollback_rows

if len(input_rows) != EXPECTED_INPUT_ROWS:
    errors.append({"kind": "unexpected_input_rows", "expected": EXPECTED_INPUT_ROWS, "actual": len(input_rows)})
if first_write.get("status") != "PASS" or int(first_write.get("created") or 0) != 200:
    errors.append({"kind": "first_write_not_pass", "write_result": first_write})
if next_write.get("status") != "PASS" or int(next_write.get("created") or 0) != 200:
    errors.append({"kind": "next_write_not_pass", "write_result": next_write})
if len(rollback_rows) != EXPECTED_WRITTEN_ROWS:
    errors.append({"kind": "unexpected_rollback_rows", "expected": EXPECTED_WRITTEN_ROWS, "actual": len(rollback_rows)})

legacy_ids = [row["legacy_contract_id"] for row in input_rows if row.get("legacy_contract_id")]
rollback_legacy_ids = [row["legacy_contract_id"] for row in rollback_rows if row.get("legacy_contract_id")]

if len(set(legacy_ids)) != len(legacy_ids):
    errors.append({"kind": "duplicate_input_legacy_contract_id"})
if len(set(rollback_legacy_ids)) != len(rollback_legacy_ids):
    errors.append({"kind": "duplicate_rollback_legacy_contract_id"})

Contract = env["construction.contract"].sudo()
existing_records = Contract.search([("legacy_contract_id", "in", legacy_ids)])
existing_legacy_ids = {rec.legacy_contract_id for rec in existing_records if rec.legacy_contract_id}
written_existing_ids = sorted(set(rollback_legacy_ids) & existing_legacy_ids)
remaining_rows = [row for row in input_rows if row.get("legacy_contract_id") not in existing_legacy_ids]
next_slice_rows = remaining_rows[:NEXT_SLICE_LIMIT]

extra_existing_ids = sorted(existing_legacy_ids - set(rollback_legacy_ids))
missing_written_ids = sorted(set(rollback_legacy_ids) - existing_legacy_ids)

if len(written_existing_ids) != EXPECTED_WRITTEN_ROWS:
    errors.append({"kind": "existing_written_count_not_400", "actual": len(written_existing_ids)})
if missing_written_ids:
    errors.append({"kind": "missing_written_ids", "count": len(missing_written_ids), "sample": missing_written_ids[:20]})
if extra_existing_ids:
    errors.append({"kind": "extra_existing_ids_from_candidate_set", "count": len(extra_existing_ids), "sample": extra_existing_ids[:20]})
if len(remaining_rows) != EXPECTED_REMAINING_ROWS:
    errors.append({"kind": "remaining_candidate_count_not_932", "actual": len(remaining_rows)})
if len(next_slice_rows) != NEXT_SLICE_LIMIT:
    errors.append({"kind": "next_slice_count_not_200", "actual": len(next_slice_rows)})

fieldnames = list(input_rows[0].keys()) if input_rows else []
write_csv(REMAINING_CSV, remaining_rows, fieldnames)
write_csv(NEXT_SLICE_CSV, next_slice_rows, fieldnames)

result = {
    "status": "PASS" if not errors else "FAIL",
    "mode": "contract_header_post400_nodb_refresh",
    "database": env.cr.dbname,
    "db_writes": 0,
    "input_rows": len(input_rows),
    "upstream_created_rows": int(first_write.get("created") or 0) + int(next_write.get("created") or 0),
    "rollback_target_rows": len(rollback_rows),
    "existing_candidate_rows": len(existing_legacy_ids),
    "written_existing_rows": len(written_existing_ids),
    "extra_existing_rows": len(extra_existing_ids),
    "missing_written_rows": len(missing_written_ids),
    "remaining_rows": len(remaining_rows),
    "next_slice_rows": len(next_slice_rows),
    "errors": errors,
    "artifacts": {
        "remaining_csv": str(REMAINING_CSV),
        "next_slice_csv": str(NEXT_SLICE_CSV),
    },
    "next_step": "open next 200-row contract header readonly precheck" if not errors else "stop_and_review_errors",
}

RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
env.cr.rollback()

if errors:
    raise Exception("CONTRACT_HEADER_POST400_NODB_REFRESH_FAILED=" + json.dumps(result, ensure_ascii=False, sort_keys=True))

print("CONTRACT_HEADER_POST400_NODB_REFRESH=" + json.dumps({
    "status": result["status"],
    "input_rows": result["input_rows"],
    "written_existing_rows": result["written_existing_rows"],
    "remaining_rows": result["remaining_rows"],
    "next_slice_rows": result["next_slice_rows"],
    "db_writes": result["db_writes"],
}, ensure_ascii=False, sort_keys=True))
