"""Configure deterministic non-production sender facts for sc_demo.

Run through Odoo shell:
odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/ops/dev_mail_sender_config_sync.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-17-DEV-MAIL-SENDER-CONFIG-SYNC"
TARGET_DB = "sc_demo"
DEFAULT_FROM = "noreply@smartconstruction.local"
FINANCE_LOGIN = "sc_fx_finance"
FINANCE_EMAIL = "sc_fx_finance@smartconstruction.local"

OUTPUT_JSON = Path("/mnt/artifacts/ops/dev_mail_sender_config_sync_result_v1.json")
ROLLBACK_JSON = Path("/mnt/artifacts/ops/dev_mail_sender_config_sync_rollback_v1.json")


def clean(value):
    return "" if value is None or value is False else str(value).strip()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def collect_state():
    ICP = env["ir.config_parameter"].sudo()  # noqa: F821
    companies = env["res.company"].sudo().search([])  # noqa: F821
    finance_user = env["res.users"].sudo().search([("login", "=", FINANCE_LOGIN)], limit=1)  # noqa: F821
    return {
        "mail_default_from": clean(ICP.get_param("mail.default.from")),
        "companies": [
            {
                "id": company.id,
                "name": company.name,
                "email": clean(company.email),
            }
            for company in companies
        ],
        "finance_user": {
            "id": finance_user.id if finance_user else False,
            "login": finance_user.login if finance_user else "",
            "email": clean(finance_user.email) if finance_user else "",
            "partner_id": finance_user.partner_id.id if finance_user else False,
            "partner_email": clean(finance_user.partner_id.email) if finance_user else "",
        },
    }


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    before = collect_state()
    write_json(ROLLBACK_JSON, {"run_id": RUN_ID, "database": env.cr.dbname, "before": before})  # noqa: F821

    planned = {
        "mail_default_from": DEFAULT_FROM,
        "company_email": DEFAULT_FROM,
        "finance_user_email": FINANCE_EMAIL,
    }
    written = {
        "mail_default_from": False,
        "company_count": 0,
        "finance_user": False,
        "finance_partner": False,
    }

    if mode == "write":
        ICP = env["ir.config_parameter"].sudo()  # noqa: F821
        if clean(ICP.get_param("mail.default.from")) != DEFAULT_FROM:
            ICP.set_param("mail.default.from", DEFAULT_FROM)
            written["mail_default_from"] = True

        companies = env["res.company"].sudo().search([])  # noqa: F821
        for company in companies:
            if clean(company.email) != DEFAULT_FROM:
                company.email = DEFAULT_FROM
                written["company_count"] += 1

        finance_user = env["res.users"].sudo().search([("login", "=", FINANCE_LOGIN)], limit=1)  # noqa: F821
        if not finance_user:
            raise RuntimeError({"missing_finance_user": FINANCE_LOGIN})
        if clean(finance_user.email) != FINANCE_EMAIL:
            finance_user.email = FINANCE_EMAIL
            written["finance_user"] = True
        if clean(finance_user.partner_id.email) != FINANCE_EMAIL:
            finance_user.partner_id.email = FINANCE_EMAIL
            written["finance_partner"] = True
        env.cr.commit()  # noqa: F821

    after = collect_state()
    result = {
        "run_id": RUN_ID,
        "database": env.cr.dbname,  # noqa: F821
        "mode": mode,
        "planned": planned,
        "written": written,
        "before": before,
        "after": after,
        "rollback_json": str(ROLLBACK_JSON),
    }
    write_json(OUTPUT_JSON, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
