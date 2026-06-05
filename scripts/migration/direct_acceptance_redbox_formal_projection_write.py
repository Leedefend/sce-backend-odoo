#!/usr/bin/env python3
"""Project accepted direct-project red-box data into formal business models.

Run dry-run first:
    DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo \
      bash scripts/ops/odoo_shell_exec.sh < scripts/migration/direct_acceptance_redbox_formal_projection_write.py

Apply:
    DB_NAME=sc_demo MIGRATION_REPLAY_DB_ALLOWLIST=sc_demo DIRECT_ACCEPTANCE_REDBOX_APPLY=1 \
      bash scripts/ops/odoo_shell_exec.sh < scripts/migration/direct_acceptance_redbox_formal_projection_write.py
"""

from __future__ import annotations

import json
import os
import re
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any


SOURCE_SYSTEM = "online_old_scbsly"
SOURCE_FACT_MODEL = "online_old_scbsly:direct_acceptance_fact"
SOURCE_DIRECT_MODEL = "online_old_scbsly:direct_acceptance"
OUTPUT_JSON_NAME = "direct_acceptance_redbox_formal_projection_write_result_v1.json"
APPLY = os.getenv("DIRECT_ACCEPTANCE_REDBOX_APPLY") == "1"
LIMIT = int(os.getenv("DIRECT_ACCEPTANCE_REDBOX_LIMIT", "0") or "0")
UPDATE_EXISTING = os.getenv("DIRECT_ACCEPTANCE_REDBOX_UPDATE_EXISTING") == "1"


