# -*- coding: utf-8 -*-
"""Smoke-test core formal business flows for create/write continuity.

Run with:
    odoo shell -d <db> -c <conf> < scripts/verify/formal_business_operation_core_flow_smoke.py
"""

from __future__ import annotations

import json
import os
import uuid
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval


ARTIFACT_PATH = Path(os.getenv(
    "FORMAL_BUSINESS_OPERATION_CORE_FLOW_SMOKE_JSON",
    "/tmp/sce-product-artifacts/formal_business_operation_core_flow_smoke_v1.json",
))
REPORT_PATH = Path(os.getenv(
    "FORMAL_BUSINESS_OPERATION_CORE_FLOW_SMOKE_MD",
    "/tmp/sce-product-artifacts/formal_business_operation_core_flow_smoke_v1.md",
))

CORE_FLOW_SPECS = [
    {"label": "一般合同（公司）", "menu_xmlid": "smart_construction_core.menu_sc_general_contract"},
    {"label": "施工合同", "menu_xmlid": "smart_construction_core.menu_sc_construction_contract"},
    {"label": "材料计划", "menu_xmlid": "smart_construction_core.menu_project_material_plan"},
    {"label": "材料入库", "menu_xmlid": "smart_construction_core.menu_sc_material_inbound"},
    {"label": "材料出库", "menu_xmlid": "smart_construction_core.menu_sc_material_outbound"},
    {"label": "分包申请", "menu_xmlid": "smart_construction_core.menu_sc_subcontract_request"},
    {"label": "分包结算", "menu_xmlid": "smart_construction_core.menu_sc_subcontract_settlement"},
    {"label": "方单", "menu_xmlid": "smart_construction_core.menu_sc_labor_usage_acceptance"},
    {"label": "机械台班记录", "menu_xmlid": "smart_construction_core.menu_sc_equipment_shift_acceptance"},
    {"label": "收款登记", "menu_xmlid": "smart_construction_core.menu_sc_receipt_income"},
    {"label": "费用报销单", "menu_xmlid": "smart_construction_core.menu_sc_expense_claim"},
    {"label": "进项发票", "menu_xmlid": "smart_construction_core.menu_sc_invoice_input"},
]

WRITE_FIELD_PREFERENCE = (
    "note",
    "remark",
    "description",
    "memo",
    "summary",
    "line_note_summary",
    "date_plan",
    "document_date",
    "business_date",
    "register_date",
    "request_date",
    "name",
    "document_no",
    "contract_name",
    "subject",
)
WRITE_FIELD_BLOCK_PREFIXES = ("legacy_", "source_", "raw_", "history_", "uc_")
WRITE_FIELD_BLOCK_NAMES = {
    "legacy_fact_model",
    "legacy_fact_id",
    "legacy_source_model",
    "legacy_source_id",
    "source_model",
    "source_id",
}


class SmokeRollback(Exception):
    pass


def _text(value) -> str:
    return str(value or "").strip()


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _xmlid(env_obj, record) -> str:
    if not record:
        return ""
    data = env_obj["ir.model.data"].sudo().search([
        ("model", "=", record._name),
        ("res_id", "=", record.id),
    ], limit=1)
    return "%s.%s" % (data.module, data.name) if data else ""


def _safe_context(action) -> dict:
    try:
        value = safe_eval(action.context or "{}", {})
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _safe_domain(action) -> list:
    try:
        value = safe_eval(action.domain or "[]", {})
        return value if isinstance(value, list) else []
    except Exception:
        return []


def _domain_references_history(action) -> bool:
    domain_text = _text(action.domain)
    return any(token in domain_text for token in ("legacy_", "source_", "history_", "uc_"))


def _action_defaults(context: dict) -> dict:
    return {
        key.replace("default_", "", 1): value
        for key, value in context.items()
        if isinstance(key, str) and key.startswith("default_")
    }


