#!/usr/bin/env python3
"""Project direct-project SCBSLY gap rows into existing business carriers.

The source is the direct-project overlay, not the SCBS55 baseline.  Every row is
tagged with an ``online_old_scbsly:*`` source so this can add data beside 55
coverage without replacing or relabeling prior replay records.
"""

from __future__ import annotations

import gzip
import json
import os
import zlib
from pathlib import Path
from typing import Any


FULL_ROWS_DIR = Path(os.getenv("SCBSLY_DIRECT_FULL_ROWS_DIR", "/mnt/artifacts/migration/scbsly_direct_20260530/full_rows"))
OUTPUT_JSON_NAME = "scbsly_direct_project_gap_projection_write_result_v1.json"


SPECS: list[dict[str, Any]] = [
    {"table": "CGXBJ_CGXJD", "menu": "报价单", "model": "sc.material.rfq", "source_key": "legacy_fact"},
    {"table": "T_JS_CLJSD", "menu": "材料结算单", "model": "sc.material.settlement", "source_key": "legacy_fact"},
    {"table": "LW_Base_FDGL", "menu": "方单", "model": "sc.labor.request", "source_key": "legacy_fact"},
    {"table": "SGGL_LWGL_LXYG", "menu": "零星用工", "model": "sc.labor.usage", "source_key": "legacy_fact"},
    {"table": "SGGL_FBGL_FBFD", "menu": "分包方单", "model": "sc.subcontract.register", "source_key": "legacy_fact"},
    {"table": "T_ZL_MachineShift", "menu": "机械台班记录", "model": "sc.equipment.usage", "source_key": "legacy_fact"},
    {"table": "T_ZL_ZRD", "menu": "租入", "model": "sc.material.rental.order", "source_key": "legacy_fact"},
    {"table": "T_ZL_HZD", "menu": "还租", "model": "sc.material.rental.order", "source_key": "legacy_fact"},
    {"table": "T_ZL_ZLJSD", "menu": "租赁结算单", "model": "sc.material.rental.settlement", "source_key": "legacy_fact"},
    {"table": "T_ZL_ZLJSD_JX", "menu": "租赁结算单", "model": "sc.material.rental.settlement", "source_key": "legacy_fact"},
    {"table": "GLFY_GLRYGZB", "menu": "管理人员工资表", "model": "sc.hr.payroll.document", "source_key": "legacy_source"},
    {"table": "D_LYXM_BG_BX_YKDJ", "menu": "油卡登记", "model": "sc.fund.account.operation", "source_key": "legacy_source"},
    {"table": "D_LYXM_BG_BX_CZDJ", "menu": "充值登记", "model": "sc.fund.account.operation", "source_key": "legacy_source"},
    {"table": "D_LYXM_BG_BX_JYDJ", "menu": "加油登记", "model": "sc.fund.account.operation", "source_key": "legacy_source"},
    {"table": "D_LYXM_XMGL_XM_GCJSD", "menu": "工程结算单", "model": "sc.settlement.order", "source_key": "legacy_fact"},
]


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def clean(value: Any) -> str:
    return str(value or "").strip()


def first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return ""


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def to_date(value: Any):
    text = clean(value)
    return text[:10] if len(text) >= 10 else False


def source_model(table: str) -> str:
    return f"online_old_scbsly:{table}"


def row_id(row: dict[str, Any]) -> str:
    detail_keys = sorted(key for key in row if key.startswith(("Id$", "ID$")))
    return clean(first(row, *detail_keys)) or clean(first(row, "Id", "ID", "id", "DJBH")) or clean(row.get("RowIndex"))


def legacy_fact_id(table: str, row: dict[str, Any]) -> int:
    token = f"{table}:{row_id(row)}".encode("utf-8")
    return zlib.crc32(token) & 0x7FFFFFFF


def safe_vals(model_name: str, vals: dict[str, Any]) -> dict[str, Any]:
    fields = env[model_name]._fields  # noqa: F821
    return {key: value for key, value in vals.items() if key in fields}


def project_id(cache: dict[str, int | bool], row: dict[str, Any]):
    legacy_id = clean(first(row, "XMID", "f_XMID"))
    name = clean(first(row, "XMMC", "ProjectName", "f_GCMC"))
    key = legacy_id or "__name__:" + name
    if key in cache:
        return cache[key]
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    project = False
    if legacy_id:
        project = Project.search([("legacy_project_id", "=", legacy_id)], limit=1)
    if not project and name:
        project = Project.search([("name", "=", name)], limit=1)
    if not project:
        project = Project.search([], order="id", limit=1)
    cache[key] = project.id if project else False
    return cache[key]


