# -*- coding: utf-8 -*-
"""Verify rebuilt runtime language baseline.

Run through Odoo shell:
    DB_NAME=sc_prod_sim make verify.runtime.language.baseline
"""

import json
import os

from lxml import etree


LANG_CODE = os.getenv("SC_RUNTIME_LANG", "zh_CN").strip() or "zh_CN"
TZ = os.getenv("SC_RUNTIME_TZ", "Asia/Shanghai").strip() or "Asia/Shanghai"


def _fail(errors, message):
    errors.append(message)


def _field_string(env, user, model, field_name):
    run_env = env(user=user, context=dict(env.context or {}, lang=LANG_CODE))
    field = (run_env[model].fields_get([field_name], attributes=["string"]) or {}).get(field_name) or {}
    return str(field.get("string") or "").strip()


def _form_arch_strings(env, user, model):
    run_env = env(user=user, context=dict(env.context or {}, lang=LANG_CODE))
    view = run_env[model].get_view(view_type="form")
    root = etree.fromstring(view["arch"].encode("utf-8"))
    return [str(value or "").strip() for value in root.xpath(".//@string") if str(value or "").strip()]


errors = []
report = {"lang": LANG_CODE, "tz": TZ}

Lang = env["res.lang"].sudo().with_context(active_test=False)
lang = Lang.search([("code", "=", LANG_CODE)], limit=1)
report["lang_exists"] = bool(lang)
report["lang_active"] = bool(lang.active) if lang else False
if not lang:
    _fail(errors, "zh_CN language record missing")
elif not lang.active:
    _fail(errors, "zh_CN language inactive")

Users = env["res.users"].sudo().with_context(active_test=False)
critical_logins = ["admin", "wutao", "chenshuai"]
users = Users.search([("login", "in", critical_logins)])
report["users"] = {user.login: {"lang": user.lang, "tz": user.tz} for user in users}
missing = sorted(set(critical_logins) - set(users.mapped("login")))
if missing:
    _fail(errors, "critical users missing: %s" % ",".join(missing))
for user in users:
    if user.lang != LANG_CODE:
        _fail(errors, "user %s lang=%s expected=%s" % (user.login, user.lang, LANG_CODE))
    if user.tz != TZ:
        _fail(errors, "user %s tz=%s expected=%s" % (user.login, user.tz, TZ))

probe_user = Users.search([("login", "=", "wutao")], limit=1) or env.user
field_labels = {
    "name": _field_string(env, probe_user, "project.project", "name"),
    "partner_id": _field_string(env, probe_user, "project.project", "partner_id"),
    "user_id": _field_string(env, probe_user, "project.project", "user_id"),
    "privacy_visibility": _field_string(env, probe_user, "project.project", "privacy_visibility"),
}
report["project_project_form_labels"] = field_labels
expected_labels = {
    "name": "名称",
    "partner_id": "客户",
    "user_id": "项目管理员",
    "privacy_visibility": "可见性",
}
for field_name, expected in expected_labels.items():
    if field_labels.get(field_name) != expected:
        _fail(
            errors,
            "project.project %s label=%r expected=%r" % (field_name, field_labels.get(field_name), expected),
        )

form_strings = _form_arch_strings(env, probe_user, "project.project")
report["project_project_form_arch_required_strings"] = {
    value: value in form_strings for value in ["提交立项", "预算", "合同", "执行结构", "工程量清单"]
}
for value, exists in report["project_project_form_arch_required_strings"].items():
    if not exists:
        _fail(errors, "project.project form arch missing zh_CN string: %s" % value)

menu_labels = {}
for xmlid in ["smart_construction_core.menu_sc_root", "smart_construction_core.menu_sc_project_project"]:
    rec = env.ref(xmlid, raise_if_not_found=False)
    if not rec:
        _fail(errors, "menu xmlid missing: %s" % xmlid)
        continue
    menu_labels[xmlid] = rec.sudo().with_context(lang=LANG_CODE).name
report["menu_labels"] = menu_labels
if menu_labels.get("smart_construction_core.menu_sc_root") != "智能施工 2.0":
    _fail(errors, "root menu zh_CN label mismatch")
if menu_labels.get("smart_construction_core.menu_sc_project_project") != "项目台账（试点）":
    _fail(errors, "project menu zh_CN label mismatch")

report["errors"] = errors
print(json.dumps(report, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