def _is_stored_input_field(field) -> bool:
    return not bool(getattr(field, "compute", False)) and not bool(getattr(field, "related", False))


def _is_writable_field(field) -> bool:
    return _is_stored_input_field(field) and not bool(getattr(field, "readonly", False))


def _many2one_value(env_obj, field):
    comodel = getattr(field, "comodel_name", "")
    if not comodel or comodel not in env_obj:
        return None
    record = env_obj[comodel].sudo().with_context(active_test=False).search([], limit=1)
    return record.id if record else None


def _selection_value(field):
    selection = getattr(field, "selection", None) or []
    if callable(selection):
        return None
    for key, _label in selection:
        if key not in (False, None, ""):
            return key
    return None


def _simple_value(env_obj, model_name: str, field_name: str, field, token: str):
    field_type = getattr(field, "type", "")
    if field_name == "company_id" and "res.company" in env_obj:
        company = env_obj.company
        return company.id if company else _many2one_value(env_obj, field)
    if field_name == "currency_id" and "res.currency" in env_obj:
        currency = env_obj.company.currency_id
        return currency.id if currency else _many2one_value(env_obj, field)
    if field_name == "business_category_id" and "sc.business.category" in env_obj:
        category = env_obj["sc.business.category"].sudo().with_context(active_test=False).search([], limit=1)
        if category:
            return category.id
    if field_type in {"char", "text", "html"}:
        return "SMOKE-%s-%s" % (model_name.replace(".", "-"), token)
    if field_type == "date":
        return date.today().isoformat()
    if field_type == "datetime":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if field_type in {"float", "monetary"}:
        return 1.0
    if field_type == "integer":
        return 1
    if field_type == "boolean":
        return False
    if field_type == "selection":
        return _selection_value(field)
    if field_type == "many2one":
        return _many2one_value(env_obj, field)
    return None


def _required_field_names(Model) -> list[str]:
    names = []
    for name, field in Model._fields.items():
        if name == "id" or name.startswith("__"):
            continue
        if bool(getattr(field, "required", False)) and _is_writable_field(field):
            names.append(name)
    return sorted(names)


def _build_create_values(env_obj, Model, action_context: dict, token: str) -> tuple[dict, list[str]]:
    required_names = _required_field_names(Model)
    optional_names = [name for name in WRITE_FIELD_PREFERENCE if name in Model._fields]
    defaults = {}
    try:
        defaults.update(Model.default_get(sorted(set(required_names + optional_names))))
    except Exception:
        defaults = {}
    defaults.update(_action_defaults(action_context))

    values = {}
    missing = []
    for name in required_names:
        field = Model._fields[name]
        value = defaults.get(name)
        if value in (None, False, ""):
            value = _simple_value(env_obj, Model._name, name, field, token)
        if value in (None, False, "") and getattr(field, "type", "") not in {"boolean"}:
            missing.append(name)
        else:
            values[name] = value

    for name, value in defaults.items():
        field = Model._fields.get(name)
        if field and _is_writable_field(field) and getattr(field, "type", "") not in {"one2many", "many2many"}:
            values.setdefault(name, value)
    return values, sorted(set(missing))


def _write_payload(Model, record, token: str) -> tuple[dict, str]:
    for name in WRITE_FIELD_PREFERENCE:
        field = Model._fields.get(name)
        if not field or not _is_formal_write_probe_field(name, field):
            continue
        return {name: _write_value(Model.env, Model._name, name, field, record, token)}, name
    for name, field in Model._fields.items():
        if _is_formal_write_probe_field(name, field):
            return {name: _write_value(Model.env, Model._name, name, field, record, token)}, name
    return {}, ""


def _is_formal_write_probe_field(name: str, field) -> bool:
    if name in WRITE_FIELD_BLOCK_NAMES or any(name.startswith(prefix) for prefix in WRITE_FIELD_BLOCK_PREFIXES):
        return False
    return _is_writable_field(field) and getattr(field, "type", "") in {
        "char",
        "text",
        "html",
        "date",
        "datetime",
        "float",
        "monetary",
        "integer",
        "boolean",
        "selection",
        "many2one",
    }