SPECS: dict[str, dict[str, Any]] = {
    "材料计划": {"model": "project.material.plan", "mode": "legacy_fact"},
    "报价单": {"model": "sc.material.rfq", "mode": "legacy_fact"},
    "入库": {"model": "sc.material.inbound", "mode": "legacy_fact"},
    "方单": {"model": "sc.labor.usage", "mode": "legacy_fact"},
    "零星用工": {"model": "sc.labor.usage", "mode": "legacy_fact"},
    "分包方单": {"model": "sc.subcontract.request", "mode": "legacy_fact"},
    "机械台班记录": {"model": "sc.equipment.usage", "mode": "legacy_fact"},
    "租入": {"model": "sc.material.rental.order", "mode": "legacy_fact"},
    "还租": {"model": "sc.material.rental.order", "mode": "legacy_fact"},
    "管理人员工资表": {"model": "sc.hr.payroll.document", "mode": "legacy_source"},
    "油卡登记": {"model": "sc.fund.account.operation", "mode": "legacy_source"},
    "充值登记": {"model": "sc.fund.account.operation", "mode": "legacy_source"},
    "施工日志（新）": {"model": "sc.construction.diary", "mode": "legacy_source"},
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/direct_acceptance_redbox/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_acceptance_redbox/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_redbox_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def clean(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def money(value: Any) -> float:
    raw = clean(value).replace(",", "").replace("￥", "").replace("¥", "")
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    return float(match.group(0)) if match else 0.0


def date_value(value: Any):
    raw = clean(value).replace("/", "-")
    if not raw:
        return False
    for fmt, size in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(raw[:size], fmt).date().isoformat()
        except ValueError:
            continue
    return False


def datetime_value(value: Any):
    raw = clean(value).replace("/", "-")
    if not raw:
        return False
    for fmt, size in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(raw[:size], fmt).isoformat(sep=" ")
        except ValueError:
            continue
    return False


def payload_of(fact) -> dict[str, Any]:
    try:
        payload = json.loads(fact.raw_payload or "{}")
    except (TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def first_payload(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = clean(payload.get(key))
        if value:
            return value
    return ""


def visible(fact, index: int) -> str:
    return clean(getattr(fact, f"legacy_visible_{index:02d}", ""))


def source_key(label: str, fact) -> int:
    token = f"{SOURCE_SYSTEM}:{label}:{fact.legacy_record_id or fact.id}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def legacy_fact_domain(label: str, fact) -> list[tuple[str, str, Any]]:
    return [
        ("legacy_fact_model", "=", SOURCE_FACT_MODEL),
        ("legacy_fact_id", "=", source_key(label, fact)),
    ]


def legacy_source_domain(label: str, fact) -> list[tuple[str, str, Any]]:
    if label == "管理人员工资表":
        return [
            ("legacy_source_table", "=", "direct_acceptance:管理人员工资表"),
            ("legacy_source_id", "=", clean(fact.legacy_record_id) or str(fact.id)),
        ]
    return [
        ("legacy_source_model", "=", SOURCE_DIRECT_MODEL),
        ("legacy_record_id", "=", f"{label}:{fact.legacy_record_id or fact.id}"),
    ]


def safe_vals(model_name: str, vals: dict[str, Any]) -> dict[str, Any]:
    fields = env[model_name]._fields  # noqa: F821
    return {key: value for key, value in vals.items() if key in fields and value not in (None, "")}


def project_id(cache: dict[str, int | bool], fact, payload: dict[str, Any]):
    if fact.project_id:
        return fact.project_id.id
    legacy_id = clean(fact.project_legacy_id) or first_payload(payload, "XMID", "f_XMID")
    name = clean(fact.project_name) or first_payload(payload, "XMMC", "ProjectName", "f_GCMC")
    key = legacy_id or "__name__:" + name
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = Project.search([("legacy_project_id", "=", legacy_id)], limit=1) if legacy_id else False
    if not project and name:
        project = Project.search([("name", "=", name)], limit=1)
    if not project:
        project = Project.search([], order="id", limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def partner_id(cache: dict[str, int | bool], name: Any, supplier: bool = True):
    key = clean(name) or ("旧系统未填单位" if supplier else "")
    if not key:
        return False
    if key in cache:
        return cache[key]
    Partner = env["res.partner"].sudo().with_context(active_test=False)  # noqa: F821
    partner = Partner.search([("name", "=", key)], limit=1)
    vals = {"name": key}
    if supplier:
        vals["supplier_rank"] = 1
    if not partner:
        partner = Partner.create(vals)
    elif supplier and partner.supplier_rank <= 0:
        partner.write({"supplier_rank": 1})
    cache[key] = partner.id
    return cache[key]


def default_product_id() -> int | bool:
    Product = env["product.product"].sudo()  # noqa: F821
    product = Product.search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)
    if not product:
        product = Product.create({"name": "系统默认材料（技术占位）", "default_code": "SC-SYSTEM-DEFAULT-MATERIAL", "type": "product"})
    return product.id


def note_for(label: str, fact, payload: dict[str, Any]) -> str:
    visible_lines = []
    for index in range(1, 61):
        value = visible(fact, index)
        if value:
            visible_lines.append(f"{index:02d}: {value}")
    return "\n".join(
        [
            f"直营项目用户验收合格数据迁入正式业务模型：{label}",
            f"source_system={SOURCE_SYSTEM}",
            f"legacy_record_id={clean(fact.legacy_record_id)}",
            f"document_no={clean(fact.document_no)}",
            f"attachment_ref={clean(fact.attachment_ref)}",
            "验收面可见字段:",
            *visible_lines,
            "raw_payload=" + json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ]
    )


def base_vals(label: str, model_name: str, fact, payload: dict[str, Any]) -> dict[str, Any]:
    vals: dict[str, Any] = {
        "legacy_acceptance_label": label,
        "source_created_by": clean(fact.creator_name),
        "source_created_at": fact.created_time or datetime_value(first_payload(payload, "LRSJ", "LRRQ", "f_LRSJ")),
        "creator_name": clean(fact.creator_name),
        "creator_legacy_user_id": clean(fact.creator_legacy_user_id),
        "created_time": fact.created_time or datetime_value(first_payload(payload, "LRSJ", "LRRQ", "f_LRSJ")),
        "legacy_document_state": clean(fact.document_state) or visible(fact, 1),
        "legacy_document_no": clean(fact.document_no),
        "legacy_attachment_ref": clean(fact.attachment_ref),
        "legacy_visible_attachment": clean(fact.attachment_ref) or "历史附件" if clean(fact.attachment_ref) else "",
    }
    if SPECS[label]["mode"] == "legacy_fact":
        vals.update(
            {
                "legacy_fact_model": SOURCE_FACT_MODEL,
                "legacy_fact_id": source_key(label, fact),
                "legacy_fact_type": f"direct_acceptance:{label}",
            }
        )
    else:
        vals.update(
            {
                "legacy_source_model": SOURCE_DIRECT_MODEL,
                "legacy_source_table": f"direct_acceptance:{label}",
                "legacy_source_id": clean(fact.legacy_record_id) or str(fact.id),
                "legacy_record_id": f"{label}:{fact.legacy_record_id or fact.id}",
            }
        )
    for index in range(1, 61):
        vals[f"legacy_visible_{index:02d}"] = visible(fact, index)
    return safe_vals(model_name, vals)


def line_qty(*values: Any) -> float:
    for value in values:
        amount = money(value)
        if amount > 0:
            return amount
    return 1.0


def vals_for(label: str, fact, caches: dict[str, dict[str, int | bool]]) -> dict[str, Any]:
    payload = payload_of(fact)
    model_name = SPECS[label]["model"]
    project = project_id(caches["project"], fact, payload)
    doc_no = clean(fact.document_no) or visible(fact, 2) or f"{label}-{fact.legacy_record_id or fact.id}"
    date = date_value(fact.document_date) or date_value(visible(fact, 3)) or date_value(first_payload(payload, "DJRQ", "RQ", "f_DJRQ", "XJSJ"))
    note = note_for(label, fact, payload)
    partner = partner_id(
        caches["partner"],
        clean(fact.partner_name)
        or first_payload(payload, "SupplierName", "XJDW", "SGDWMC", "FBS", "ZLDW", "f_SupplierName", "SGDWMC", "f_LWDW"),
    )

    if label == "材料计划":
        vals = {
            "name": doc_no,
            "project_id": project,
            "date_plan": date,
            "state": "draft",
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": default_product_id(),
                        "material_name": visible(fact, 5) or first_payload(payload, "f_CLMC$T_JH_XMZJH"),
                        "spec": visible(fact, 6) or first_payload(payload, "f_GGXH$T_JH_XMZJH"),
                        "material_uom_text": visible(fact, 7) or first_payload(payload, "f_DW$T_JH_XMZJH"),
                        "quantity": line_qty(visible(fact, 8), first_payload(payload, "f_YSCBSL$T_JH_XMZJH")),
                        "note": visible(fact, 10) or clean(fact.note),
                    },
                )
            ],
        }
    elif label == "报价单":
        vals = {
            "name": doc_no,
            "project_id": project,
            "selected_supplier_id": partner,
            "rfq_date": date,
            "state": "draft",
            "note": note,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "supplier_id": partner,
                        "product_id": default_product_id(),
                        "material_spec": visible(fact, 6),
                        "qty": line_qty(visible(fact, 7)),
                        "unit_price": money(visible(fact, 8)),
                        "amount": money(visible(fact, 9)),
                        "note": visible(fact, 12),
                    },
                )
            ],
        }
    elif label == "入库":
        vals = {
            "name": doc_no,
            "project_id": project,
            "inbound_date": date,
            "supplier_id": partner,
            "state": "draft",
            "note": note,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": default_product_id(),
                        "material_spec": visible(fact, 6),
                        "qty": line_qty(visible(fact, 7), visible(fact, 11)),
                        "unit_price": money(visible(fact, 8)),
                        "note": visible(fact, 18),
                    },
                )
            ],
        }
    elif label in {"方单", "零星用工"}:
        vals = {
            "name": doc_no,
            "project_id": project,
            "usage_date": date,
            "labor_team": visible(fact, 6) or visible(fact, 5) or "旧系统班组",
            "contractor_id": partner,
            "work_content": visible(fact, 8) or visible(fact, 6) or clean(fact.document_title) or label,
            "worker_qty": line_qty(visible(fact, 7), visible(fact, 8)),
            "work_hours": line_qty(first_payload(payload, "GRHJ$SGGL_LWGL_LXYG_CB", "GSHJ$SGGL_LWGL_LXYG_CB"), visible(fact, 9)),
            "foreman_name": visible(fact, 12) or clean(fact.creator_name),
            "state": "draft",
            "note": note,
        }
    elif label == "分包方单":
        vals = {
            "name": doc_no,
            "project_id": project,
            "request_date": date,
            "subcontract_scope": visible(fact, 6) or visible(fact, 8) or clean(fact.document_title) or label,
            "suggested_subcontractor_id": partner,
            "state": "draft",
            "request_reason": note,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "work_scope": visible(fact, 8) or visible(fact, 6) or label,
                        "work_content": visible(fact, 8) or clean(fact.note),
                        "required_qty": line_qty(visible(fact, 9)),
                        "estimated_amount": money(visible(fact, 11)),
                        "note": visible(fact, 12),
                    },
                )
            ],
        }
    elif label == "机械台班记录":
        vals = {
            "name": doc_no,
            "project_id": project,
            "usage_date": date,
            "equipment_name": visible(fact, 7) or "旧系统机械",
            "equipment_code": first_payload(payload, "JXID$T_ZL_MachineShift_CB"),
            "usage_location": visible(fact, 6) or visible(fact, 2) or "旧系统施工部位",
            "operator_name": visible(fact, 6) or clean(fact.creator_name) or "旧系统操作员",
            "usage_qty": 1.0,
            "usage_hours": line_qty(visible(fact, 10)),
            "supplier_id": partner,
            "state": "draft",
            "note": note,
        }
    elif label in {"租入", "还租"}:
        vals = {
            "name": doc_no,
            "project_id": project,
            "supplier_id": partner,
            "rental_date": date,
            "state": "returned" if label == "还租" else "draft",
            "note": note,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "material_name": visible(fact, 6) or clean(fact.document_title) or label,
                        "material_spec": visible(fact, 7),
                        "unit_name": visible(fact, 8),
                        "qty": line_qty(visible(fact, 8)),
                        "daily_price": money(visible(fact, 9)),
                        "returned_qty": line_qty(visible(fact, 15)) if label == "还租" else 0.0,
                        "note": visible(fact, 12),
                    },
                )
            ],
        }
    elif label == "管理人员工资表":
        amount = money(visible(fact, 6)) or money(visible(fact, 7)) or fact.amount_total
        vals = {
            "name": doc_no,
            "fact_type": "salary_registration",
            "project_id": project,
            "business_date": date,
            "period_year": int((date or "1970")[:4]) if date else False,
            "period_month": int((date or "1970-01")[5:7]) if date else False,
            "employee_name": "管理人员工资表",
            "gross_amount": amount,
            "net_salary": amount,
            "amount": amount,
            "legacy_document_no": doc_no,
            "legacy_document_state": visible(fact, 1),
            "legacy_source_table": "direct_acceptance:管理人员工资表",
            "legacy_source_id": clean(fact.legacy_record_id) or str(fact.id),
            "legacy_visible_creator_name": clean(fact.creator_name),
            "legacy_visible_created_time": fact.created_time,
            "legacy_visible_note": note,
        }
    elif label in {"油卡登记", "充值登记"}:
        amount = money(visible(fact, 6)) if label == "油卡登记" else money(visible(fact, 6)) or money(visible(fact, 7))
        vals = {
            "name": doc_no,
            "operation_type": "balance_adjustment",
            "operation_date": date,
            "project_id": project,
            "amount": amount,
            "before_balance": 0.0,
            "after_balance": amount or 0.01,
            "operation_reason": f"{label}:{visible(fact, 5) or doc_no}",
            "state": "draft",
            "note": note,
            "legacy_visible_document_no": doc_no,
            "legacy_visible_project_name": visible(fact, 4),
            "legacy_visible_account_name": visible(fact, 5),
            "legacy_visible_reason": visible(fact, 8) or visible(fact, 9),
            "legacy_visible_note": visible(fact, 8) or visible(fact, 9),
        }
    elif label == "施工日志（新）":
        vals = {
            "name": doc_no,
            "source_origin": "legacy",
            "state": "legacy_confirmed",
            "project_id": project,
            "date_diary": datetime_value(fact.document_date) or datetime_value(visible(fact, 4)),
            "document_no": doc_no,
            "title": visible(fact, 5) or label,
            "construction_unit": visible(fact, 5),
            "manpower_count": int(money(visible(fact, 6))) if money(visible(fact, 6)) else 0,
            "description": visible(fact, 7) or visible(fact, 8) or note,
            "note": note,
            "legacy_source_model": SOURCE_DIRECT_MODEL,
            "legacy_source_table": "direct_acceptance:施工日志（新）",
            "legacy_record_id": f"{label}:{fact.legacy_record_id or fact.id}",
            "legacy_document_state": visible(fact, 1),
            "legacy_attachment_ref": clean(fact.attachment_ref),
        }
    else:
        raise RuntimeError({"unsupported_label": label})
    vals.update(base_vals(label, model_name, fact, payload))
    return safe_vals(model_name, vals)


