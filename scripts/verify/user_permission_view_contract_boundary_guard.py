# -*- coding: utf-8 -*-
"""Guard user-permission maintenance view contract boundaries.

Run with:
  make verify.user_permission_view_contract_boundary.guard DB_NAME=<db>

This script expects to be executed by ``odoo shell`` and uses the global
``env`` object. It verifies that the custom frontend contract consumes Odoo
facts with the intended source priority:

  ir.ui.view XML surface facts > contract governance projection > fields_get.
"""

EXPECTED_FIELD_LABELS = {
    "login": "用户名",
    "name": "姓名",
    "active": "启用",
    "password": "重置密码",
    "phone": "手机号",
    "email": "邮箱",
    "company_id": "所属公司",
    "sc_user_role_group_ids": "业务角色组",
}

EXPECTED_GROUP_LABELS = ["账号信息", "联系方式", "组织归属", "业务角色"]

FORBIDDEN_ACTION_LABELS = {
    "创建员工",
    "发送重置密码说明",
    "全部撤销",
    "修改密码",
    "action_totp_disable",
    "action_totp_enable_wizard",
}


def _env():
    return globals()["env"]


def _fail(errors):
    if errors:
        for error in errors:
            print("USER_PERMISSION_VIEW_CONTRACT_BOUNDARY_ERROR=%s" % error)
        raise AssertionError("; ".join(errors))


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk(value)


def _contract_for(login, render_profile="create"):
    from odoo import api
    from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler

    env = _env()
    action = env.ref("smart_construction_core.action_sc_runtime_user_management")
    user = env["res.users"].with_context(active_test=False).search([("login", "=", login)], limit=1)
    if not user:
        raise AssertionError("missing user: %s" % login)
    user_env = api.Environment(env.cr, user.id, dict(env.context, lang="zh_CN"))
    params = {
        "op": "action_open",
        "action_id": action.id,
        "client_type": "web_pc",
        "delivery_profile": "full",
        "render_profile": render_profile,
        "contract_surface": "user",
        "source_mode": "governance_pipeline",
    }
    result = UiContractV2Handler(user_env, payload={"params": params}).handle(params, {})
    envelope = result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else result
    if not envelope.get("ok", True):
        raise AssertionError("ui.contract.v2 failed for %s: %s" % (login, envelope))
    return envelope.get("data") or {}


def _field_labels(contract):
    labels = {}
    containers = ((contract.get("layoutContract") or {}).get("containerTree") or [])
    for row in _walk(containers):
        code = row.get("fieldCode") or row.get("field_code") or row.get("name")
        if not isinstance(code, str):
            continue
        if code in EXPECTED_FIELD_LABELS:
            label = row.get("label") or row.get("string") or ""
            if label and code not in labels:
                labels[code] = label
    return labels


def _labels_in_contract(contract):
    labels = []
    for row in _walk(contract):
        label = row.get("label") or row.get("title") or row.get("string")
        if isinstance(label, str) and label:
            labels.append(label)
    return labels


def _actions_in_contract(contract):
    labels = []
    for row in _walk(contract):
        kind = str(row.get("kind") or row.get("type") or row.get("buttonType") or "").lower()
        label = row.get("label") or row.get("title") or row.get("string") or row.get("name")
        if isinstance(label, str) and label and (
            "action" in kind
            or row.get("methodName")
            or row.get("buttonType")
            or row.get("payload")
            or row.get("action")
        ):
            labels.append(label)
    return labels


def _check_xml_view():
    env = _env()
    view = env.ref("smart_construction_core.view_sc_runtime_user_form")
    arch = view.arch_db or ""
    errors = []
    for label in EXPECTED_FIELD_LABELS.values():
        if ('string="%s"' % label) not in arch:
            errors.append("runtime user form XML missing field string: %s" % label)
    for label in EXPECTED_GROUP_LABELS:
        if ('string="%s"' % label) not in arch:
            errors.append("runtime user form XML missing group string: %s" % label)
    _fail(errors)
    print("USER_PERMISSION_XML_VIEW_ID=%s" % view.id)