def partner_id(cache: dict[str, int | bool], name: Any, supplier: bool = False):
    key = clean(name) or ("旧系统未填供应商" if supplier else "")
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


def user_id(cache: dict[str, int | bool], legacy_id: Any, name: Any):
    legacy = clean(legacy_id)
    label = clean(name)
    key = legacy or "__name__:" + label
    if key in cache:
        return cache[key]
    user = False
    if legacy:
        profile = env["sc.legacy.user.profile"].sudo().search([("legacy_user_id", "=", legacy)], limit=1)  # noqa: F821
        user = profile.user_id if profile else False
    if not user and label:
        user = env["res.users"].sudo().with_context(active_test=False).search([("name", "=", label)], limit=1)  # noqa: F821
    cache[key] = user.id if user else False
    return cache[key]


def note_for(table: str, menu: str, row: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"旧系统直营项目菜单数据补充：{menu}",
            f"source_table={table}",
            f"legacy_record_id={row_id(row)}",
            f"legacy_document_no={clean(first(row, 'DJBH', 'f_ZRDH', 'f_HZDH'))}",
            f"legacy_document_state={clean(row.get('DJZT'))}",
            f"legacy_project_id={clean(first(row, 'XMID', 'f_XMID'))}",
            f"legacy_project_name={clean(first(row, 'XMMC', 'ProjectName', 'f_GCMC'))}",
            f"legacy_payload={json.dumps(row, ensure_ascii=False, sort_keys=True)}",
        ]
    )


def exists(model_name: str, spec: dict[str, Any], table: str, row: dict[str, Any]):
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if spec["source_key"] == "legacy_source":
        domain = [("legacy_source_table", "=", table), ("legacy_source_id", "=", row_id(row))]
        if "legacy_source_model" in Model._fields:
            domain = [("legacy_source_model", "=", source_model(table)), ("legacy_record_id" if "legacy_record_id" in Model._fields else "legacy_source_id", "=", row_id(row))]
        return Model.search(domain, limit=1)
    return Model.search([("legacy_fact_model", "=", source_model(table)), ("legacy_fact_id", "=", legacy_fact_id(table, row))], limit=1)


def base_legacy_vals(model_name: str, spec: dict[str, Any], table: str, row: dict[str, Any]) -> dict[str, Any]:
    if spec["source_key"] == "legacy_source":
        return safe_vals(
            model_name,
            {
                "legacy_source_model": source_model(table),
                "legacy_source_table": table,
                "legacy_record_id": row_id(row),
                "legacy_source_id": row_id(row),
                "legacy_document_state": clean(row.get("DJZT")),
                "legacy_document_no": clean(first(row, "DJBH", "f_ZRDH", "f_HZDH")),
                "creator_legacy_user_id": clean(first(row, "LRRID", "CZRID", "DJRID", "ZYGLRID")),
                "creator_name": clean(first(row, "LRR", "CZR", "DJR", "ZYGLR")),
                "created_time": clean(row.get("LRSJ")) or False,
            },
        )
    return safe_vals(
        model_name,
        {
            "legacy_fact_model": source_model(table),
            "legacy_fact_id": legacy_fact_id(table, row),
            "legacy_fact_type": f"direct_project:{spec['menu']}",
        },
    )


