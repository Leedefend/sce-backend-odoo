# -*- coding: utf-8 -*-
"""Probe read-only mapping candidates around locked P1 business facts.

Run with:
docker compose exec -T odoo odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < scripts/verify/p1_locked_fact_mapping_candidate_probe.py
"""

import json


SPECS = [
    {
        "family": "付款与费用",
        "model": "sc.expense.claim",
        "target": "partner_id",
        "candidate_fields": [
            "payee",
            "receipt_account_name",
            "legacy_visible_supplier_name",
            "legacy_visible_borrower",
            "legacy_visible_project_name",
        ],
        "match_kind": "partner",
    },
    {
        "family": "付款与费用",
        "model": "sc.expense.claim",
        "target": "payment_request_id",
        "candidate_fields": ["legacy_visible_document_no", "legacy_document_no", "name"],
        "match_kind": "payment_request",
    },
    {
        "family": "付款与费用",
        "model": "sc.payment.execution",
        "target": "partner_id",
        "candidate_fields": [
            "legacy_visible_supplier_name",
            "legacy_visible_actual_payee_unit",
            "receipt_account_name",
        ],
        "match_kind": "partner",
    },
    {
        "family": "付款与费用",
        "model": "sc.payment.execution",
        "target": "contract_id",
        "candidate_fields": ["legacy_visible_payment_source", "legacy_visible_request_no", "document_no"],
        "match_kind": "contract",
    },
    {
        "family": "付款与费用",
        "model": "sc.payment.execution",
        "target": "payment_request_id",
        "candidate_fields": ["legacy_visible_request_no", "legacy_visible_document_no", "document_no"],
        "match_kind": "payment_request",
    },
    {
        "family": "付款与费用",
        "model": "payment.request",
        "target": "contract_id",
        "candidate_fields": ["contract_no", "legacy_contract_no", "legacy_visible_contract_no", "name"],
        "match_kind": "contract",
    },
    {
        "family": "税务与发票",
        "model": "sc.invoice.registration",
        "target": "partner_id",
        "candidate_fields": [
            "legacy_partner_name",
            "legacy_visible_partner_name",
            "recipient_unit_name",
            "invoice_issue_company",
            "actual_invoice_issue_company",
            "invoice_provider_name",
        ],
        "match_kind": "partner",
    },
    {
        "family": "税务与发票",
        "model": "sc.invoice.registration",
        "target": "contract_id",
        "candidate_fields": ["legacy_visible_contract_no", "document_no"],
        "match_kind": "contract",
    },
    {
        "family": "税务与发票",
        "model": "sc.tax.deduction.registration",
        "target": "partner_id",
        "candidate_fields": ["partner_name", "deduction_unit_name"],
        "match_kind": "partner",
    },
    {
        "family": "收入与收款",
        "model": "sc.receipt.income",
        "target": "partner_id",
        "candidate_fields": [
            "legacy_partner_name",
            "receiving_account_name",
            "legacy_company_name",
        ],
        "match_kind": "partner",
    },
    {
        "family": "收入与收款",
        "model": "sc.receipt.income",
        "target": "contract_id",
        "candidate_fields": ["legacy_contract_no", "document_no"],
        "match_kind": "contract",
    },
    {
        "family": "收入与收款",
        "model": "sc.receipt.invoice.line",
        "target": "contract_id",
        "candidate_fields": ["source_contract_no", "document_no", "source_document_no"],
        "match_kind": "contract",
    },
    {
        "family": "账户与往来资金",
        "model": "sc.fund.account.operation",
        "target": "source_account_id",
        "candidate_fields": [
            "legacy_visible_account_name",
            "payment_account_name",
            "payer_account",
            "payment_account_no",
        ],
        "match_kind": "fund_account",
    },
    {
        "family": "账户与往来资金",
        "model": "sc.fund.account.operation",
        "target": "target_account_id",
        "candidate_fields": [
            "legacy_visible_counterparty_account_name",
            "receipt_account_name",
            "payee_account",
            "receipt_account_no",
        ],
        "match_kind": "fund_account",
    },
    {
        "family": "账户与往来资金",
        "model": "sc.financing.loan",
        "target": "partner_id",
        "candidate_fields": [
            "legacy_counterparty_name",
            "legacy_visible_counterparty_name",
            "legacy_visible_payee",
            "legacy_visible_payer_unit",
            "legacy_visible_receiver_unit",
        ],
        "match_kind": "partner",
    },
    {
        "family": "合同与结算",
        "model": "sc.settlement.order",
        "target": "partner_id",
        "candidate_fields": ["legacy_counterparty_name", "settlement_unit_name"],
        "match_kind": "partner",
    },
    {
        "family": "合同与结算",
        "model": "sc.settlement.order",
        "target": "contract_id",
        "candidate_fields": ["legacy_contract_no", "document_no"],
        "match_kind": "contract",
    },
    {
        "family": "项目与主数据",
        "model": "sc.business.entity",
        "target": "partner_id",
        "candidate_fields": ["name", "legacy_xmmc", "legacy_company_name"],
        "match_kind": "partner",
    },
    {
        "family": "项目与主数据",
        "model": "project.project",
        "target": "partner_id",
        "candidate_fields": ["partner_name", "customer_name", "owner_name", "legacy_partner_name"],
        "match_kind": "partner",
    },
    {
        "family": "预算成本管控",
        "model": "project.cost.ledger",
        "target": "partner_id",
        "candidate_fields": ["partner_name", "legacy_partner_name", "note"],
        "match_kind": "partner",
    },
]


