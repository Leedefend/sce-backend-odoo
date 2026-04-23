"""Readonly consolidated pair projection for project_member neutral evidence."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


PROFILE_JSON = Path("/mnt/artifacts/migration/project_member_neutral_pair_consolidation_profile_v1.json")
PAIRS_JSON = Path("/mnt/artifacts/migration/project_member_consolidated_pairs_v1.json")
PAIRS_CSV = Path("/mnt/artifacts/migration/project_member_consolidated_pairs_v1.csv")
SUMMARY_JSON = Path("/mnt/artifacts/migration/project_member_consolidated_summary_v1.json")

TARGET_MODEL = "sc.project.member.staging"
EXPECTED_PAIR_COUNT = 362


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pair_key(record):
    return f"{record.project_id.id}:{record.user_id.id}"


def promotion_candidate(statuses):
    return any(status != "missing" for status in statuses)


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    profile = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
    if profile.get("status") != "PASS":
        raise RuntimeError({"za_profile_not_pass": profile.get("status")})
    if profile.get("pair_key") != "project_id + user_id":
        raise RuntimeError({"pair_key_not_frozen": profile.get("pair_key")})

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    records = model.search([], order="project_id, user_id, id")
    grouped = defaultdict(list)
    for record in records:
        grouped[pair_key(record)].append(record)

    projection_rows = []
    csv_rows = []
    evidence_count_counter = Counter()
    role_status_counter = Counter()
    batch_counter = Counter()

    for key in sorted(grouped, key=lambda value: tuple(int(part) for part in value.split(":"))):
        pair_records = grouped[key]
        first = pair_records[0]
        evidence_count = len(pair_records)
        evidence_batches = sorted({record.import_batch for record in pair_records})
        role_statuses = sorted({record.role_fact_status for record in pair_records})
        role_fact_status_summary = "+".join(role_statuses)
        candidate = promotion_candidate(role_statuses)
        evidence_row_ids = [record.id for record in pair_records]
        batch_distribution = dict(sorted(Counter(record.import_batch for record in pair_records).items()))

        item = {
            "pair_key": key,
            "project_id": first.project_id.id,
            "project_name": first.project_id.name or "",
            "user_id": first.user_id.id,
            "user_name": first.user_id.name or "",
            "evidence_count": evidence_count,
            "evidence_batches": evidence_batches,
            "first_seen_batch": evidence_batches[0] if evidence_batches else "",
            "last_seen_batch": evidence_batches[-1] if evidence_batches else "",
            "role_fact_status": role_fact_status_summary,
            "role_fact_status_summary": role_fact_status_summary,
            "batch_distribution": batch_distribution,
            "duplicate_flag": evidence_count > 1,
            "evidence_row_ids": evidence_row_ids,
            "promotion_candidate": candidate,
        }
        projection_rows.append(item)
        csv_rows.append({
            "pair_key": item["pair_key"],
            "project_id": item["project_id"],
            "project_name": item["project_name"],
            "user_id": item["user_id"],
            "user_name": item["user_name"],
            "evidence_count": item["evidence_count"],
            "duplicate_flag": "yes" if item["duplicate_flag"] else "no",
            "role_fact_status": item["role_fact_status"],
            "promotion_candidate": "yes" if item["promotion_candidate"] else "no",
            "evidence_batches": ",".join(item["evidence_batches"]),
            "evidence_row_ids": ",".join(str(value) for value in item["evidence_row_ids"]),
        })
        evidence_count_counter[str(evidence_count)] += 1
        role_status_counter[role_fact_status_summary] += 1
        for batch in evidence_batches:
            batch_counter[batch] += 1

    summary = {
        "status": "PASS",
        "mode": "project_member_consolidated_pair_projection_summary",
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "total_pairs": len(projection_rows),
        "pairs_with_duplicates": sum(1 for row in projection_rows if row["duplicate_flag"]),
        "pairs_without_duplicates": sum(1 for row in projection_rows if not row["duplicate_flag"]),
        "max_evidence_per_pair": max((row["evidence_count"] for row in projection_rows), default=0),
        "role_fact_missing_pairs": sum(1 for row in projection_rows if row["role_fact_status"] == "missing"),
        "promotion_candidate_pairs": sum(1 for row in projection_rows if row["promotion_candidate"]),
        "pairs_grouped_by_evidence_count": dict(sorted(evidence_count_counter.items(), key=lambda item: int(item[0]))),
        "role_fact_status_grouped_by_pair": dict(sorted(role_status_counter.items())),
        "batch_distribution_by_pair": dict(sorted(batch_counter.items())),
    }

    blocking_reasons = []
    if len(projection_rows) != EXPECTED_PAIR_COUNT:
        blocking_reasons.append({"error": "pair_count_not_362", "actual": len(projection_rows)})
    required_fields = {
        "project_id",
        "project_name",
        "user_id",
        "user_name",
        "evidence_count",
        "evidence_batches",
        "first_seen_batch",
        "last_seen_batch",
        "role_fact_status",
        "duplicate_flag",
        "evidence_row_ids",
        "promotion_candidate",
    }
    for index, row in enumerate(projection_rows, start=1):
        missing = sorted(field for field in required_fields if field not in row)
        if missing:
            blocking_reasons.append({"error": "missing_required_projection_field", "row": index, "fields": missing})
            break
    if blocking_reasons:
        summary["status"] = "BLOCKED"
        summary["blocking_reasons"] = blocking_reasons
    else:
        summary["blocking_reasons"] = []

    output = {
        "status": summary["status"],
        "mode": "project_member_consolidated_pair_projection",
        "database": env.cr.dbname,  # noqa: F821
        "db_writes": 0,
        "projection_type": "readonly_governance_projection",
        "source_model": TARGET_MODEL,
        "pair_key": "project_id + user_id",
        "total_pairs": len(projection_rows),
        "pairs": projection_rows,
        "blocking_reasons": summary["blocking_reasons"],
    }
    write_json(PAIRS_JSON, output)
    write_csv(
        PAIRS_CSV,
        [
            "pair_key",
            "project_id",
            "project_name",
            "user_id",
            "user_name",
            "evidence_count",
            "duplicate_flag",
            "role_fact_status",
            "promotion_candidate",
            "evidence_batches",
            "evidence_row_ids",
        ],
        csv_rows,
    )
    write_json(SUMMARY_JSON, summary)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_CONSOLIDATED_PAIR_PROJECTION=" + json.dumps({
        "status": output["status"],
        "total_pairs": summary["total_pairs"],
        "pairs_with_duplicates": summary["pairs_with_duplicates"],
        "pairs_without_duplicates": summary["pairs_without_duplicates"],
        "max_evidence_per_pair": summary["max_evidence_per_pair"],
        "role_fact_missing_pairs": summary["role_fact_missing_pairs"],
        "promotion_candidate_pairs": summary["promotion_candidate_pairs"],
        "db_writes": output["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_consolidated_pair_projection_blocked": blocking_reasons})


main()