def vals_for(spec: dict[str, Any], row: dict[str, Any], caches: dict[str, dict[str, int | bool]]) -> dict[str, Any]:
    table = spec["table"]
    menu = spec["menu"]
    model = spec["model"]
    project = project_id(caches["project"], row)
    partner_name = first(row, "XJDW", "GYDW", "f_LWDW", "SGDWMC", "FBS", "ZLDW", "f_SupplierName", "JSDW", "D_LYXM_SKDWMC", "FBR")
    partner = partner_id(caches["partner"], partner_name, supplier=True)
    doc_no = clean(first(row, "DJBH", "f_ZRDH", "f_HZDH")) or f"{menu}-{row_id(row)}"
    date = to_date(first(row, "DJRQ", "XJSJ", "JSRQ", "f_LRSJ", "LRSJ", "f_DJRQ", "CZRQ", "JYRQ"))
    note = note_for(table, menu, row)
    vals: dict[str, Any]

    if model == "sc.material.rfq":
        vals = {"name": doc_no, "project_id": project, "selected_supplier_id": partner, "rfq_date": date, "contact_name": clean(row.get("LXR")), "contact_phone": clean(row.get("LXDH")), "state": "draft", "note": note}
    elif model == "sc.material.settlement":
        vals = {"name": doc_no, "project_id": project, "supplier_id": partner, "settlement_date": date, "state": "draft", "note": note}
    elif model == "sc.labor.request":
        vals = {"name": doc_no, "project_id": project, "request_date": date, "contractor_id": partner, "state": "draft", "note": note}
    elif model == "sc.labor.usage":
        vals = {
            "name": doc_no,
            "project_id": project,
            "usage_date": date,
            "labor_team": clean(first(row, "SGDWMC", "ZRDW", "SGY$SGGL_LWGL_LXYG_CB")) or "旧系统班组",
            "contractor_id": partner,
            "work_content": clean(first(row, "SGNR$SGGL_LWGL_LXYG_CB", "BZ", "BT")) or "旧系统零星用工",
            "worker_qty": to_float(first(row, "RS$SGGL_LWGL_LXYG_CB"), 1.0) or 1.0,
            "work_hours": to_float(first(row, "GSHJ$SGGL_LWGL_LXYG_CB", "GRHJ$SGGL_LWGL_LXYG_CB"), 1.0),
            "foreman_name": clean(first(row, "ZDR", "LRR")),
            "state": "draft",
            "note": note,
        }
    elif model == "sc.subcontract.register":
        vals = {"name": doc_no, "project_id": project, "register_date": date, "subcontract_scope": clean(first(row, "FBNR", "BT", "BZ")) or "旧系统分包方单", "subcontractor_id": partner, "state": "draft", "note": note}
    elif model == "sc.equipment.usage":
        vals = {
            "name": doc_no,
            "project_id": project,
            "usage_date": date,
            "equipment_name": clean(first(row, "JXMC$T_ZL_MachineShift_CB", "BZ")) or "旧系统机械",
            "equipment_code": clean(row.get("JXID$T_ZL_MachineShift_CB")),
            "usage_location": clean(first(row, "SGBW", "SGBW$T_ZL_MachineShift_CB", "XMMC")) or "旧系统施工部位",
            "operator_name": clean(first(row, "D_LYXM_CYM", "LRR")) or "旧系统操作员",
            "usage_qty": 1.0,
            "usage_hours": to_float(first(row, "GZSJ$T_ZL_MachineShift_CB"), 1.0) or 1.0,
            "supplier_id": partner,
            "state": "draft",
            "note": note,
        }
    elif model == "sc.material.rental.order":
        vals = {"name": doc_no, "project_id": project, "supplier_id": partner, "rental_date": date, "state": "returned" if table == "T_ZL_HZD" else "draft", "note": note}
    elif model == "sc.material.rental.settlement":
        vals = {"name": doc_no, "project_id": project, "supplier_id": partner, "settlement_date": date, "state": "draft", "note": note}
    elif model == "sc.hr.payroll.document":
        amount = to_float(first(row, "BCSFGZZE", "BCYFGZZE"))
        vals = {"name": doc_no, "fact_type": "salary_registration", "project_id": project, "business_date": date, "amount": amount, "gross_amount": amount, "net_salary": amount, "legacy_document_no": doc_no, "legacy_document_state": clean(row.get("DJZT")), "legacy_source_table": table, "legacy_source_id": row_id(row), "legacy_visible_note": note}
    elif model == "sc.fund.account.operation":
        amount = to_float(first(row, "CSJE", "CZZE", "JYJE"))
        vals = {
            "name": doc_no,
            "operation_type": "balance_adjustment",
            "operation_date": date,
            "project_id": project,
            "amount": amount,
            "before_balance": 0.0,
            "after_balance": amount if table != "D_LYXM_BG_BX_JYDJ" else 0.0,
            "operation_reason": f"{menu}:{clean(first(row, 'YKKH', 'CZKH$D_LYXM_BG_BX_CZDJCB', 'JYKH', 'BZ')) or doc_no}",
            "state": "draft",
            "note": note,
        }
        if vals["before_balance"] == vals["after_balance"]:
            vals["after_balance"] = vals["before_balance"] + amount + 0.01
    elif model == "sc.settlement.order":
        customer = partner_id(caches["partner"], first(row, "FBR", "CBR"), supplier=False)
        vals = {
            "name": doc_no,
            "project_id": project,
            "partner_id": customer,
            "settlement_unit_id": customer,
            "legacy_counterparty_name": clean(first(row, "FBR", "CBR")),
            "title": clean(first(row, "BT", "HTMC")) or doc_no,
            "document_date": date,
            "settlement_type": "in",
            "settlement_stage": "final",
            "date_settlement": date,
            "approved_amount": to_float(first(row, "SDJE", "SSJE", "JSJE")),
            "submitted_amount": to_float(first(row, "SSJE", "JSJE")),
            "state": "draft",
            "settlement_description": note,
        }
    else:
        raise RuntimeError(f"unsupported model: {model}")

    vals.update(base_legacy_vals(model, spec, table, row))
    handler = user_id(caches["user"], first(row, "LRRID", "CZRID", "DJRID"), first(row, "LRR", "CZR", "DJR"))
    if handler:
        vals.update(safe_vals(model, {"owner_id": handler, "requester_id": handler, "recorder_id": handler, "entry_user_id": handler, "handler_id": handler}))
    return safe_vals(model, vals)