def _write_value(env_obj, model_name: str, field_name: str, field, record, token: str):
    current = record[field_name] if record and field_name in record else None
    field_type = getattr(field, "type", "")
    if field_type == "many2one":
        return current.id if current else _many2one_value(env_obj, field)
    if current not in (None, False, ""):
        return current
    return _simple_value(env_obj, model_name, field_name, field, token)


def _menu_action(env_obj, menu_xmlid: str):
    menu = env_obj.ref(menu_xmlid, raise_if_not_found=False)
    action = menu.action if menu and menu.action and menu.action._name == "ir.actions.act_window" else None
    return menu, action


def _run_create_write_smoke(env_obj, Model, action, token: str) -> dict:
    action_context = _safe_context(action)
    ProbeModel = Model.with_context(**action_context)
    values, missing = _build_create_values(env_obj, ProbeModel, action_context, token)
    result = {
        "create_status": "fail",
        "write_status": "fail",
        "create_values": sorted(values),
        "missing_required_fields": missing,
        "write_field": "",
        "error": "",
    }
    if missing:
        result["error"] = "missing required values: %s" % ", ".join(missing)
        return result
    try:
        with env_obj.cr.savepoint():
            record = ProbeModel.create(values)
            result["create_status"] = "pass"
            payload, field_name = _write_payload(ProbeModel, record, token)
            result["write_field"] = field_name
            if not payload:
                result["error"] = "no writable char/text/html field found"
                raise SmokeRollback()
            record.write(payload)
            result["write_status"] = "pass"
            result["created_id"] = record.id
            raise SmokeRollback()
    except SmokeRollback:
        return result
    except Exception as exc:
        result["error"] = repr(exc)
        return result
    return result


def _run_existing_write_smoke(env_obj, Model, action, token: str) -> dict:
    domain = _safe_domain(action)
    result = {"status": "skip", "record_id": 0, "write_field": "", "error": ""}
    try:
        record = Model.with_context(active_test=False).search(domain, limit=1)
    except Exception:
        record = Model.with_context(active_test=False).search([], limit=1)
    if not record:
        result["error"] = "no existing record"
        return result
    try:
        with env_obj.cr.savepoint():
            payload, field_name = _write_payload(Model, record, token)
            result["write_field"] = field_name
            if not payload:
                result["status"] = "fail"
                result["error"] = "no writable char/text/html field found"
                raise SmokeRollback()
            record.write(payload)
            result["status"] = "pass"
            result["record_id"] = record.id
            raise SmokeRollback()
    except SmokeRollback:
        return result
    except Exception as exc:
        result["status"] = "fail"
        result["error"] = repr(exc)
        return result
    return result


def _access(Model) -> dict:
    result = {}
    for op in ("read", "create", "write"):
        try:
            result[op] = bool(Model.check_access_rights(op, raise_exception=False))
        except AccessError:
            result[op] = False
    return result


