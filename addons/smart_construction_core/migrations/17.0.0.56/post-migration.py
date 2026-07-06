# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api


ROOT_MENU_XMLID = "smart_construction_core.menu_sc_root"
MAX_ITERATIONS = 8
IGNORED_BOOTSTRAP_FAILURES = {
    ("quota.import.wizard", "四川定额导入"),
}
REPRESENTATIVE_LOGINS = [
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


def _run(handler_cls, env, params):
    return handler_cls(env=env, payload={"params": params}).handle()


def _system_env(env, user=None):
    context = dict(env.context, business_config_system_remediation=True)
    if user is None:
        return env(context=context)
    return env(user=user, context=context)


def _is_ignored_bootstrap_failure(item):
    model = str(item.get("model") or "").strip()
    name = str(item.get("name") or "").strip()
    return (model, name) in IGNORED_BOOTSTRAP_FAILURES


def _format_bootstrap_failure(item):
    return "%s:%s" % (item.get("action_id"), item.get("name") or item.get("model"))


def _remediate(env, *, params, scan_handler, bootstrap_handler):
    for _index in range(MAX_ITERATIONS):
        scan = _run(scan_handler, env, params)
        summary = (scan.get("data") or {}).get("summary") if isinstance(scan, dict) else {}
        if int((summary or {}).get("runtime_missing_count") or 0) <= 0:
            break
        result = _run(bootstrap_handler, env, params)
        data = (result.get("data") or {}) if isinstance(result, dict) else {}
        if int(data.get("failed_count") or 0) > 0:
            failed_items = [
                item
                for item in (data.get("results") or [])
                if not item.get("ok")
            ]
            blocking_failures = [
                item for item in failed_items
                if not _is_ignored_bootstrap_failure(item)
            ]
            if blocking_failures or not failed_items:
                failures = [_format_bootstrap_failure(item) for item in (blocking_failures or failed_items)][:10]
                raise RuntimeError("业务配置契约自动固化失败：%s" % "，".join(failures))
            # System configuration wizards are not business configuration contracts.
            break
        if int(data.get("candidate_count") or 0) <= 0:
            raise RuntimeError("业务配置契约仍有运行态缺口，但没有可自动固化的候选项。")


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.smart_core.handlers.business_config_surface import (
        BusinessConfigCoverageBootstrapMissingHandler,
        BusinessConfigCoverageScanHandler,
    )

    base_params = {
        "limit": 1000,
        "batch_limit": 300,
        "root_menu_xmlid": ROOT_MENU_XMLID,
        "skip_unavailable_models": True,
    }
    _remediate(
        _system_env(env),
        params={**base_params, "include_all_root_menu_actions": True},
        scan_handler=BusinessConfigCoverageScanHandler,
        bootstrap_handler=BusinessConfigCoverageBootstrapMissingHandler,
    )

    group_ids = []
    for xmlid in (
        "smart_core.group_smart_core_business_config_admin",
        "smart_core.group_smart_core_admin",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)
        if group:
            group_ids.append(group.id)
    user_domain = [
        ("active", "=", True),
        ("share", "=", False),
        "|",
        ("login", "in", REPRESENTATIVE_LOGINS),
        ("groups_id", "in", group_ids or [0]),
    ]
    users = env["res.users"].sudo().search(user_domain)
    for user in users:
        _remediate(
            _system_env(env, user=user),
            params=base_params,
            scan_handler=BusinessConfigCoverageScanHandler,
            bootstrap_handler=BusinessConfigCoverageBootstrapMissingHandler,
        )
