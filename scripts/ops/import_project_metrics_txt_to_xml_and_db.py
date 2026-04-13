#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROLLBACK_FILE = Path("tmp/customer_metrics_import.rollback.json")

RAW_FIELD_TO_TARGET: dict[str, dict[str, str]] = {
    "施工合同金额": {"model": "project.project", "field": "budget_total", "note": "primary"},
    "施工合同价_应收应付": {"model": "project.project", "field": "budget_total", "note": "fallback"},
    "进项上报金额": {"model": "project.project", "field": "cost_actual", "note": "primary"},
    "已付款": {"model": "project.project", "field": "cost_actual", "note": "fallback"},
    "已付款_应收应付": {"model": "project.project", "field": "cost_actual", "note": "fallback"},
    "收款金额": {"model": "project.project", "field": "plan_percent", "note": "derived with budget_total"},
    "工程进度收款": {"model": "project.project", "field": "actual_percent", "note": "derived with budget_total"},
    "已收款_应收应付": {"model": "project.project", "field": "actual_percent/plan_percent", "note": "derived fallback"},
    "材料合同": {"model": "project.cost.ledger", "field": "amount", "note": "component ledger"},
    "劳务合同": {"model": "project.cost.ledger", "field": "amount", "note": "component ledger"},
    "租赁合同": {"model": "project.cost.ledger", "field": "amount", "note": "component ledger"},
    "分包合同": {"model": "project.cost.ledger", "field": "amount", "note": "component ledger"},
    "其他合同": {"model": "project.cost.ledger", "field": "amount", "note": "component ledger"},
}


def _to_float(raw: Any) -> float | None:
    text = str(raw or "").strip()
    if not text:
        return None
    if text.endswith("%"):
        text = text[:-1]
    text = text.replace(",", "").strip()
    try:
        return float(text)
    except Exception:
        return None


def _pick_number(row: dict[str, str], keys: list[str]) -> float | None:
    for key in keys:
        value = _to_float(row.get(key, ""))
        if value is not None:
            return value
    return None


def _sum_numbers(row: dict[str, str], keys: list[str]) -> float | None:
    values = [_to_float(row.get(key, "")) for key in keys]
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return float(sum(valid))


