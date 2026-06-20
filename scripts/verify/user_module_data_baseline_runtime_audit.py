# -*- coding: utf-8 -*-
"""Runtime audit for the P2 user-module data baseline.

Run through Odoo shell:
    DB_NAME=sc_demo make verify.user_module.data_baseline.runtime_audit
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from odoo.tools.misc import file_path


def _artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/tmp/user_module_data_baseline")
    path = root / env.cr.dbname  # noqa: F821
    path.mkdir(parents=True, exist_ok=True)
    return path


def _payload_user_count() -> int:
    xml_path = file_path("smart_construction_custom/data/user_master_v1.xml")
    root = ET.parse(xml_path).getroot()
    return len(
        [
            node
            for node in root.iter("record")
            if str(node.attrib.get("model") or "").strip() == "res.users"
        ]
    )


def _legacy_user_count() -> int:
    return env["res.users"].sudo().with_context(active_test=False).search_count([("login", "=like", "legacy_%")])  # noqa: F821


def _baseline_user_count() -> int:
    Imd = env["ir.model.data"].sudo()  # noqa: F821
    rows = Imd.search(
        [
            ("module", "=", "smart_construction_custom"),
            ("name", "=like", "legacy_user_sc_%"),
            ("model", "=", "res.users"),
        ]
    )
    user_ids = [row.res_id for row in rows if row.res_id]
    if not user_ids:
        return 0
    return env["res.users"].sudo().with_context(active_test=False).search_count([("id", "in", user_ids)])  # noqa: F821


def _custom_xmlid_count() -> int:
    return env["ir.model.data"].sudo().search_count(  # noqa: F821
        [
            ("module", "=", "smart_construction_custom"),
            ("name", "=like", "legacy_user_sc_%"),
            ("model", "=", "res.users"),
        ]
    )


def _duplicate_legacy_logins() -> list[dict[str, object]]:
    User = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    rows = User.read_group(
        [("login", "=like", "legacy_%")],
        ["login"],
        ["login"],
        lazy=False,
    )
    duplicates = []
    for row in rows:
        count = int(row.get("login_count") or row.get("__count") or 0)
        login = row.get("login")
        if login and count > 1:
            duplicates.append({"login": login, "count": count})
    return duplicates


def _missing_required_login_aliases() -> list[str]:
    required = ["wutao", "chenshuai", "caisiqi", "zhaowei", "yangdesheng"]
    User = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
    existing = set(User.search([("login", "in", required)]).mapped("login"))
    return [login for login in required if login not in existing]


def _table_count(table: str, where: str = "") -> int | None:
    env.cr.execute("SELECT to_regclass(%s)", (table,))  # noqa: F821
    if not env.cr.fetchone()[0]:  # noqa: F821
        return None
    sql = f"SELECT COUNT(*) FROM {table}"
    if where:
        sql += f" WHERE {where}"
    env.cr.execute(sql)  # noqa: F821
    return int(env.cr.fetchone()[0] or 0)  # noqa: F821


def _business_data_counts() -> dict[str, int | None]:
    return {
        "project_project": _table_count("project_project"),
        "construction_contract": _table_count("construction_contract"),
        "payment_request": _table_count("payment_request"),
        "sc_expense_claim": _table_count("sc_expense_claim"),
        "sc_receipt_income": _table_count("sc_receipt_income"),
        "sc_legacy_direct_acceptance_fact": _table_count("sc_legacy_direct_acceptance_fact"),
        "sc_legacy_receipt_income_fact": _table_count("sc_legacy_receipt_income_fact"),
        "sc_legacy_payment_adjustment_fact": _table_count("sc_legacy_payment_adjustment_fact"),
        "sc_legacy_self_funding_fact": _table_count("sc_legacy_self_funding_fact"),
        "sc_legacy_supplier_contract_pricing_fact": _table_count("sc_legacy_supplier_contract_pricing_fact"),
        "sc_legacy_invoice_analysis_report_fact": _table_count("sc_legacy_invoice_analysis_report_fact"),
        "sc_legacy_project_operation_report_fact": _table_count("sc_legacy_project_operation_report_fact"),
    }


def _assert_business_data_restored(counts: dict[str, int | None]) -> list[str]:
    errors: list[str] = []
    required_positive = {
        "project_project": counts.get("project_project"),
        "construction_contract": counts.get("construction_contract"),
        "payment_request": counts.get("payment_request"),
    }
    for table, value in required_positive.items():
        if value is None:
            errors.append(f"business table missing after history baseline replay: {table}")
        elif value <= 0:
            errors.append(f"business table has no rows after history baseline replay: {table}=0")

    legacy_fact_tables = [
        table
        for table in counts
        if table.startswith("sc_legacy_") and table.endswith("_fact")
    ]
    legacy_fact_total = sum(int(counts.get(table) or 0) for table in legacy_fact_tables)
    if legacy_fact_total <= 0:
        errors.append("legacy business fact tables have no rows after history baseline replay")
    return errors


def main() -> int:
    Initializer = env["sc.user.preference.initialization"].sudo()  # noqa: F821
    payload_count = _payload_user_count()
    before_users = _legacy_user_count()
    before_baseline_users = _baseline_user_count()
    before_xmlids = _custom_xmlid_count()
    first = Initializer.apply_legacy_user_master_data_baseline()
    mid_users = _legacy_user_count()
    mid_baseline_users = _baseline_user_count()
    mid_xmlids = _custom_xmlid_count()
    second = Initializer.apply_legacy_user_master_data_baseline()
    history_business = Initializer.apply_history_business_data_baseline_manifest()
    rebaseline_contract = Initializer.apply_user_data_rebaseline_contract()
    business_data_counts = _business_data_counts()
    after_users = _legacy_user_count()
    after_baseline_users = _baseline_user_count()
    after_xmlids = _custom_xmlid_count()
    duplicates = _duplicate_legacy_logins()
    missing_aliases = _missing_required_login_aliases()

    errors = []
    if payload_count < 100:
        errors.append(f"payload_count too small: {payload_count} < 100")
    if mid_baseline_users != payload_count or after_baseline_users != payload_count:
        errors.append(
            "baseline user XMLID binding mismatch: "
            f"payload={payload_count} mid={mid_baseline_users} after={after_baseline_users}"
        )
    if mid_xmlids != payload_count or after_xmlids != payload_count:
        errors.append(f"custom XMLID count mismatch: payload={payload_count} mid={mid_xmlids} after={after_xmlids}")
    if missing_aliases:
        errors.append(f"required login aliases missing: {missing_aliases}")
    if second.get("created") != 0:
        errors.append(f"second run created users: {second.get('created')}")
    if after_baseline_users != mid_baseline_users or after_xmlids != mid_xmlids:
        errors.append(
            "second run is not idempotent: "
            f"users {mid_baseline_users}->{after_baseline_users}, xmlids {mid_xmlids}->{after_xmlids}"
        )
    if duplicates:
        errors.append(f"duplicate legacy logins: {duplicates[:10]}")
    if history_business.get("status") != "PASS":
        errors.append(f"history business baseline manifest failed: {history_business}")
    if int(history_business.get("visible_business_family_count") or 0) < 11:
        errors.append(f"history business family count too small: {history_business}")
    if int(history_business.get("legacy_asset_package_count") or 0) < 23:
        errors.append(f"legacy asset package count too small: {history_business}")
    if int(history_business.get("post_asset_closure_target_count") or 0) < 70:
        errors.append(f"post-asset closure target count too small: {history_business}")
    if history_business.get("restore_target") != "user_module.history_business_baseline.restore":
        errors.append(f"history business restore target missing: {history_business}")
    if history_business.get("external_payload_lock") != "docs/migration_alignment/migration_asset_package_lock_v1.json":
        errors.append(f"history business external payload lock missing: {history_business}")
    if rebaseline_contract.get("status") != "PASS":
        errors.append(f"user data rebaseline contract failed: {rebaseline_contract}")
    if int(rebaseline_contract.get("scbs55_surface_count") or 0) != 42:
        errors.append(f"SCBS55 surface count mismatch: {rebaseline_contract}")
    if int(rebaseline_contract.get("scbsly_v2_surface_count") or 0) != 32:
        errors.append(f"SCBSLY_V2 surface count mismatch: {rebaseline_contract}")
    if int(rebaseline_contract.get("history_payload_count") or 0) != 52:
        errors.append(f"history payload count mismatch: {rebaseline_contract}")
    if int(rebaseline_contract.get("core_replay_asset_count") or 0) != 7:
        errors.append(f"core replay asset count mismatch: {rebaseline_contract}")
    if rebaseline_contract.get("attachment_policy") != "link_only":
        errors.append(f"attachment policy mismatch: {rebaseline_contract}")
    if os.getenv("USER_MODULE_DATA_BASELINE_REQUIRE_BUSINESS_ROWS") == "1":
        errors.extend(_assert_business_data_restored(business_data_counts))

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "payload_user_count": payload_count,
        "before": {
            "legacy_users": before_users,
            "baseline_users": before_baseline_users,
            "custom_xmlids": before_xmlids,
        },
        "after_first_run": {
            "legacy_users": mid_users,
            "baseline_users": mid_baseline_users,
            "custom_xmlids": mid_xmlids,
            "result": first,
        },
        "after_second_run": {
            "legacy_users": after_users,
            "baseline_users": after_baseline_users,
            "custom_xmlids": after_xmlids,
            "result": second,
        },
        "history_business_data": history_business,
        "rebaseline_contract": rebaseline_contract,
        "business_data_counts": business_data_counts,
        "duplicate_legacy_logins": duplicates,
        "missing_required_login_aliases": missing_aliases,
        "errors": errors,
    }
    out = _artifact_root() / "user_module_data_baseline_runtime_audit.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("USER_MODULE_DATA_BASELINE_RUNTIME_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


raise SystemExit(main())
