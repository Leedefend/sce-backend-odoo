# -*- coding: utf-8 -*-
"""Read-only Odoo shell gate for low-code business config coverage.

Run with:
  ENV=dev DB_NAME=sc_demo make verify.business_config.coverage

The script expects the global ``env`` object from ``odoo shell``.
"""

import json
import os

from odoo.exceptions import UserError

from odoo.addons.smart_core.handlers.business_config_surface import BusinessConfigCoverageScanHandler


ROOT_MENU_XMLID = os.getenv("BUSINESS_CONFIG_COVERAGE_ROOT_MENU_XMLID", "smart_construction_core.menu_sc_root")
DEFAULT_LOGINS = [
    "admin",
    "demo_business_full",
    "wutao",
    "sc_fx_contract_admin",
    "sc_fx_cost_user",
    "sc_fx_executive",
    "sc_fx_finance",
    "sc_fx_material_user",
    "sc_fx_pm",
    "sc_fx_project_member",
]


def _env():
    return globals()["env"]


def _scan(env_obj, params):
    return BusinessConfigCoverageScanHandler(env=env_obj, payload={"params": params}).handle()


def _system_env(env_obj, user=None):
    context = dict(env_obj.context, business_config_system_remediation=True)
    if user is None:
        return env_obj(context=context)
    return env_obj(user=user, context=context)


def _summary(result):
    return (result.get("data") or {}).get("summary") if isinstance(result, dict) else {}


def _runtime_route_text(row):
    route = row.get("runtime_route") or {}
    path = str(route.get("path") or "").strip()
    if not path:
        return ""
    query = route.get("query") or {}
    if not isinstance(query, dict) or not query:
        return path
    pairs = [
        "%s=%s" % (key, value)
        for key, value in sorted(query.items())
        if str(key or "").strip() and str(value or "").strip()
    ]
    return "%s?%s" % (path, "&".join(pairs)) if pairs else path


def _sample_view_type(row, preferred_view_type=""):
    preferred = str(preferred_view_type or "").strip()
    if preferred and preferred in (row.get("target_view_types") or []):
        return preferred
    for view_type in ("pivot", "graph", "calendar", "dashboard", "form", "tree", "search"):
        if view_type in (row.get("target_view_types") or []):
            return view_type
    return ""


def _route_sample(row, scope_reason, preferred_view_type=""):
    route = _runtime_route_text(row)
    if not route:
        return None
    return {
        "action_id": int(row.get("action_id") or 0),
        "name": str(row.get("name") or row.get("model") or ""),
        "model": str(row.get("model") or ""),
        "severity": str(row.get("severity") or ""),
        "view_mode": str(row.get("view_mode") or ""),
        "view_type": _sample_view_type(row, preferred_view_type),
        "target_view_types": list(row.get("target_view_types") or []),
        "menu_ids": list(row.get("menu_ids") or []),
        "runtime_route": route,
        "sample_reason": scope_reason,
    }


def _route_samples(result, limit=20):
    data = result.get("data") if isinstance(result, dict) else {}
    items = data.get("items") if isinstance(data, dict) else []
    if not isinstance(items, list):
        return []
    issue_rows = [
        row for row in items
        if isinstance(row, dict)
        and (not row.get("is_runtime_complete") or not row.get("is_complete") or not row.get("has_menu"))
    ]
    rows = [row for row in items if isinstance(row, dict)]
    samples = []
    seen = set()

    def add(row, reason, preferred_view_type=""):
        if not isinstance(row, dict):
            return
        sample = _route_sample(row, reason, preferred_view_type)
        if not sample:
            return
        key = "%s:%s" % (sample["runtime_route"], sample["view_type"])
        if key in seen:
            return
        seen.add(key)
        samples.append(sample)

    for row in issue_rows:
        add(row, "issue")
        if len(samples) >= limit:
            return samples

    for required_view_type in ("pivot", "graph", "form", "tree", "search"):
        for row in rows:
            if required_view_type in (row.get("target_view_types") or []):
                add(row, "representative:%s" % required_view_type, required_view_type)
                break
        if len(samples) >= limit:
            return samples

    for row in rows:
        add(row, "sample")
        if len(samples) >= limit:
            break
    return samples


def _showcase_action_ids(env_obj):
    rows = env_obj["ir.model.data"].sudo().search([
        ("module", "=", "smart_construction_demo"),
        ("model", "=", "ir.actions.act_window"),
    ])
    return {int(row.res_id or 0) for row in rows if int(row.res_id or 0)}