def _compute_percent(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return round((numerator / denominator) * 100.0, 4)


def _read_txt_table(txt_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    lines = txt_path.read_text(encoding="utf-8").splitlines()
    candidates: list[tuple[int, int]] = []
    for idx, line in enumerate(lines):
        if line.startswith("项目名称\t"):
            col_count = len(line.split("\t"))
            candidates.append((idx, col_count))

    if not candidates:
        raise RuntimeError("未找到制表符表头：项目名称\\t...")

    header_index, header_col_count = max(candidates, key=lambda item: item[1])
    if header_col_count < 3:
        raise RuntimeError(f"检测到的表头列数异常：{header_col_count}")

    rows = lines[header_index:]
    reader = csv.reader(rows, delimiter="\t")
    header = next(reader)
    out: list[dict[str, str]] = []
    for row in reader:
        if not row:
            continue
        padded = row + [""] * (len(header) - len(row))
        record = {header[i]: str(padded[i]).strip() for i in range(len(header))}
        if not record.get("项目名称"):
            continue
        out.append(record)
    return header, out


def _build_import_rows(table_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in table_rows:
        name = str(row.get("项目名称") or "").strip()
        if not name:
            continue

        contract_amount = _pick_number(row, ["施工合同金额", "施工合同价_应收应付"])
        actual_cost = _pick_number(row, ["进项上报金额", "已付款", "已付款_应收应付"])
        collected = _pick_number(row, ["收款金额", "已收款_应收应付", "工程进度收款"])
        progress = _pick_number(row, ["工程进度收款", "已收款_应收应付", "收款金额"])

        cost_components = {
            "材料合同": _to_float(row.get("材料合同", "")),
            "劳务合同": _to_float(row.get("劳务合同", "")),
            "租赁合同": _to_float(row.get("租赁合同", "")),
            "分包合同": _to_float(row.get("分包合同", "")),
            "其他合同": _to_float(row.get("其他合同", "")),
        }
        committed_cost = _sum_numbers(row, ["材料合同", "劳务合同", "租赁合同", "分包合同", "其他合同"])

        actual_percent = _compute_percent(progress, contract_amount)
        plan_percent = _compute_percent(collected, contract_amount)

        metrics = {key: value for key, value in row.items() if str(value or "").strip()}
        description_payload = {
            "import_tag": "customer_metrics_import",
            "source": "项目业务关键信息提取.txt",
            "metrics": metrics,
            "mapped_fields": {
                "budget_total": contract_amount,
                "cost_actual": actual_cost,
                "cost_committed": committed_cost,
                "actual_percent": actual_percent,
                "plan_percent": plan_percent,
            },
        }

        out.append(
            {
                "name": name,
                "budget_total": contract_amount,
                "cost_actual": actual_cost,
                "cost_committed": committed_cost,
                "actual_percent": actual_percent,
                "plan_percent": plan_percent,
                "cost_components": cost_components,
                "description": json.dumps(description_payload, ensure_ascii=False),
            }
        )
    return out


def _build_gap_report(header: list[str], import_rows: list[dict[str, Any]]) -> dict[str, Any]:
    header_fields = [field for field in header if field and field != "项目名称"]

    def gap_reason(field_name: str) -> dict[str, str]:
        if "开票" in field_name or "税" in field_name:
            return {
                "reason_code": "NEEDS_ACCOUNTING_CONTEXT",
                "reason": "该字段属于发票/税务口径，现有导入任务未包含会计凭证上下文，无法安全直写业务事实模型。",
                "suggested_model": "account.move/account.move.line（需单独授权批次）",
            }
        if field_name in {"可用余额", "自筹垫付收入", "退回", "未退回"}:
            return {
                "reason_code": "DERIVED_FUNDING_FIELD",
                "reason": "该字段在现系统由资金基准/付款流程派生，不应直接写入结果字段。",
                "suggested_model": "project.funding.baseline + payment.request（需流程化导入）",
            }
        if field_name in {"利润额", "利润率", "收支结余", "成本差额"}:
            return {
                "reason_code": "COMPUTED_METRIC",
                "reason": "该字段属于聚合/计算指标，现有模型字段多为只读计算，不应直接落库覆盖。",
                "suggested_model": "project.project 计算链/投影报表模型",
            }
        return {
            "reason_code": "NO_SAFE_WRITABLE_TARGET",
            "reason": "当前授权范围内未发现可安全写入且语义等价的现有字段。",
            "suggested_model": "需新建映射任务明确目标模型与约束",
        }

    mapped_fields = []
    for field_name in header_fields:
        if field_name in RAW_FIELD_TO_TARGET:
            target = RAW_FIELD_TO_TARGET[field_name]
            mapped_fields.append(
                {
                    "source_field": field_name,
                    "target_model": target["model"],
                    "target_field": target["field"],
                    "note": target["note"],
                }
            )

    unmapped_fields = []
    for field_name in header_fields:
        if field_name in RAW_FIELD_TO_TARGET:
            continue
        details = gap_reason(field_name)
        unmapped_fields.append(
            {
                "source_field": field_name,
                **details,
            }
        )

    coverage = {
        "total_source_fields": len(header_fields),
        "mapped_source_fields": len(mapped_fields),
        "unmapped_source_fields": len(unmapped_fields),
        "import_rows": len(import_rows),
        "project_dispatch_rows": len(import_rows),
        "ledger_dispatch_rows_estimate": sum(
            1
            for row in import_rows
            for value in [
                row.get("cost_actual"),
                row.get("cost_components", {}).get("材料合同"),
                row.get("cost_components", {}).get("劳务合同"),
                row.get("cost_components", {}).get("租赁合同"),
                row.get("cost_components", {}).get("分包合同"),
                row.get("cost_components", {}).get("其他合同"),
            ]
            if value is not None
        ),
    }

    return {
        "source": "tmp/项目业务关键信息提取.txt",
        "dispatch_models": ["project.project", "project.cost.ledger"],
        "coverage": coverage,
        "mapped_fields": mapped_fields,
        "unmapped_fields": unmapped_fields,
    }


def _write_xml(rows: list[dict[str, Any]], xml_path: Path) -> None:
    odoo = ET.Element("odoo")
    data = ET.SubElement(odoo, "data", {"noupdate": "1"})
    mapped_fields = ["budget_total", "cost_actual", "cost_committed", "actual_percent", "plan_percent"]

    for idx, row in enumerate(rows, start=1):
        record = ET.SubElement(
            data,
            "record",
            {
                "id": f"customer_project_metrics_import_{idx:04d}",
                "model": "project.project",
            },
        )
        ET.SubElement(record, "field", {"name": "name"}).text = str(row["name"])
        for field_name in mapped_fields:
            field_value = row.get(field_name)
            if field_value is None:
                continue
            ET.SubElement(record, "field", {"name": field_name}).text = str(field_value)
        ET.SubElement(record, "field", {"name": "description"}).text = str(row["description"])
        ET.SubElement(record, "field", {"name": "active", "eval": "True"})

    xml_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(odoo)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)


def _run_odoo_shell(db: str, script: str) -> str:
    env = os.environ.copy()
    env["DB_NAME"] = db
    proc = subprocess.run(
        ["bash", "scripts/ops/odoo_shell_exec.sh"],
        input=script,
        text=True,
        env=env,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"odoo shell failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc.stdout


def _import_to_db(db: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_payload = []
    for row in rows:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        rows_payload.append(
            {
                "name": name,
                "description": str(row.get("description") or ""),
                "budget_total": row.get("budget_total"),
                "cost_actual": row.get("cost_actual"),
                "cost_committed": row.get("cost_committed"),
                "actual_percent": row.get("actual_percent"),
                "plan_percent": row.get("plan_percent"),
                "cost_components": row.get("cost_components") or {},
            }
        )

    rows_json = json.dumps(rows_payload, ensure_ascii=False)
    py = """
import json
from odoo import fields

rows = json.loads(r'''__ROWS_JSON__''')
Project = env['project.project'].sudo()
CostCode = env['project.cost.code'].sudo()
CostLedger = env['project.cost.ledger'].sudo()

value_fields = ['budget_total', 'cost_actual', 'cost_committed', 'actual_percent', 'plan_percent']
created_ids = []
updated_rows = []
processed = 0

ledger_created_ids = []
ledger_updated_rows = []


def ensure_cost_code(code: str, name: str):
    rec = CostCode.search([('code', '=', code)], limit=1)
    if rec:
        return rec
    return CostCode.create({'code': code, 'name': name, 'type': 'other'})


cost_code_map = {
    'IMP_ACTUAL': ensure_cost_code('IMP_ACTUAL', '导入实际成本').id,
    'IMP_MATERIAL': ensure_cost_code('IMP_MATERIAL', '导入材料合同').id,
    'IMP_LABOR': ensure_cost_code('IMP_LABOR', '导入劳务合同').id,
    'IMP_RENT': ensure_cost_code('IMP_RENT', '导入租赁合同').id,
    'IMP_SUBCON': ensure_cost_code('IMP_SUBCON', '导入分包合同').id,
    'IMP_OTHER': ensure_cost_code('IMP_OTHER', '导入其他合同').id,
}

period_value = fields.Date.context_today(env.user).strftime('%Y-%m')
date_value = fields.Date.context_today(env.user)

for row in rows:
    project_name = str(row.get('name') or '').strip()
    if not project_name:
        continue

    existing = Project.search([('name', '=', project_name)], limit=1)
    values = {
        'description': row.get('description') or '',
        'active': True,
    }
    for field_name in value_fields:
        field_value = row.get(field_name)
        if field_value is not None:
            values[field_name] = float(field_value)

    if existing:
        prev = {
            'id': existing.id,
            'name': existing.name,
            'description': existing.description or '',
            'budget_total': existing.budget_total,
            'cost_actual': existing.cost_actual,
            'cost_committed': existing.cost_committed,
            'actual_percent': existing.actual_percent,
            'plan_percent': existing.plan_percent,
        }
        existing.write(values)
        updated_rows.append(prev)
        project = existing
    else:
        project = Project.create({'name': project_name, **values})
        created_ids.append(project.id)

    components = row.get('cost_components') or {}
    ledger_items = [
        {'line_id': 1, 'amount': row.get('cost_actual'), 'code': 'IMP_ACTUAL', 'note': '客户导入指标-实际成本'},
        {'line_id': 10, 'amount': components.get('材料合同'), 'code': 'IMP_MATERIAL', 'note': '客户导入指标-材料合同'},
        {'line_id': 11, 'amount': components.get('劳务合同'), 'code': 'IMP_LABOR', 'note': '客户导入指标-劳务合同'},
        {'line_id': 12, 'amount': components.get('租赁合同'), 'code': 'IMP_RENT', 'note': '客户导入指标-租赁合同'},
        {'line_id': 13, 'amount': components.get('分包合同'), 'code': 'IMP_SUBCON', 'note': '客户导入指标-分包合同'},
        {'line_id': 14, 'amount': components.get('其他合同'), 'code': 'IMP_OTHER', 'note': '客户导入指标-其他合同'},
    ]

    for item in ledger_items:
        amount = item.get('amount')
        if amount is None:
            continue
        domain = [
            ('source_model', '=', 'customer.metrics.import'),
            ('source_id', '=', project.id),
            ('source_line_id', '=', item['line_id']),
        ]
        existing_ledger = CostLedger.search(domain, limit=1)
        ledger_values = {
            'project_id': project.id,
            'cost_code_id': cost_code_map[item['code']],
            'period': period_value,
            'date': date_value,
            'amount': float(amount),
            'source_model': 'customer.metrics.import',
            'source_id': project.id,
            'source_line_id': item['line_id'],
            'note': item['note'],
        }

        if existing_ledger:
            prev_ledger = {
                'id': existing_ledger.id,
                'project_id': existing_ledger.project_id.id,
                'cost_code_id': existing_ledger.cost_code_id.id,
                'period': existing_ledger.period,
                'date': str(existing_ledger.date) if existing_ledger.date else False,
                'amount': existing_ledger.amount,
                'source_model': existing_ledger.source_model,
                'source_id': existing_ledger.source_id,
                'source_line_id': existing_ledger.source_line_id,
                'note': existing_ledger.note,
            }
            existing_ledger.write(ledger_values)
            ledger_updated_rows.append(prev_ledger)
        else:
            created_ledger = CostLedger.create(ledger_values)
            ledger_created_ids.append(created_ledger.id)

    processed += 1

result = {
    'processed': processed,
    'created_count': len(created_ids),
    'updated_count': len(updated_rows),
    'created_ids': created_ids,
    'updated_rows': updated_rows,
    'ledger_created_count': len(ledger_created_ids),
    'ledger_updated_count': len(ledger_updated_rows),
    'ledger_created_ids': ledger_created_ids,
    'ledger_updated_rows': ledger_updated_rows,
}
env.cr.commit()
print(json.dumps(result, ensure_ascii=False))
""".replace("__ROWS_JSON__", rows_json)

    raw = _run_odoo_shell(db, py)
    match = re.findall(r"\{.*\}", raw, flags=re.S)
    if not match:
        raise RuntimeError(f"import result not found in shell output:\n{raw}")
    return json.loads(match[-1])


def _rollback(db: str) -> dict[str, Any]:
    if not ROLLBACK_FILE.exists():
        raise RuntimeError(f"rollback file not found: {ROLLBACK_FILE}")

    payload = json.loads(ROLLBACK_FILE.read_text(encoding="utf-8"))
    created_ids = payload.get("created_ids") or []
    updated_rows = payload.get("updated_rows") or []
    ledger_created_ids = payload.get("ledger_created_ids") or []
    ledger_updated_rows = payload.get("ledger_updated_rows") or []

    py = f"""
import json

Project = env['project.project'].sudo()
CostLedger = env['project.cost.ledger'].sudo()
created_ids = {json.dumps(created_ids, ensure_ascii=False)}
updated_rows = {json.dumps(updated_rows, ensure_ascii=False)}
ledger_created_ids = {json.dumps(ledger_created_ids, ensure_ascii=False)}
ledger_updated_rows = {json.dumps(ledger_updated_rows, ensure_ascii=False)}

value_fields = ['budget_total', 'cost_actual', 'cost_committed', 'actual_percent', 'plan_percent']
deleted = 0
restored = 0
ledger_deleted = 0
ledger_restored = 0

if ledger_created_ids:
    ledgers = CostLedger.browse(ledger_created_ids).exists()
    ledger_deleted = len(ledgers)
    ledgers.unlink()

for row in ledger_updated_rows:
    rec = CostLedger.browse(int(row.get('id') or 0)).exists()
    if not rec:
        continue
    vals = {{
        'project_id': row.get('project_id'),
        'cost_code_id': row.get('cost_code_id'),
        'period': row.get('period') or False,
        'date': row.get('date') or False,
        'amount': row.get('amount') or 0.0,
        'source_model': row.get('source_model') or False,
        'source_id': row.get('source_id') or False,
        'source_line_id': row.get('source_line_id') or False,
        'note': row.get('note') or False,
    }}
    rec.write(vals)
    ledger_restored += 1

if created_ids:
    created = Project.browse(created_ids).exists()
    deleted = len(created)
    created.unlink()

for row in updated_rows:
    rec = Project.browse(int(row.get('id') or 0)).exists()
    if not rec:
        continue
    vals = {{
        'description': row.get('description') or False,
    }}
    for field_name in value_fields:
        if field_name in row:
            vals[field_name] = row.get(field_name)
    rec.write(vals)
    restored += 1

env.cr.commit()
print(json.dumps({{'deleted': deleted, 'restored': restored, 'ledger_deleted': ledger_deleted, 'ledger_restored': ledger_restored}}, ensure_ascii=False))
"""

    raw = _run_odoo_shell(db, py)
    match = re.findall(r"\{.*\}", raw, flags=re.S)
    if not match:
        raise RuntimeError(f"rollback result not found:\n{raw}")
    return json.loads(match[-1])


def main() -> int:
    parser = argparse.ArgumentParser(description="Import project metrics txt -> xml -> db")
    parser.add_argument("--txt", default="tmp/项目业务关键信息提取.txt")
    parser.add_argument("--xml", default="tmp/customer_project_metrics_import.xml")
    parser.add_argument("--db", default="sc_demo")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback-tag", default="")
    parser.add_argument("--gap-report", default="artifacts/import/customer_metrics_mapping_gap_v1.json")
    args = parser.parse_args()

    txt_path = Path(args.txt)
    xml_path = Path(args.xml)
    gap_report_path = Path(args.gap_report)

    if args.rollback_tag:
        result = _rollback(args.db)
        print(json.dumps({"status": "ROLLBACK", "result": result}, ensure_ascii=False, indent=2))
        return 0

    header, table_rows = _read_txt_table(txt_path)
    import_rows = _build_import_rows(table_rows)
    _write_xml(import_rows, xml_path)

    gap_report = _build_gap_report(header, import_rows)
    gap_report_path.parent.mkdir(parents=True, exist_ok=True)
    gap_report_path.write_text(json.dumps(gap_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    mapped_field_coverage = {
        "budget_total_non_empty": sum(1 for row in import_rows if row.get("budget_total") is not None),
        "cost_actual_non_empty": sum(1 for row in import_rows if row.get("cost_actual") is not None),
        "cost_committed_non_empty": sum(1 for row in import_rows if row.get("cost_committed") is not None),
        "actual_percent_non_empty": sum(1 for row in import_rows if row.get("actual_percent") is not None),
        "plan_percent_non_empty": sum(1 for row in import_rows if row.get("plan_percent") is not None),
    }

    summary: dict[str, Any] = {
        "status": "DRY_RUN" if args.dry_run else "IMPORTED",
        "txt": str(txt_path),
        "xml": str(xml_path),
        "gap_report": str(gap_report_path),
        "header_count": len(header),
        "row_count": len(table_rows),
        "import_row_count": len(import_rows),
        "mapped_field_coverage": mapped_field_coverage,
        "gap_coverage": gap_report.get("coverage") or {},
        "model_dispatch": {
            "project.project": [
                "budget_total",
                "cost_actual",
                "cost_committed",
                "actual_percent",
                "plan_percent",
                "description",
            ],
            "project.cost.ledger": [
                "amount(cost_actual)",
                "amount(材料/劳务/租赁/分包/其他合同)",
                "source_model/source_id/source_line_id",
            ],
        },
    }

    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    result = _import_to_db(args.db, import_rows)
    summary["db"] = args.db
    summary["db_result"] = result

    ROLLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROLLBACK_FILE.write_text(
        json.dumps(
            {
                "created_ids": result.get("created_ids") or [],
                "updated_rows": result.get("updated_rows") or [],
                "ledger_created_ids": result.get("ledger_created_ids") or [],
                "ledger_updated_rows": result.get("ledger_updated_rows") or [],
                "source_xml": str(xml_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary["rollback_file"] = str(ROLLBACK_FILE)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
