# -*- coding: utf-8 -*-
"""Audit business list search coverage.

Run inside Odoo shell, for example:
docker compose exec -T odoo odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/ops/audit_business_list_search.py
"""

import json
import re
import time

from lxml import etree
from odoo.osv import expression

from odoo.addons.smart_core.handlers.api_data import ApiDataHandler


start = time.time()
handler = ApiDataHandler(env=env)  # noqa: F821 - provided by odoo shell
Menu = env["ir.ui.menu"].sudo()  # noqa: F821 - provided by odoo shell
View = env["ir.ui.view"].sudo()  # noqa: F821 - provided by odoo shell

INCLUDE_RE = re.compile(
    r"(项目|单位|名称|编号|单号|备注|内容|合同|账户|人员|申请人|录入人|施工|供应商|往来|收款|付款|发票|凭证|标题|事由|地址|开户|银行|材料|租赁|劳务|分包|机械)"
)
EXCLUDE_RE = re.compile(
    r"(状态|日期|时间|金额|数量|附件|税率|排序|是否|推送结果|金蝶|大写|余额|期数|单价|总额|合计|比例|天数)"
)


def _action_domain(action):
    try:
        return action._get_eval_domain() if hasattr(action, "_get_eval_domain") else []
    except Exception:
        try:
            from odoo.tools.safe_eval import safe_eval

            return safe_eval(action.domain or "[]") if action.domain else []
        except Exception:
            return []


def _tree_view(action):
    for view_id, view_type in action.views:
        if view_type in ("tree", "list") and view_id:
            view = View.browse(view_id)
            if view.exists():
                return view
    return None


def _fields_from_view(view):
    if not view or not view.arch_db:
        return []
    root = etree.fromstring(view.arch_db.encode())
    names = []
    for node in root.xpath(".//field[@name]"):
        name = (node.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _sample_term(value):
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    if not text or len(text) < 2:
        return ""
    if len(text) <= 18:
        return text
    middle = len(text) // 2
    return text[max(0, middle - 8) : middle + 10].strip()


failures = []
checked_terms = 0
actions_seen = set()
menus_checked = 0

for menu in Menu.search([]):
    path = menu.complete_name or ""
    if "智慧施工管理平台" not in path:
        continue
    action = menu.action
    if not action or action._name != "ir.actions.act_window" or not action.res_model:
        continue
    if action.id in actions_seen:
        continue
    actions_seen.add(action.id)
    menus_checked += 1
    if "用户核对菜单" in path:
        continue
    try:
        Model = env[action.res_model].sudo()  # noqa: F821 - provided by odoo shell
    except Exception:
        continue
    view = _tree_view(action)
    fields = _fields_from_view(view)
    if not fields:
        continue
    fields_safe = handler._filter_readable_fields(Model, fields)
    base_domain = _action_domain(action)
    records = Model.search(base_domain, limit=3)
    per_action_terms = 0
    for record in records:
        for field_name in fields_safe:
            field = Model._fields.get(field_name)
            if not field or getattr(field, "type", "") not in ("char", "text", "html", "many2one", "selection"):
                continue
            label = (getattr(field, "string", "") or field_name or "").strip()
            if not INCLUDE_RE.search(label) or EXCLUDE_RE.search(label):
                continue
            try:
                value = record[field_name]
                if getattr(field, "type", "") == "many2one":
                    value = value.display_name if value else ""
            except Exception:
                continue
            term = _sample_term(value)
            if not term:
                continue
            checked_terms += 1
            per_action_terms += 1
            search_domain = handler._build_search_term_domain(Model, term, fields_safe)
            try:
                count = Model.search_count(expression.AND([base_domain, search_domain, [("id", "=", record.id)]]))
            except Exception as exc:
                failures.append(
                    {
                        "kind": "error",
                        "action_id": action.id,
                        "action_name": action.name,
                        "menu": path,
                        "model": action.res_model,
                        "view": view.name if view else "",
                        "record_id": record.id,
                        "field": field_name,
                        "label": label,
                        "term": term,
                        "error": str(exc)[:300],
                    }
                )
                continue
            if count < 1:
                failures.append(
                    {
                        "kind": "miss",
                        "action_id": action.id,
                        "action_name": action.name,
                        "menu": path,
                        "model": action.res_model,
                        "view": view.name if view else "",
                        "record_id": record.id,
                        "field": field_name,
                        "label": label,
                        "term": term,
                        "visible_text": str(value or "")[:300],
                    }
                )
            if per_action_terms >= 5:
                break
        if per_action_terms >= 5:
            break

print(
    json.dumps(
        {
            "checked": {"menus": menus_checked, "actions": len(actions_seen), "terms": checked_terms},
            "failure_count": len(failures),
            "failures": failures[:120],
            "elapsed_seconds": round(time.time() - start, 2),
        },
        ensure_ascii=False,
        indent=2,
    )
)
