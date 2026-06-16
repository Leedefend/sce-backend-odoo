# -*- coding: utf-8 -*-
"""Audit the readonly P1 relationship suggestion projection."""

import json

from odoo.exceptions import UserError  # noqa: F401


ALLOWED_SOURCE_MODELS = {
    "sc.receipt.income",
    "sc.invoice.registration",
    "sc.tax.deduction.registration",
}
ALLOWED_TARGETS = {("res.partner", "partner_id")}


def _count(domain):
    return env["sc.p1.relationship.suggestion"].sudo().search_count(domain)  # noqa: F821


def _read_group(groupby):
    rows = env["sc.p1.relationship.suggestion"].sudo().read_group([], ["__count"], groupby, lazy=False)  # noqa: F821
    return {
        "|".join(str(row.get(name) or "") for name in groupby): int(row.get("__count") or 0)
        for row in rows
    }


def main():
    Suggestion = env["sc.p1.relationship.suggestion"].sudo()  # noqa: F821
    errors = []
    total = Suggestion.search_count([])
    if total <= 0:
        errors.append("relationship suggestion projection is empty")

    source_model_counts = _read_group(["source_model"])
    unexpected_sources = sorted(set(source_model_counts) - ALLOWED_SOURCE_MODELS)
    if unexpected_sources:
        errors.append("unexpected source models: %s" % ", ".join(unexpected_sources))

    target_rows = Suggestion.read_group([], ["__count"], ["target_model", "target_field"], lazy=False)
    unexpected_targets = sorted(
        {
            (row.get("target_model"), row.get("target_field"))
            for row in target_rows
            if (row.get("target_model"), row.get("target_field")) not in ALLOWED_TARGETS
        }
    )
    if unexpected_targets:
        errors.append("unexpected targets: %s" % unexpected_targets)

    null_partner_count = _count([("partner_id", "=", False)])
    if null_partner_count:
        errors.append("suggestions without partner_id: %s" % null_partner_count)

    weak_confidence_count = _count([("confidence_score", "<", 0.85)])
    if weak_confidence_count:
        errors.append("suggestions below confidence floor: %s" % weak_confidence_count)

    readonly_error = None
    try:
        Suggestion.create({"source_model": "probe"})
    except Exception as exc:  # expected
        readonly_error = type(exc).__name__
    if readonly_error != "UserError":
        errors.append("create should be blocked by UserError, got %s" % readonly_error)

    payload = {
        "scope": "p1_relationship_suggestion_audit",
        "database": env.cr.dbname,  # noqa: F821
        "status": "PASS" if not errors else "FAIL",
        "total": total,
        "source_model_counts": source_model_counts,
        "recommendation_counts": _read_group(["recommendation"]),
        "candidate_field_counts": _read_group(["source_model", "candidate_field"]),
        "null_partner_count": null_partner_count,
        "weak_confidence_count": weak_confidence_count,
        "readonly_create_error": readonly_error,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    if errors:
        raise SystemExit(1)


main()