def _scope_result(name, env_obj, params):
    result = _scan(env_obj, params)
    summary = _summary(result) or {}
    data = result.get("data") if isinstance(result, dict) else {}
    items = data.get("items") if isinstance(data, dict) else []
    items = [row for row in items if isinstance(row, dict)]
    showcase_ids = _showcase_action_ids(env_obj)
    excluded = [row for row in items if int(row.get("action_id") or 0) in showcase_ids]
    delivery_items = [row for row in items if int(row.get("action_id") or 0) not in showcase_ids]
    runtime_missing = [row for row in delivery_items if not row.get("is_runtime_complete")]
    missing_by_view = {
        view_type: sum(view_type in (row.get("runtime_missing_view_types") or []) for row in runtime_missing)
        for view_type in ("form", "tree", "search", "pivot", "graph", "calendar", "dashboard")
    }
    delivery_result = {**result, "data": {**(data or {}), "items": delivery_items}}
    return {
        "scope": name,
        "overall_status": "pass" if not runtime_missing else "blocked",
        "action_count": len(delivery_items),
        "runtime_missing_count": len(runtime_missing),
        "runtime_missing_form_count": missing_by_view["form"],
        "runtime_missing_list_count": missing_by_view["tree"],
        "runtime_missing_search_count": missing_by_view["search"],
        "runtime_missing_analysis_count": sum(missing_by_view[key] for key in ("pivot", "graph", "calendar", "dashboard")),
        "severity_counts": summary.get("severity_counts") or {},
        "remediation_action_counts": summary.get("remediation_action_counts") or {},
        "runtime_route_samples": _route_samples(delivery_result),
        "excluded_showcase_actions": [
            {
                "action_id": int(row.get("action_id") or 0),
                "name": str(row.get("name") or ""),
                "menu_ids": list(row.get("menu_ids") or []),
                "runtime_missing_view_types": list(row.get("runtime_missing_view_types") or []),
                "decision": "excluded_from_formal_delivery_denominator",
                "authority": "ir.model.data.module=smart_construction_demo",
            }
            for row in excluded
        ],
    }


def _representative_logins():
    raw = os.getenv("BUSINESS_CONFIG_COVERAGE_LOGINS", "")
    if raw.strip():
        return [item.strip() for item in raw.split(",") if item.strip()]
    return list(DEFAULT_LOGINS)


def main():
    env_obj = _env()
    base_params = {
        "limit": int(os.getenv("BUSINESS_CONFIG_COVERAGE_LIMIT", "1000")),
        "root_menu_xmlid": ROOT_MENU_XMLID,
        "use_product_navigation_actions": os.getenv("BUSINESS_CONFIG_COVERAGE_USE_PRODUCT_NAV", "1").strip().lower()
        not in {"0", "false", "no", "off"},
        "product_key": os.getenv("BUSINESS_CONFIG_COVERAGE_PRODUCT_KEY", ""),
        "edition_key": os.getenv("BUSINESS_CONFIG_COVERAGE_EDITION_KEY", ""),
        "base_product_key": os.getenv("BUSINESS_CONFIG_COVERAGE_BASE_PRODUCT_KEY", ""),
    }
    rows = [
        _scope_result(
            "system_root",
            _system_env(env_obj),
            {**base_params, "include_all_root_menu_actions": True},
        )
    ]
    missing_logins = []
    User = env_obj["res.users"].sudo()
    for login in _representative_logins():
        user = User.search([("login", "=", login), ("active", "=", True)], limit=1)
        if not user:
            missing_logins.append(login)
            continue
        rows.append(_scope_result("user:%s" % login, _system_env(env_obj, user=user), base_params))

    failed = [
        row for row in rows
        if row["overall_status"] != "pass" or row["runtime_missing_count"] != 0
    ]
    report = {
        "database": env_obj.cr.dbname,
        "root_menu_xmlid": ROOT_MENU_XMLID,
        "missing_representative_logins": missing_logins,
        "scope_count": len(rows),
        "failed_scope_count": len(failed),
        "scopes": rows,
    }
    report_path = os.getenv(
        "BUSINESS_CONFIG_COVERAGE_REPORT_PATH",
        "/tmp/business_config_coverage_gate.json",
    )
    if report_path:
        report_dir = os.path.dirname(report_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print("[business_config_coverage_gate] %s" % ("FAIL" if failed else "PASS"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failed:
        raise UserError("低代码业务配置覆盖验收未通过：%s" % ", ".join(row["scope"] for row in failed[:10]))


main()
