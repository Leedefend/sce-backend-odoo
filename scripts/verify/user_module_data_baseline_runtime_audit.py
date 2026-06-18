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


def main() -> int:
    Initializer = env["sc.user.preference.initialization"].sudo()  # noqa: F821
    payload_count = _payload_user_count()
    before_users = _legacy_user_count()
    before_xmlids = _custom_xmlid_count()
    first = Initializer.apply_legacy_user_master_data_baseline()
    mid_users = _legacy_user_count()
    mid_xmlids = _custom_xmlid_count()
    second = Initializer.apply_legacy_user_master_data_baseline()
    history_business = Initializer.apply_history_business_data_baseline_manifest()
    after_users = _legacy_user_count()
    after_xmlids = _custom_xmlid_count()
    duplicates = _duplicate_legacy_logins()

    errors = []
    if payload_count < 100:
        errors.append(f"payload_count too small: {payload_count} < 100")
    if mid_users != payload_count or after_users != payload_count:
        errors.append(f"legacy user count mismatch: payload={payload_count} mid={mid_users} after={after_users}")
    if mid_xmlids != payload_count or after_xmlids != payload_count:
        errors.append(f"custom XMLID count mismatch: payload={payload_count} mid={mid_xmlids} after={after_xmlids}")
    if second.get("created") != 0:
        errors.append(f"second run created users: {second.get('created')}")
    if after_users != mid_users or after_xmlids != mid_xmlids:
        errors.append(
            "second run is not idempotent: "
            f"users {mid_users}->{after_users}, xmlids {mid_xmlids}->{after_xmlids}"
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

    payload = {
        "status": "PASS" if not errors else "FAIL",
        "database": env.cr.dbname,  # noqa: F821
        "payload_user_count": payload_count,
        "before": {"legacy_users": before_users, "custom_xmlids": before_xmlids},
        "after_first_run": {"legacy_users": mid_users, "custom_xmlids": mid_xmlids, "result": first},
        "after_second_run": {"legacy_users": after_users, "custom_xmlids": after_xmlids, "result": second},
        "history_business_data": history_business,
        "duplicate_legacy_logins": duplicates,
        "errors": errors,
    }
    out = _artifact_root() / "user_module_data_baseline_runtime_audit.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("USER_MODULE_DATA_BASELINE_RUNTIME_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


raise SystemExit(main())