def load_rows(spec: dict[str, Any]) -> list[dict[str, Any]]:
    pattern = f"scbsly_direct_full_rows_{spec['table']}_{spec['menu']}_*.json.gz"
    paths = sorted(FULL_ROWS_DIR.glob(pattern))
    if not paths:
        return []
    with gzip.open(paths[0], "rt", encoding="utf-8") as handle:
        return json.load(handle).get("rows") or []


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",") if item.strip()}  # noqa: F821
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_direct_projection": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


ensure_allowed_db()
caches = {"project": {}, "partner": {}, "user": {}}
results: list[dict[str, Any]] = []
rebuild = os.getenv("SCBSLY_DIRECT_REBUILD") == "1"

for spec in SPECS:
    model_name = spec["model"]
    rows = load_rows(spec)
    created = 0
    skipped_existing = 0
    blocked = 0
    errors: list[dict[str, str]] = []
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if rebuild:
        with env.cr.savepoint():  # noqa: F821
            if spec["source_key"] == "legacy_source":
                if "legacy_source_model" in Model._fields:
                    Model.search([("legacy_source_model", "=", source_model(spec["table"]))]).unlink()
                else:
                    Model.search([("legacy_source_table", "=", spec["table"])]).unlink()
            else:
                Model.search([("legacy_fact_model", "=", source_model(spec["table"]))]).unlink()
    for row in rows:
        try:
            with env.cr.savepoint():  # noqa: F821
                if exists(model_name, spec, spec["table"], row):
                    skipped_existing += 1
                    continue
                vals = vals_for(spec, row, caches)
                if "project_id" in Model._fields and not vals.get("project_id") and Model._fields["project_id"].required:
                    blocked += 1
                    errors.append({"id": row_id(row), "error": "missing_required_project"})
                    continue
                Model.create(vals)
                created += 1
        except Exception as exc:  # noqa: BLE001
            blocked += 1
            if len(errors) < 20:
                errors.append({"id": row_id(row), "error": repr(exc)})
    results.append(
        {
            "table": spec["table"],
            "menu": spec["menu"],
            "model": model_name,
            "source_model": source_model(spec["table"]),
            "input_rows": len(rows),
            "created": created,
            "skipped_existing": skipped_existing,
            "blocked": blocked,
            "errors": errors,
        }
    )

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if all(not item["blocked"] and item["input_rows"] for item in results) else "REVIEW",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "scbsly_direct_project_gap_projection_write",
    "full_rows_dir": str(FULL_ROWS_DIR),
    "results": results,
    "created_total": sum(item["created"] for item in results),
    "skipped_existing_total": sum(item["skipped_existing"] for item in results),
    "blocked_total": sum(item["blocked"] for item in results),
    "source_boundary": "online_old_scbsly overlay only; SCBS55 sources are not overwritten",
}
out = artifact_root() / OUTPUT_JSON_NAME
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("SCBSLY_DIRECT_PROJECT_GAP_PROJECTION_WRITE=" + json.dumps({key: payload[key] for key in ("status", "database", "created_total", "skipped_existing_total", "blocked_total")}, ensure_ascii=False, sort_keys=True))
