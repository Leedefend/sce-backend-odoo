# -*- coding: utf-8 -*-
"""Verify P0 finance handling models default new business documents to CNY."""

from __future__ import annotations

import json
import sys
import traceback
from collections import OrderedDict


MODELS = [
    "payment.request",
    "sc.payment.execution",
    "sc.receipt.income",
    "sc.expense.claim",
    "sc.financing.loan",
    "sc.self.funding.registration",
    "sc.fund.account",
    "sc.fund.account.operation",
    "sc.invoice.registration",
    "sc.tax.deduction.registration",
]


def main():
    cny = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
    if not cny:
        raise AssertionError("base.CNY is missing")

    rows = []
    failures = []
    for model_name in MODELS:
        Model = env[model_name].sudo()  # noqa: F821
        defaults = Model.default_get(["currency_id"])
        currency_id = defaults.get("currency_id")
        currency = env["res.currency"].sudo().browse(currency_id).exists() if currency_id else False  # noqa: F821
        row = OrderedDict(
            [
                ("model", model_name),
                ("currency_id", currency.id if currency else False),
                ("currency_name", currency.name if currency else False),
            ]
        )
        rows.append(row)
        if currency != cny:
            failures.append(dict(row))

    result = OrderedDict(
        [
            ("status", "PASS" if not failures else "FAIL"),
            ("database", env.cr.dbname),  # noqa: F821
            ("expected_currency_id", cny.id),
            ("expected_currency_name", cny.name),
            ("rows", rows),
            ("failures", failures),
        ]
    )
    print("FINANCE_P0_CURRENCY_DEFAULT_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    env.cr.rollback()  # noqa: F821
    print(
        "FINANCE_P0_CURRENCY_DEFAULT_AUDIT: %s"
        % json.dumps(
            {
                "status": "FAIL",
                "error": str(err),
                "traceback": traceback.format_exc(),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
    )
    sys.exit(1)
