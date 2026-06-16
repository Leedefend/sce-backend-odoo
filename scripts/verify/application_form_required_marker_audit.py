# -*- coding: utf-8 -*-
"""Audit required markers on application-like handling form menu entries.

Run inside Odoo shell:
    ENV=dev DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/application_form_required_marker_audit.py
"""

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler


INCLUDE_KEYWORDS = ("申请", "报销", "借款", "开票")
EXCLUDE_KEYWORDS = ("统计", "汇总", "明细", "台账", "审批", "配置")
EXCLUDE_PATH_KEYWORDS = ("用户验收/",)


def _walk_layout(layout):
    visible = set()
    required = set()

    def visit(node):
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        node_type = str(node.get("type") or node.get("kind") or "").strip().lower()
        name = str(node.get("name") or "").strip()
        field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
        field_info = field_info or (node.get("field_info") if isinstance(node.get("field_info"), dict) else {})
        if name and (node_type == "field" or field_info):
            visible.add(name)
            if node.get("required") is True or field_info.get("required") is True:
                required.add(name)
        for key in ("children", "groups", "pages", "fields", "items", "nodes", "layout"):
            value = node.get(key)
            if isinstance(value, list):
                visit(value)

    visit(layout)
    return visible, required


def _contract_required(data):
    out = set()
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    for name, descriptor in fields.items():
        if isinstance(descriptor, dict) and descriptor.get("required") is True:
            out.add(str(name))
    policies = data.get("field_policies") if isinstance(data.get("field_policies"), dict) else {}
    for name, policy in policies.items():
        if not isinstance(policy, dict):
            continue
        if (
            policy.get("source_required") is True
            or policy.get("required") is True
            or bool(policy.get("required_profiles") if isinstance(policy.get("required_profiles"), list) else [])
        ):
            out.add(str(name))
    for row in data.get("validation_rules") if isinstance(data.get("validation_rules"), list) else []:
        if isinstance(row, dict) and str(row.get("code") or "").strip().upper() == "REQUIRED":
            name = str(row.get("field") or "").strip()
            if name:
                out.add(name)
    return out


def _is_application_menu(label):
    return (
        "智慧施工管理平台/" in label
        and any(keyword in label for keyword in INCLUDE_KEYWORDS)
        and not any(keyword in label for keyword in EXCLUDE_KEYWORDS)
        and not any(keyword in label for keyword in EXCLUDE_PATH_KEYWORDS)
    )


assembler = PageAssembler(env)  # noqa: F821
menus = env["ir.ui.menu"].sudo().search([])  # noqa: F821
failures = []
checked = 0

for menu in menus:
    label = str(menu.complete_name or menu.name or "").strip()
    if not _is_application_menu(label):
        continue
    action = menu.action
    if not action or action._name != "ir.actions.act_window" or not action.res_model:
        continue
    data, _versions = assembler.assemble_page_contract(
        {
            "model": action.res_model,
            "view_types": ["form"],
            "view_type": "form",
            "action_id": int(action.id),
            "render_profile": "create",
        },
        action=action.read()[0],
    )
    checked += 1
    layout = (((data.get("views") or {}).get("form") or {}).get("layout")) or []
    visible, layout_required = _walk_layout(layout)
    contract_required = _contract_required(data)
    visible_contract_required = {name for name in contract_required if name in visible}
    if not contract_required:
        failures.append((label, action.res_model, int(action.id), "contract_required_empty"))
        continue
    if not layout_required:
        failures.append((label, action.res_model, int(action.id), "layout_required_empty", sorted(contract_required)[:12]))
        continue
    missing_layout = sorted(visible_contract_required - layout_required)
    if missing_layout:
        failures.append((label, action.res_model, int(action.id), "layout_required_missing", missing_layout[:12]))

if failures:
    print("[application_form_required_marker_audit] FAIL checked=%s failures=%s" % (checked, len(failures)))
    for failure in failures[:120]:
        print("ERROR", failure)
    if len(failures) > 120:
        print("ERROR ... truncated %s more" % (len(failures) - 120))
    raise SystemExit(1)

print("[application_form_required_marker_audit] PASS checked=%s" % checked)