def _quote(name):
    return '"' + name.replace('"', '""') + '"'


def _table(model_name):
    return env[model_name].sudo()._table


def _field_exists(model_name, field_name):
    if model_name not in env:
        return False
    field = env[model_name].sudo()._fields.get(field_name)
    return bool(field and getattr(field, "store", True))


def _count_sql(sql, params=None):
    try:
        env.cr.execute(sql, params or [])
        row = env.cr.fetchone()
        return int(row[0] or 0)
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:220])}


def _where_missing(target):
    return "%s IS NULL" % _quote(target)


def _where_nonempty(field):
    return "NULLIF(BTRIM(COALESCE(%s::text, '')), '') IS NOT NULL" % _quote(field)


def _target_values_sql(kind):
    if kind == "partner":
        return (
            "SELECT LOWER(BTRIM(name::text)) AS norm, NULL::integer AS project_id "
            "FROM res_partner WHERE active IS TRUE AND NULLIF(BTRIM(name::text), '') IS NOT NULL "
            "UNION "
            "SELECT LOWER(BTRIM(legacy_partner_name::text)) AS norm, NULL::integer AS project_id "
            "FROM sc_legacy_partner_map "
            "WHERE active IS TRUE AND partner_id IS NOT NULL AND mapping_state = 'confirmed' "
            "AND NULLIF(BTRIM(legacy_partner_name::text), '') IS NOT NULL"
        )
    if kind == "contract":
        return (
            "SELECT LOWER(BTRIM(name::text)) AS norm, project_id "
            "FROM construction_contract WHERE active IS TRUE AND NULLIF(BTRIM(name::text), '') IS NOT NULL "
            "UNION "
            "SELECT LOWER(BTRIM(legacy_contract_no::text)) AS norm, project_id "
            "FROM construction_contract WHERE active IS TRUE AND NULLIF(BTRIM(COALESCE(legacy_contract_no, '')::text), '') IS NOT NULL "
            "UNION "
            "SELECT LOWER(BTRIM(legacy_external_contract_no::text)) AS norm, project_id "
            "FROM construction_contract WHERE active IS TRUE AND NULLIF(BTRIM(COALESCE(legacy_external_contract_no, '')::text), '') IS NOT NULL"
        )
    if kind == "payment_request":
        return (
            "SELECT LOWER(BTRIM(name::text)) AS norm, project_id "
            "FROM payment_request WHERE active IS TRUE AND NULLIF(BTRIM(name::text), '') IS NOT NULL "
            "UNION "
            "SELECT LOWER(BTRIM(legacy_visible_document_no::text)) AS norm, project_id "
            "FROM payment_request WHERE active IS TRUE AND NULLIF(BTRIM(COALESCE(legacy_visible_document_no, '')::text), '') IS NOT NULL"
        )
    if kind == "fund_account":
        return (
            "SELECT LOWER(BTRIM(name::text)) AS norm, project_id "
            "FROM sc_fund_account WHERE active IS TRUE AND NULLIF(BTRIM(name::text), '') IS NOT NULL "
            "UNION "
            "SELECT LOWER(BTRIM(account_no::text)) AS norm, project_id "
            "FROM sc_fund_account WHERE active IS TRUE AND NULLIF(BTRIM(COALESCE(account_no, '')::text), '') IS NOT NULL "
            "UNION "
            "SELECT LOWER(BTRIM(display_name::text)) AS norm, project_id "
            "FROM sc_fund_account WHERE active IS TRUE AND NULLIF(BTRIM(COALESCE(display_name, '')::text), '') IS NOT NULL"
        )
    return "SELECT NULL::text AS norm, NULL::integer AS project_id WHERE FALSE"