def _check_acl():
    env = _env()
    group = env.ref("smart_construction_core.group_sc_cap_business_config_admin")
    model = env["ir.model"]._get("res.users")
    acl = env["ir.model.access"].search([("model_id", "=", model.id), ("group_id", "=", group.id)], limit=1)
    errors = []
    if not acl:
        errors.append("missing res.users ACL for business config admin")
    else:
        if not (acl.perm_read and acl.perm_write and acl.perm_create):
            errors.append(
                "business config admin res.users ACL must be read/write/create: read=%s write=%s create=%s"
                % (acl.perm_read, acl.perm_write, acl.perm_create)
            )
        if acl.perm_unlink:
            errors.append("business config admin must not unlink res.users")
    _fail(errors)
    print("USER_PERMISSION_ACL=%s read=%s write=%s create=%s unlink=%s" % (acl.name, acl.perm_read, acl.perm_write, acl.perm_create, acl.perm_unlink))


def _check_action_domain():
    from odoo.tools.safe_eval import safe_eval
    from odoo.addons.smart_core.security.platform_admin import platform_admin_groups

    env = _env()
    action = env.ref("smart_construction_core.action_sc_runtime_user_management")
    system_group = env.ref("base.group_system")
    platform_group_records = env["res.groups"]
    for group in platform_admin_groups(env, include_legacy=True):
        platform_group_records |= group
    domain = safe_eval(action.domain or "[]") if isinstance(action.domain, str) else (action.domain or [])
    users = env["res.users"].sudo().with_context(active_test=False).search(domain)
    errors = []
    if users.filtered(
        lambda user: (
            bool(user.groups_id & platform_group_records)
            or system_group in user.groups_id
        )
    ):
        errors.append("runtime user action domain leaked platform/system admin users")
    if env["res.users"].sudo().search([("login", "=", "weihuguanliyuan")], limit=1) not in users:
        errors.append("runtime user action domain should keep business config admin user visible")
    forbidden_logins = {"default"}
    leaked_non_real = users.filtered(
        lambda user: (
            not user.active
            or user.share
            or str(user.login or "").startswith(("demo_", "legacy_", "history_system_user_"))
            or str(user.login or "") in forbidden_logins
            or "测试" in str(user.name or "")
            or "临时账号" in str(user.name or "")
            or str(user.name or "").startswith(("Demo", "Smoke", "技术"))
            or not env["sc.legacy.user.profile"].sudo().with_context(active_test=False).search_count(
                [("user_id", "=", user.id)]
            )
        )
    )
    if leaked_non_real:
        errors.append("runtime user action domain leaked non-company-real users: %s" % ", ".join(leaked_non_real.mapped("login")))
    _fail(errors)
    print("USER_PERMISSION_ACTION_DOMAIN_VISIBLE_COUNT=%s" % len(users))


def _check_contract(login):
    contract = _contract_for(login)
    errors = []
    field_labels = _field_labels(contract)
    for field_name, expected_label in EXPECTED_FIELD_LABELS.items():
        actual = field_labels.get(field_name)
        if actual != expected_label:
            errors.append("field %s label expected=%s actual=%s" % (field_name, expected_label, actual))

    labels = _labels_in_contract(contract)
    for group_label in EXPECTED_GROUP_LABELS:
        if group_label not in labels:
            errors.append("missing group label in contract for %s: %s" % (login, group_label))

    form = (((contract.get("meta") or {}).get("compat") or {}).get("ui_contract") or {}).get("ui_contract", {}).get("views", {}).get("form", {})
    statusbar = form.get("statusbar") if isinstance(form, dict) else {}
    statusbar_nodes = []
    if isinstance(statusbar, dict) and (statusbar.get("field") or statusbar.get("states")):
        statusbar_nodes.append(statusbar)
    if statusbar_nodes:
        errors.append("user permission form contract leaked native statusbar for %s" % login)

    action_labels = set(_actions_in_contract(contract))
    leaked = sorted(FORBIDDEN_ACTION_LABELS & action_labels)
    if leaked:
        errors.append("user permission form contract leaked native actions for %s: %s" % (login, leaked))

    global_status = (contract.get("statusContract") or {}).get("globalStatus") or {}
    if global_status.get("pageAuth") != "edit":
        errors.append("contract pageAuth for %s expected=edit actual=%s" % (login, global_status.get("pageAuth")))

    _fail(errors)
    print("USER_PERMISSION_CONTRACT=%s pageAuth=%s labels=%s" % (login, global_status.get("pageAuth"), ",".join(field_labels.get(name, "") for name in EXPECTED_FIELD_LABELS)))


def main():
    _check_xml_view()
    _check_acl()
    _check_action_domain()
    _check_contract("weihuguanliyuan")
    _check_contract("admin")
    print("[user_permission_view_contract_boundary_guard] PASS")


main()
