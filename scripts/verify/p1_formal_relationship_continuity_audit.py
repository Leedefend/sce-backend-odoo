# -*- coding: utf-8 -*-
"""Audit P1 formal document relationship continuity.

Run inside ``odoo shell``.  This audit is read-only: it does not require every
locked historical fact to have formal anchors, but once a formal relation is
present it must not cross project, contract, settlement or counterparty scope.
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("P1_RELATIONSHIP_AUDIT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/p1_relationship/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def fetch_rows(sql: str, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def count_rows(sql: str, params=None) -> int:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return int(row[0] or 0) if row else 0


CHECKS = OrderedDict(
    [
        (
            "settlement_contract_scope",
            {
                "description": "结算单绑定合同时，项目和往来单位不能与合同相冲突。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM sc_settlement_order AS s
                      JOIN construction_contract AS c ON c.id = s.contract_id
                     WHERE (s.project_id IS NOT NULL AND c.project_id IS NOT NULL AND s.project_id <> c.project_id)
                        OR (s.partner_id IS NOT NULL AND c.partner_id IS NOT NULL AND s.partner_id <> c.partner_id)
                """,
                "sample_sql": """
                    SELECT s.id, s.name, s.project_id, c.project_id AS contract_project_id,
                           s.partner_id, c.partner_id AS contract_partner_id, s.contract_id
                      FROM sc_settlement_order AS s
                      JOIN construction_contract AS c ON c.id = s.contract_id
                     WHERE (s.project_id IS NOT NULL AND c.project_id IS NOT NULL AND s.project_id <> c.project_id)
                        OR (s.partner_id IS NOT NULL AND c.partner_id IS NOT NULL AND s.partner_id <> c.partner_id)
                     ORDER BY s.id
                     LIMIT 20
                """,
            },
        ),
        (
            "payment_request_settlement_scope",
            {
                "description": "付款/收款申请绑定结算单时，项目、合同和往来单位不能与结算单相冲突。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM payment_request AS r
                      JOIN sc_settlement_order AS s ON s.id = r.settlement_id
                     WHERE (r.project_id IS NOT NULL AND s.project_id IS NOT NULL AND r.project_id <> s.project_id)
                        OR (r.contract_id IS NOT NULL AND s.contract_id IS NOT NULL AND r.contract_id <> s.contract_id)
                        OR (
                            r.partner_id IS NOT NULL
                            AND COALESCE(s.settlement_unit_id, s.partner_id) IS NOT NULL
                            AND r.partner_id <> COALESCE(s.settlement_unit_id, s.partner_id)
                        )
                """,
                "sample_sql": """
                    SELECT r.id, r.name, r.type, r.project_id, s.project_id AS settlement_project_id,
                           r.contract_id, s.contract_id AS settlement_contract_id,
                           r.partner_id, s.partner_id AS settlement_partner_id,
                           s.settlement_unit_id, COALESCE(s.settlement_unit_id, s.partner_id) AS settlement_effective_partner_id,
                           r.settlement_id
                      FROM payment_request AS r
                      JOIN sc_settlement_order AS s ON s.id = r.settlement_id
                     WHERE (r.project_id IS NOT NULL AND s.project_id IS NOT NULL AND r.project_id <> s.project_id)
                        OR (r.contract_id IS NOT NULL AND s.contract_id IS NOT NULL AND r.contract_id <> s.contract_id)
                        OR (
                            r.partner_id IS NOT NULL
                            AND COALESCE(s.settlement_unit_id, s.partner_id) IS NOT NULL
                            AND r.partner_id <> COALESCE(s.settlement_unit_id, s.partner_id)
                        )
                     ORDER BY r.id
                     LIMIT 20
                """,
            },
        ),
        (
            "payment_execution_request_scope",
            {
                "description": "付款登记绑定付款申请时，申请类型和项目不能相冲突；申请往来单位与实际收款单位允许以正式字段分别承载。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM sc_payment_execution AS e
                      JOIN payment_request AS r ON r.id = e.payment_request_id
                     WHERE NOT (COALESCE(e.source_origin, '') = 'legacy' AND e.state = 'legacy_confirmed')
                       AND (
                            (r.type IS NOT NULL AND r.type <> 'pay')
                            OR (e.project_id IS NOT NULL AND r.project_id IS NOT NULL AND e.project_id <> r.project_id)
                       )
                """,
                "sample_sql": """
                    SELECT e.id, e.name, e.project_id, r.project_id AS request_project_id,
                           e.contract_id, r.contract_id AS request_contract_id,
                           e.partner_id, r.partner_id AS request_partner_id,
                           e.payment_request_id, r.type AS request_type
                      FROM sc_payment_execution AS e
                      JOIN payment_request AS r ON r.id = e.payment_request_id
                     WHERE NOT (COALESCE(e.source_origin, '') = 'legacy' AND e.state = 'legacy_confirmed')
                       AND (
                            (r.type IS NOT NULL AND r.type <> 'pay')
                            OR (e.project_id IS NOT NULL AND r.project_id IS NOT NULL AND e.project_id <> r.project_id)
                       )
                     ORDER BY e.id
                     LIMIT 20
                """,
                "risk_count_sql": """
                    SELECT COUNT(*)
                     FROM sc_payment_execution AS e
                     JOIN payment_request AS r ON r.id = e.payment_request_id
                     WHERE (
                            e.project_id IS NULL
                            OR r.project_id IS NULL
                            OR e.project_id = r.project_id
                            OR (COALESCE(e.source_origin, '') = 'legacy' AND e.state = 'legacy_confirmed')
                       )
                       AND (
                            (e.project_id IS NOT NULL AND r.project_id IS NOT NULL AND e.project_id <> r.project_id)
                            OR
                            (e.contract_id IS NOT NULL AND r.contract_id IS NOT NULL AND e.contract_id <> r.contract_id)
                            OR (e.contract_id IS NULL AND r.contract_id IS NOT NULL)
                       )
                """,
                "risk_sample_sql": """
                    SELECT e.id, e.name, e.project_id, r.project_id AS request_project_id,
                           e.contract_id, r.contract_id AS request_contract_id,
                           e.partner_id, r.partner_id AS request_partner_id,
                           e.payment_request_id, r.type AS request_type
                      FROM sc_payment_execution AS e
                      JOIN payment_request AS r ON r.id = e.payment_request_id
                     WHERE (
                            e.project_id IS NULL
                            OR r.project_id IS NULL
                            OR e.project_id = r.project_id
                            OR (COALESCE(e.source_origin, '') = 'legacy' AND e.state = 'legacy_confirmed')
                       )
                       AND (
                            (e.project_id IS NOT NULL AND r.project_id IS NOT NULL AND e.project_id <> r.project_id)
                            OR
                            (e.contract_id IS NOT NULL AND r.contract_id IS NOT NULL AND e.contract_id <> r.contract_id)
                            OR (e.contract_id IS NULL AND r.contract_id IS NOT NULL)
                       )
                     ORDER BY e.id
                     LIMIT 20
                """,
                "accepted_count_sql": """
                    SELECT COUNT(*)
                     FROM sc_payment_execution AS e
                     JOIN payment_request AS r ON r.id = e.payment_request_id
                     WHERE COALESCE(e.source_origin, '') = 'legacy'
                       AND e.state = 'legacy_confirmed'
                       AND e.project_id IS NOT NULL
                       AND r.project_id IS NOT NULL
                       AND e.project_id = r.project_id
                       AND (
                            r.contract_id IS NULL
                            OR (e.contract_id IS NOT NULL AND e.contract_id = r.contract_id)
                       )
                       AND e.partner_id IS NOT NULL
                       AND r.partner_id IS NOT NULL
                       AND e.partner_id <> r.partner_id
                """,
                "accepted_sample_sql": """
                    SELECT e.id, e.name, e.project_id, r.project_id AS request_project_id,
                           e.contract_id, r.contract_id AS request_contract_id,
                           e.partner_id AS actual_payee_partner_id, r.partner_id AS request_partner_id,
                           e.payment_request_id, r.type AS request_type
                      FROM sc_payment_execution AS e
                      JOIN payment_request AS r ON r.id = e.payment_request_id
                     WHERE COALESCE(e.source_origin, '') = 'legacy'
                       AND e.state = 'legacy_confirmed'
                       AND e.project_id IS NOT NULL
                       AND r.project_id IS NOT NULL
                       AND e.project_id = r.project_id
                       AND (
                            r.contract_id IS NULL
                            OR (e.contract_id IS NOT NULL AND e.contract_id = r.contract_id)
                       )
                       AND e.partner_id IS NOT NULL
                       AND r.partner_id IS NOT NULL
                       AND e.partner_id <> r.partner_id
                     ORDER BY e.id
                     LIMIT 20
                """,
            },
        ),
        (
            "receipt_income_request_scope",
            {
                "description": "收款登记绑定收款申请时，项目、合同和往来单位不能与申请相冲突。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM sc_receipt_income AS i
                      JOIN payment_request AS r ON r.id = i.payment_request_id
                     WHERE (r.type IS NOT NULL AND r.type <> 'receive')
                        OR (i.project_id IS NOT NULL AND r.project_id IS NOT NULL AND i.project_id <> r.project_id)
                        OR (i.contract_id IS NOT NULL AND r.contract_id IS NOT NULL AND i.contract_id <> r.contract_id)
                        OR (i.partner_id IS NOT NULL AND r.partner_id IS NOT NULL AND i.partner_id <> r.partner_id)
                """,
                "sample_sql": """
                    SELECT i.id, i.name, i.project_id, r.project_id AS request_project_id,
                           i.contract_id, r.contract_id AS request_contract_id,
                           i.partner_id, r.partner_id AS request_partner_id,
                           i.payment_request_id, r.type AS request_type
                      FROM sc_receipt_income AS i
                      JOIN payment_request AS r ON r.id = i.payment_request_id
                     WHERE (r.type IS NOT NULL AND r.type <> 'receive')
                        OR (i.project_id IS NOT NULL AND r.project_id IS NOT NULL AND i.project_id <> r.project_id)
                        OR (i.contract_id IS NOT NULL AND r.contract_id IS NOT NULL AND i.contract_id <> r.contract_id)
                        OR (i.partner_id IS NOT NULL AND r.partner_id IS NOT NULL AND i.partner_id <> r.partner_id)
                     ORDER BY i.id
                     LIMIT 20
                """,
            },
        ),
        (
            "expense_claim_request_scope",
            {
                "description": "费用/保证金绑定付款/收款申请时，申请类型和项目不能相冲突。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM sc_expense_claim AS c
                      JOIN payment_request AS r ON r.id = c.payment_request_id
                     WHERE NOT (COALESCE(c.source_origin, '') = 'legacy' AND c.state = 'legacy_confirmed')
                       AND (
                            (c.direction = 'inflow' AND r.type <> 'receive')
                            OR (c.direction = 'outflow' AND r.type <> 'pay')
                            OR (c.project_id IS NOT NULL AND r.project_id IS NOT NULL AND c.project_id <> r.project_id)
                       )
                """,
                "sample_sql": """
                    SELECT c.id, c.name, c.claim_type, c.direction, c.project_id,
                           r.project_id AS request_project_id, c.payment_request_id, r.type AS request_type
                      FROM sc_expense_claim AS c
                      JOIN payment_request AS r ON r.id = c.payment_request_id
                     WHERE NOT (COALESCE(c.source_origin, '') = 'legacy' AND c.state = 'legacy_confirmed')
                       AND (
                            (c.direction = 'inflow' AND r.type <> 'receive')
                            OR (c.direction = 'outflow' AND r.type <> 'pay')
                            OR (c.project_id IS NOT NULL AND r.project_id IS NOT NULL AND c.project_id <> r.project_id)
                       )
                     ORDER BY c.id
                     LIMIT 20
                """,
                "risk_count_sql": """
                    SELECT COUNT(*)
                      FROM sc_expense_claim AS c
                      JOIN payment_request AS r ON r.id = c.payment_request_id
                     WHERE COALESCE(c.source_origin, '') = 'legacy'
                       AND c.state = 'legacy_confirmed'
                       AND (
                            (c.direction = 'inflow' AND r.type <> 'receive')
                            OR (c.direction = 'outflow' AND r.type <> 'pay')
                            OR (c.project_id IS NOT NULL AND r.project_id IS NOT NULL AND c.project_id <> r.project_id)
                       )
                """,
                "risk_sample_sql": """
                    SELECT c.id, c.name, c.claim_type, c.direction, c.project_id,
                           r.project_id AS request_project_id, c.payment_request_id, r.type AS request_type
                      FROM sc_expense_claim AS c
                      JOIN payment_request AS r ON r.id = c.payment_request_id
                     WHERE COALESCE(c.source_origin, '') = 'legacy'
                       AND c.state = 'legacy_confirmed'
                       AND (
                            (c.direction = 'inflow' AND r.type <> 'receive')
                            OR (c.direction = 'outflow' AND r.type <> 'pay')
                            OR (c.project_id IS NOT NULL AND r.project_id IS NOT NULL AND c.project_id <> r.project_id)
                       )
                     ORDER BY c.id
                     LIMIT 20
                """,
            },
        ),
        (
            "invoice_settlement_scope",
            {
                "description": "发票登记绑定结算单时，项目、合同和往来单位不能与结算单相冲突。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM sc_invoice_registration AS i
                      JOIN sc_settlement_order AS s ON s.id = i.settlement_id
                     WHERE (i.project_id IS NOT NULL AND s.project_id IS NOT NULL AND i.project_id <> s.project_id)
                        OR (i.contract_id IS NOT NULL AND s.contract_id IS NOT NULL AND i.contract_id <> s.contract_id)
                        OR (i.partner_id IS NOT NULL AND s.partner_id IS NOT NULL AND i.partner_id <> s.partner_id)
                """,
                "sample_sql": """
                    SELECT i.id, i.name, i.project_id, s.project_id AS settlement_project_id,
                           i.contract_id, s.contract_id AS settlement_contract_id,
                           i.partner_id, s.partner_id AS settlement_partner_id, i.settlement_id
                      FROM sc_invoice_registration AS i
                      JOIN sc_settlement_order AS s ON s.id = i.settlement_id
                     WHERE (i.project_id IS NOT NULL AND s.project_id IS NOT NULL AND i.project_id <> s.project_id)
                        OR (i.contract_id IS NOT NULL AND s.contract_id IS NOT NULL AND i.contract_id <> s.contract_id)
                        OR (i.partner_id IS NOT NULL AND s.partner_id IS NOT NULL AND i.partner_id <> s.partner_id)
                     ORDER BY i.id
                     LIMIT 20
                """,
            },
        ),
        (
            "invoice_contract_scope",
            {
                "description": "发票登记绑定合同时，项目和往来单位不能与合同相冲突。",
                "count_sql": """
                    SELECT COUNT(*)
                      FROM sc_invoice_registration AS i
                      JOIN construction_contract AS c ON c.id = i.contract_id
                     WHERE (i.project_id IS NOT NULL AND c.project_id IS NOT NULL AND i.project_id <> c.project_id)
                        OR (i.partner_id IS NOT NULL AND c.partner_id IS NOT NULL AND i.partner_id <> c.partner_id)
                """,
                "sample_sql": """
                    SELECT i.id, i.name, i.project_id, c.project_id AS contract_project_id,
                           i.partner_id, c.partner_id AS contract_partner_id, i.contract_id
                      FROM sc_invoice_registration AS i
                      JOIN construction_contract AS c ON c.id = i.contract_id
                     WHERE (i.project_id IS NOT NULL AND c.project_id IS NOT NULL AND i.project_id <> c.project_id)
                        OR (i.partner_id IS NOT NULL AND c.partner_id IS NOT NULL AND i.partner_id <> c.partner_id)
                     ORDER BY i.id
                     LIMIT 20
                """,
            },
        ),
    ]
)


rows = []
errors = []
risks = []
accepted_differences = []
for key, spec in CHECKS.items():
    mismatch_count = count_rows(spec["count_sql"])
    row = OrderedDict(
        [
            ("key", key),
            ("description", spec["description"]),
            ("mismatch_count", mismatch_count),
        ]
    )
    if mismatch_count:
        row["sample"] = fetch_rows(spec["sample_sql"])
        errors.append(row)
    if spec.get("risk_count_sql"):
        risk_count = count_rows(spec["risk_count_sql"])
        row["risk_count"] = risk_count
        if risk_count:
            risk_row = OrderedDict(
                [
                    ("key", key),
                    ("description", "存在可解释关系差异，需要后续按业务口径细化：合同缺失/不同或实际收款方不同。"),
                    ("risk_count", risk_count),
                    ("sample", fetch_rows(spec["risk_sample_sql"])),
                ]
            )
            risks.append(risk_row)
    if spec.get("accepted_count_sql"):
        accepted_count = count_rows(spec["accepted_count_sql"])
        row["accepted_difference_count"] = accepted_count
        if accepted_count:
            accepted_differences.append(
                OrderedDict(
                    [
                        ("key", key),
                        (
                            "description",
                            "历史付款执行的实际收款单位与付款申请往来单位不同，已由正式字段 payment_request_partner_id / actual_payee_partner_id 分别承载。",
                        ),
                        ("accepted_difference_count", accepted_count),
                        ("sample", fetch_rows(spec["accepted_sample_sql"])),
                    ]
                )
            )
    rows.append(row)

payload = OrderedDict(
    [
        ("status", "PASS" if not errors else "FAIL"),
        ("database", env.cr.dbname),  # noqa: F821
        ("scope", "P1 formal relationship continuity"),
        (
            "policy",
            "locked historical facts may lack anchors, but any formal anchor that exists must stay within one project/contract/counterparty scope",
        ),
        ("checks", rows),
        ("errors", errors),
        ("risks", risks),
        ("accepted_differences", accepted_differences),
    ]
)

artifact = artifact_root() / f"p1_formal_relationship_continuity_audit_{env.cr.dbname}.json"  # noqa: F821
artifact.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({"status": payload["status"], "error_count": len(errors), "artifact": str(artifact)}, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
