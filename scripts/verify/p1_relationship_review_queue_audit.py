# -*- coding: utf-8 -*-
"""Audit the readonly P1 relationship manual review queue."""

import json


EXPECTED_MODELS = {
    "sc.expense.claim",
    "sc.payment.execution",
    "sc.receipt.income",
    "sc.financing.loan",
    "sc.settlement.order",
    "sc.business.entity",
    "project.cost.ledger",
}
ALLOWED_RECOMMENDATIONS = {
    "hybrid_candidate",
    "manual_review_candidate",
    "insufficient_evidence",
}


def _read_group(groupby):
    rows = env["sc.p1.relationship.review.queue"].sudo().read_group([], ["candidate_record_count:sum"], groupby, lazy=False)  # noqa: F821
    return {
        "|".join(str(row.get(name) or "") for name in groupby): int(row.get("candidate_record_count") or 0)
        for row in rows
    }


def main():
    Queue = env["sc.p1.relationship.review.queue"].sudo()  # noqa: F821
    errors = []
    total_rows = Queue.search_count([])
    env.cr.execute("SELECT COALESCE(SUM(candidate_record_count), 0)::integer FROM sc_p1_relationship_review_queue")  # noqa: F821
    total_records = int(env.cr.fetchone()[0] or 0)  # noqa: F821
    if total_rows <= 0 or total_records <= 0:
        errors.append("relationship review queue is empty")

    source_record_counts = _read_group(["source_model"])
    missing_sources = sorted(EXPECTED_MODELS - set(source_record_counts))
    if missing_sources:
        errors.append("missing expected review source models: %s" % ", ".join(missing_sources))

    recommendation_counts = _read_group(["recommendation"])
    unexpected_recommendations = sorted(set(recommendation_counts) - ALLOWED_RECOMMENDATIONS)
    if unexpected_recommendations:
        errors.append("unexpected review recommendations: %s" % ", ".join(unexpected_recommendations))

    auto_like_count = Queue.search_count([("recommendation", "=", "auto_candidate")])
    if auto_like_count:
        errors.append("review queue must not expose auto_candidate rows: %s" % auto_like_count)

    blank_value_count = Queue.search_count([("candidate_value", "=", False)])
    if blank_value_count:
        errors.append("review queue has blank candidate values: %s" % blank_value_count)

    readonly_error = None
    try:
        Queue.create({"source_model": "probe"})
    except Exception as exc:  # expected
        readonly_error = type(exc).__name__
    if readonly_error != "UserError":
        errors.append("create should be blocked by UserError, got %s" % readonly_error)

    payload = {
        "scope": "p1_relationship_review_queue_audit",
        "database": env.cr.dbname,  # noqa: F821
        "status": "PASS" if not errors else "FAIL",
        "total_rows": total_rows,
        "total_candidate_records": total_records,
        "source_record_counts": source_record_counts,
        "recommendation_counts": recommendation_counts,
        "auto_like_count": auto_like_count,
        "blank_value_count": blank_value_count,
        "readonly_create_error": readonly_error,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    if errors:
        raise SystemExit(1)


main()
