"""Readonly pair-consolidation profile for project_member neutral carrier."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


OUTPUT_JSON = Path("/mnt/artifacts/migration/project_member_neutral_pair_consolidation_profile_v1.json")
TARGET_MODEL = "sc.project.member.staging"
EXPECTED_EVIDENCE_ROWS = 534
EXPECTED_DISTINCT_PAIRS = 362


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pair_key(record):
    return f"{record.project_id.id}:{record.user_id.id}"


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    model = env[TARGET_MODEL].sudo()  # noqa: F821
    records = model.search([], order="project_id, user_id, id")
    by_pair = defaultdict(list)
    for record in records:
        by_pair[pair_key(record)].append(record)

    evidence_count_distribution = Counter()
    role_status_by_pair = Counter()
    batch_distribution_by_pair = Counter()
    duplicate_samples = []
    pair_samples = []

    for key, pair_records in by_pair.items():
        evidence_count = len(pair_records)
        evidence_count_distribution[str(evidence_count)] += 1
        role_statuses = sorted({record.role_fact_status for record in pair_records})
        batches = sorted({record.import_batch for record in pair_records})
        role_status_summary = "+".join(role_statuses)
        batch_summary = "+".join(batches)
        role_status_by_pair[role_status_summary] += 1
        batch_distribution_by_pair[batch_summary] += 1

        first = pair_records[0]
        item = {
            "pair_key": key,
            "project_id": first.project_id.id,
            "project_name": first.project_id.name or "",
            "user_id": first.user_id.id,
            "user_name": first.user_id.name or "",
            "evidence_count": evidence_count,
            "role_fact_status_summary": role_status_summary,
            "batch_list": batches,
            "duplicate_evidence": evidence_count > 1,
            "first_neutral_id": pair_records[0].id,
            "last_neutral_id": pair_records[-1].id,
        }
        if len(pair_samples) < 50:
            pair_samples.append(item)
        if evidence_count > 1 and len(duplicate_samples) < 50:
            duplicate_samples.append(item)

    blocking_reasons = []
    if len(records) != EXPECTED_EVIDENCE_ROWS:
        blocking_reasons.append({"error": "unexpected_evidence_row_count", "expected": EXPECTED_EVIDENCE_ROWS, "actual": len(records)})
    if len(by_pair) != EXPECTED_DISTINCT_PAIRS:
        blocking_reasons.append({"error": "unexpected_distinct_pair_count", "expected": EXPECTED_DISTINCT_PAIRS, "actual": len(by_pair)})
    if any(not record.project_id or not record.user_id for record in records):
        blocking_reasons.append({"error": "missing_project_or_user_on_evidence"})

    payload = {
        "status": "PASS" if not blocking_reasons else "BLOCKED",
        "mode": "project_member_neutral_pair_consolidation_profile",
        "database": env.cr.dbname,  # noqa: F821
        "target_model": TARGET_MODEL,
        "db_writes": 0,
        "evidence_layer": True,
        "consolidated_pair_projection": "readonly_governance_projection",
        "pair_key": "project_id + user_id",
        "total_evidence_rows": len(records),
        "total_distinct_pairs": len(by_pair),
        "duplicate_pair_count": sum(1 for items in by_pair.values() if len(items) > 1),
        "max_evidence_per_pair": max((len(items) for items in by_pair.values()), default=0),
        "pairs_grouped_by_evidence_count": dict(sorted(evidence_count_distribution.items(), key=lambda item: int(item[0]))),
        "role_fact_status_grouped_by_pair": dict(sorted(role_status_by_pair.items())),
        "batch_distribution_by_pair": dict(sorted(batch_distribution_by_pair.items())),
        "sample_duplicate_pairs": duplicate_samples,
        "sample_pairs": pair_samples,
        "promotion_gate": {
            "confirmed_project_id": True,
            "confirmed_user_id": True,
            "verified_role_fact_required": True,
            "no_existing_project_responsibility_conflict_required": True,
            "promotion_scope": "pair",
            "promotion_executed_in_this_batch": False,
        },
        "blocking_reasons": blocking_reasons,
    }
    write_json(OUTPUT_JSON, payload)
    env.cr.rollback()  # noqa: F821
    print("PROJECT_MEMBER_NEUTRAL_PAIR_CONSOLIDATION_PROFILE=" + json.dumps({
        "status": payload["status"],
        "total_evidence_rows": payload["total_evidence_rows"],
        "total_distinct_pairs": payload["total_distinct_pairs"],
        "duplicate_pair_count": payload["duplicate_pair_count"],
        "max_evidence_per_pair": payload["max_evidence_per_pair"],
        "db_writes": payload["db_writes"],
    }, ensure_ascii=False, sort_keys=True))
    if blocking_reasons:
        raise RuntimeError({"project_member_neutral_pair_consolidation_profile_blocked": blocking_reasons})


main()