def _probe_field(model_name, target, candidate_field, match_kind):
    table = _table(model_name)
    base_where = _where_missing(target)
    candidate_where = _where_nonempty(candidate_field)
    candidate_count = _count_sql(
        "SELECT COUNT(*) FROM %s src WHERE %s AND %s"
        % (_quote(table), base_where, candidate_where)
    )
    project_expr = "project_id" if _field_exists(model_name, "project_id") else "NULL::integer"
    match_count = _count_sql(
        """
        WITH candidate AS (
            SELECT
                LOWER(BTRIM(%(field)s::text)) AS norm,
                %(project_expr)s AS project_id,
                COUNT(*)::integer AS cnt
            FROM %(table)s src
            WHERE %(base_where)s AND %(candidate_where)s
            GROUP BY LOWER(BTRIM(%(field)s::text)), %(project_expr)s
        ),
        target AS (
            %(target_values)s
        )
        SELECT COALESCE(SUM(candidate.cnt), 0)::integer
        FROM candidate
        WHERE EXISTS (
            SELECT 1
            FROM target
            WHERE target.norm = candidate.norm
              AND (
                    candidate.project_id IS NULL
                 OR target.project_id IS NULL
                 OR target.project_id = candidate.project_id
              )
        )
        """
        % {
            "field": _quote(candidate_field),
            "project_expr": project_expr,
            "table": _quote(table),
            "base_where": base_where,
            "candidate_where": candidate_where,
            "target_values": _target_values_sql(match_kind),
        }
    )
    sample_sql = (
        "SELECT DISTINCT BTRIM(%s::text) AS value FROM %s src "
        "WHERE %s AND %s ORDER BY value LIMIT 8"
        % (_quote(candidate_field), _quote(table), base_where, candidate_where)
    )
    samples = []
    try:
        env.cr.execute(sample_sql)
        samples = [row[0] for row in env.cr.fetchall() if row and row[0]]
    except Exception as exc:
        samples = [{"error": "%s: %s" % (type(exc).__name__, str(exc)[:160])}]
    return {
        "field": candidate_field,
        "candidate_count": candidate_count,
        "match_count": match_count,
        "samples": samples,
    }


def _coverage(numerator, denominator):
    if not isinstance(numerator, int) or not isinstance(denominator, int) or denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def _classify(best_match_count, missing_count):
    ratio = _coverage(best_match_count, missing_count)
    if ratio is None:
        return "unknown"
    if ratio >= 0.8:
        return "auto_candidate"
    if ratio >= 0.3:
        return "hybrid_candidate"
    if best_match_count > 0:
        return "manual_review_candidate"
    return "insufficient_evidence"


def main():
    probes = []
    for spec in SPECS:
        model_name = spec["model"]
        target = spec["target"]
        if model_name not in env or not _field_exists(model_name, target):
            probes.append({**spec, "installed": False, "error": "model_or_target_missing"})
            continue
        table = _table(model_name)
        missing_count = _count_sql(
            "SELECT COUNT(*) FROM %s src WHERE %s" % (_quote(table), _where_missing(target))
        )
        fields = []
        for candidate_field in spec.get("candidate_fields", []):
            if not _field_exists(model_name, candidate_field):
                continue
            fields.append(_probe_field(model_name, target, candidate_field, spec["match_kind"]))
        best_candidate_count = max(
            [item["candidate_count"] for item in fields if isinstance(item.get("candidate_count"), int)] or [0]
        )
        best_match_count = max(
            [item["match_count"] for item in fields if isinstance(item.get("match_count"), int)] or [0]
        )
        probes.append(
            {
                **spec,
                "installed": True,
                "missing_count": missing_count,
                "best_candidate_count": best_candidate_count,
                "best_match_count": best_match_count,
                "candidate_coverage": _coverage(best_candidate_count, missing_count),
                "match_coverage": _coverage(best_match_count, missing_count),
                "recommendation": _classify(best_match_count, missing_count),
                "fields": fields,
            }
        )

    summary = {
        "probe_count": len(probes),
        "auto_candidate_count": len([p for p in probes if p.get("recommendation") == "auto_candidate"]),
        "hybrid_candidate_count": len([p for p in probes if p.get("recommendation") == "hybrid_candidate"]),
        "manual_review_candidate_count": len(
            [p for p in probes if p.get("recommendation") == "manual_review_candidate"]
        ),
        "insufficient_evidence_count": len([p for p in probes if p.get("recommendation") == "insufficient_evidence"]),
    }
    result = {
        "ok": True,
        "database": env.cr.dbname,
        "scope": "p1_locked_fact_mapping_candidate_probe",
        "write_policy": "read_only_probe_locked_user_fact_data_must_not_be_updated",
        "summary": summary,
        "probes": probes,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str))


main()