def search_existing(label: str, model_name: str, fact):
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    domain = legacy_fact_domain(label, fact) if SPECS[label]["mode"] == "legacy_fact" else legacy_source_domain(label, fact)
    return Model.search(domain, limit=1)


def source_facts(label: str):
    return env["sc.legacy.direct.acceptance.fact"].sudo().search(  # noqa: F821
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
        order="document_no,legacy_record_id,id",
        limit=LIMIT or None,
    )


ensure_allowed_db()
caches = {"project": {}, "partner": {}}
results = []

for label, spec in SPECS.items():
    model_name = spec["model"]
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    facts = source_facts(label)
    created = updated = existing = blocked = 0
    errors = []
    for fact in facts:
        try:
            with env.cr.savepoint():  # noqa: F821
                vals = vals_for(label, fact, caches)
                if "project_id" in Model._fields and Model._fields["project_id"].required and not vals.get("project_id"):
                    blocked += 1
                    errors.append({"legacy_record_id": fact.legacy_record_id, "error": "missing_required_project"})
                    continue
                record = search_existing(label, model_name, fact)
                if record:
                    existing += 1
                    if APPLY and UPDATE_EXISTING:
                        scalar_vals = {
                            key: value
                            for key, value in vals.items()
                            if not (key.endswith("_ids") and isinstance(value, list))
                        }
                        record.write(scalar_vals)
                        updated += 1
                    continue
                if APPLY:
                    Model.create(vals)
                created += 1
        except Exception as exc:  # noqa: BLE001
            blocked += 1
            if len(errors) < 30:
                errors.append({"legacy_record_id": fact.legacy_record_id, "error": repr(exc)})
    formal_domain = [("legacy_fact_model", "=", SOURCE_FACT_MODEL), ("legacy_fact_type", "=", f"direct_acceptance:{label}")]
    if spec["mode"] == "legacy_source":
        if model_name == "sc.hr.payroll.document":
            formal_domain = [("legacy_source_table", "=", "direct_acceptance:管理人员工资表")]
        else:
            formal_domain = [("legacy_source_model", "=", SOURCE_DIRECT_MODEL), ("legacy_source_table", "=", f"direct_acceptance:{label}")]
    formal_count = Model.search_count(formal_domain)
    source_count = len(facts)
    projected_after = formal_count + (created if APPLY is False else 0)
    results.append(
        {
            "label": label,
            "model": model_name,
            "source_count": source_count,
            "formal_count": formal_count,
            "projected_after_dry_run_count": projected_after,
            "created": created,
            "existing": existing,
            "updated": updated,
            "blocked": blocked,
            "errors": errors,
            "status": "PASS" if not blocked and (APPLY and formal_count == source_count or (not APPLY and projected_after == source_count)) else "REVIEW",
        }
    )

if APPLY:
    env.cr.commit()  # noqa: F821
else:
    env.cr.rollback()  # noqa: F821

payload = {
    "status": "PASS" if all(item["status"] == "PASS" for item in results) else "REVIEW",
    "mode": "direct_acceptance_redbox_formal_projection_write",
    "apply": APPLY,
    "database": env.cr.dbname,  # noqa: F821
    "results": results,
}
out = artifact_root() / OUTPUT_JSON_NAME
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("DIRECT_ACCEPTANCE_REDBOX_FORMAL_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