def _audit_spec(env_obj, spec: dict) -> dict:
    token = uuid.uuid4().hex[:8]
    menu, action = _menu_action(env_obj, spec["menu_xmlid"])
    issues = []
    model_name = _text(action.res_model) if action else ""
    if not menu:
        issues.append("menu_missing")
    elif not menu.active:
        issues.append("menu_inactive")
    if not action:
        issues.append("act_window_missing")
    else:
        action_context = _safe_context(action)
        if action_context.get("create") is False:
            issues.append("action_create_disabled")
        if _domain_references_history(action):
            issues.append("action_domain_history_scoped")
    if model_name not in env_obj:
        issues.append("model_missing")
        model_name = ""

    access = _access(env_obj[model_name]) if model_name else {"read": False, "create": False, "write": False}
    for op, ok in access.items():
        if not ok:
            issues.append("access_%s_missing" % op)

    create_write = {}
    existing_write = {}
    if not issues and model_name:
        Model = env_obj[model_name].with_context(active_test=False)
        create_write = _run_create_write_smoke(env_obj, Model, action, token)
        existing_write = _run_existing_write_smoke(env_obj, Model, action, token)
        if create_write.get("create_status") != "pass":
            issues.append("create_smoke_failed")
        if create_write.get("write_status") != "pass":
            issues.append("created_record_write_smoke_failed")
        if existing_write.get("status") == "fail":
            issues.append("existing_record_write_smoke_failed")

    return {
        **spec,
        "status": "pass" if not issues else "fail",
        "issues": sorted(set(issues)),
        "menu_id": int(menu.id) if menu else 0,
        "action_id": int(action.id) if action else 0,
        "action_xmlid": _xmlid(env_obj, action) if action else "",
        "model": model_name,
        "access": access,
        "create_write_smoke": create_write,
        "existing_write_smoke": existing_write,
    }


def _escape(value) -> str:
    return _text(value).replace("|", "\\|")


def _render_markdown(payload: dict) -> str:
    lines = [
        "# 正式办理核心流程新增编辑 Smoke V1",
        "",
        "本门禁抽取核心正式办理入口，以菜单动作运行上下文执行 ORM 新增与编辑，并在事务 savepoint 内回滚，验证历史数据进入正式模型后仍能按正式业务继续维护。",
        "",
        "## 摘要",
        "",
        f"- 数据库：`{payload['database']}`",
        f"- 核心流程：`{payload['summary']['flow_count']}`",
        f"- 通过：`{payload['summary']['pass_count']}`",
        f"- 失败：`{payload['summary']['fail_count']}`",
        f"- issue 分布：`{json.dumps(payload['summary']['issue_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## 结果",
        "",
        "| 入口 | 模型 | 新增 | 新增后编辑 | 既有记录编辑 | 写字段 | 问题 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        create_write = row.get("create_write_smoke") or {}
        existing_write = row.get("existing_write_smoke") or {}
        lines.append("| %s | `%s` | `%s` | `%s` | `%s` | `%s` | %s |" % (
            _escape(row.get("label")),
            _escape(row.get("model")),
            _escape(create_write.get("create_status")),
            _escape(create_write.get("write_status")),
            _escape(existing_write.get("status")),
            _escape(create_write.get("write_field") or existing_write.get("write_field")),
            _escape(", ".join(row.get("issues") or []) or "PASS"),
        ))
        error = _text(create_write.get("error") or existing_write.get("error"))
        if error:
            lines.append("|  |  |  |  |  |  | `%s` |" % _escape(error[:240]))
    return "\n".join(lines) + "\n"


def main() -> int:
    env_obj = globals()["env"]
    rows = [_audit_spec(env_obj, spec) for spec in CORE_FLOW_SPECS]
    issue_counter = Counter(issue for row in rows for issue in row.get("issues", []))
    failed = [row for row in rows if row.get("status") != "pass"]
    payload = {
        "schema_version": "formal_business_operation_core_flow_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": env_obj.cr.dbname,
        "summary": {
            "flow_count": len(rows),
            "pass_count": len(rows) - len(failed),
            "fail_count": len(failed),
            "issue_counts": dict(sorted(issue_counter.items())),
        },
        "rows": rows,
    }
    artifact_path = _write(ARTIFACT_PATH, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    report_path = _write(REPORT_PATH, _render_markdown(payload))
    env_obj.cr.rollback()
    print(json.dumps({
        "status": "PASS" if not failed else "FAIL",
        "artifact": str(artifact_path),
        "report": str(report_path),
        **payload["summary"],
    }, ensure_ascii=False, sort_keys=True))
    if failed:
        raise AssertionError("formal business operation core flow smoke failed: %s" % payload["summary"]["issue_counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
