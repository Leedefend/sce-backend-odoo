import csv
import json
from pathlib import Path


ARTIFACT_DIR = Path("/mnt/artifacts/migration")
INPUT_CSV = ARTIFACT_DIR / "contract_header_bounded_dry_run_rows_v1.csv"
ROLLBACK_CSVS = [
    ARTIFACT_DIR / "contract_header_slice200_rollback_targets_v1.csv",
    ARTIFACT_DIR / "contract_header_next200_rollback_targets_v1.csv",
    ARTIFACT_DIR / "contract_header_post400_next200_rollback_targets_v1.csv",
    ARTIFACT_DIR / "contract_header_post600_next200_rollback_targets_v1.csv",
    ARTIFACT_DIR / "contract_header_post800_next200_rollback_targets_v1.csv",
    ARTIFACT_DIR / "contract_header_post1000_next200_rollback_targets_v1.csv",
    ARTIFACT_DIR / "contract_header_final132_rollback_targets_v1.csv",
]
OUTPUT_JSON = ARTIFACT_DIR / "contract_header_final_aggregate_confirm_result_v1.json"
EXPECTED_COUNT = 1332


def read_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if env.cr.dbname != "sc_demo":  # noqa: F821
    raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

source_rows = read_csv_rows(INPUT_CSV)
rollback_rows = []
for path in ROLLBACK_CSVS:
    rollback_rows.extend(read_csv_rows(path))

source_ids = {row.get("legacy_contract_id") for row in source_rows if row.get("legacy_contract_id")}
rollback_ids = {row.get("legacy_contract_id") for row in rollback_rows if row.get("legacy_contract_id")}
records = env["construction.contract"].sudo().search([("legacy_contract_id", "in", list(source_ids))])  # noqa: F821
target_ids = {rec.legacy_contract_id for rec in records if rec.legacy_contract_id}

errors = []
if len(source_rows) != EXPECTED_COUNT:
    errors.append({"kind": "source_count_not_1332", "actual": len(source_rows)})
if len(source_ids) != EXPECTED_COUNT:
    errors.append({"kind": "source_unique_legacy_count_not_1332", "actual": len(source_ids)})
if len(rollback_rows) != EXPECTED_COUNT:
    errors.append({"kind": "rollback_count_not_1332", "actual": len(rollback_rows)})
if len(rollback_ids) != EXPECTED_COUNT:
    errors.append({"kind": "rollback_unique_legacy_count_not_1332", "actual": len(rollback_ids)})
if len(records) != EXPECTED_COUNT:
    errors.append({"kind": "target_match_count_not_1332", "actual": len(records)})
if source_ids != rollback_ids:
    errors.append({"kind": "source_rollback_legacy_set_mismatch", "missing_from_rollback": sorted(source_ids - rollback_ids)[:20]})
if source_ids != target_ids:
    errors.append({"kind": "source_target_legacy_set_mismatch", "missing_from_target": sorted(source_ids - target_ids)[:20]})

payload = {
    "status": "PASS" if not errors else "FAIL",
    "mode": "contract_header_final_aggregate_confirm",
    "database": env.cr.dbname,  # noqa: F821
    "db_writes": 0,
    "source_rows": len(source_rows),
    "source_unique_legacy_ids": len(source_ids),
    "rollback_rows": len(rollback_rows),
    "rollback_unique_legacy_ids": len(rollback_ids),
    "target_match_rows": len(records),
    "target_unique_legacy_ids": len(target_ids),
    "errors": errors,
}
write_json(OUTPUT_JSON, payload)
env.cr.rollback()  # noqa: F821
print("CONTRACT_HEADER_FINAL_AGGREGATE_CONFIRM=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise RuntimeError({"contract_header_final_aggregate_confirm_failed": errors})
