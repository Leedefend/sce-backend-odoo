#!/usr/bin/env python3
"""Audit company operation summary sources against legacy output and runtime data."""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
EXCEL_PATH = Path(
    os.getenv(
        "COMPANY_OPERATION_SUMMARY_EXCEL",
        "/home/odoo/workspace/partner_import_source/公司经营情况表1778418457134.xlsx",
    )
)
ARTIFACT_ROOT = REPO_ROOT / "artifacts/company-operation-summary-source-audit"
LEGACY_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
LEGACY_SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
LEGACY_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
LEGACY_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
COMPOSE_PROJECT_NAME = os.getenv("COMPOSE_PROJECT_NAME", "sc-backend-odoo-dev")
ENV_FILE = os.getenv("ENV_FILE", ".env.dev.audit")
DB_NAME = os.getenv("DB_NAME", "sc_acceptance_audit_20260510")


COLUMNS = [
    ("revenue_amount", "营收", None),
    ("deduction_management_fee_amount", "扣款实缴登记/管理费", "GLF"),
    ("deduction_enterprise_income_tax_amount", "扣款实缴登记/企业所得税", "QYSDS_KKSJ"),
    ("deduction_vat_surcharge_amount", "扣款实缴登记/增值税附加", "ZZSFJ"),
    ("deduction_vat_surcharge_nonrefundable_amount", "扣款实缴登记/增值税附加(不可退)", "ZZSFJ_BKT"),
    ("company_interest_income_amount", "财务收入/利息公司", "LXGS_SR"),
    ("bid_document_fee_income_amount", "财务收入/标书制作费", "BSZZF_SR"),
    ("appearance_fee_income_amount", "财务收入/出场费", "CCF_SR"),
    ("certificate_fee_income_amount", "财务收入/证书费", "ZSF_SR"),
    ("company_operation_income_amount", "财务收入/公司经营收入", "GSJYSR_SR"),
    ("union_fee_income_amount", "财务收入/工会经费", "GHJF_SR"),
    ("branch_annual_fee_income_amount", "财务收入/分公司年费", "FGSNF_SR"),
    ("disability_fund_income_amount", "财务收入/残保金", "CBJ_SR"),
    ("personal_income_tax_income_amount", "财务收入/个人所得税", "GRSDS_SR"),
    ("income_amount", "收入合计", None),
    ("expense_amount", "支出合计", None),
    ("reimbursement_amount", "报销申请/报销", "BSSQ"),
    ("salary_amount", "工资登记/工资", "GZ"),
    ("employee_social_security_amount", "社保登记/员工社保", "YGSB"),
    ("certificate_social_security_amount", "社保登记/证书社保", "ZSSB"),
    ("deduction_refund_surcharge_amount", "扣款实缴退回/增值税附加退项目", "ZZSFJXM"),
    ("company_enterprise_income_tax_expense_amount", "公司财务支出/企业所得税", "QYSDS_ZC"),
    ("company_personal_income_tax_expense_amount", "公司财务支出/个人所得税", "GRSDS_ZC"),
    ("company_vat_surcharge_tax_bureau_amount", "公司财务支出/增值税附加交税务局", "ZZSFJJSWJ_ZC"),
    ("tender_fee_expense_amount", "公司财务支出/投标费", "TBF_ZC"),
    ("appearance_fee_expense_amount", "公司财务支出/出场费", "CCF_ZC"),
    ("company_operation_expense_amount", "公司财务支出/公司经营支出", "GSJYZC_ZC"),
    ("company_interest_expense_amount", "公司财务支出/利息公司", "LXGS_ZC"),
    ("disability_fund_expense_amount", "公司财务支出/残保金", "CBJ_ZC"),
    ("union_fee_expense_amount", "公司财务支出/工会经费", "GHJF_ZC"),
    ("service_fee_expense_amount", "公司财务支出/手续费", "SXF_ZC"),
]


EXCEL_COLUMN_INDEX = {
    "revenue_amount": 2,
    "deduction_management_fee_amount": 3,
    "deduction_enterprise_income_tax_amount": 4,
    "deduction_vat_surcharge_amount": 5,
    "deduction_vat_surcharge_nonrefundable_amount": 6,
    "company_interest_income_amount": 7,
    "bid_document_fee_income_amount": 8,
    "appearance_fee_income_amount": 9,
    "certificate_fee_income_amount": 10,
    "company_operation_income_amount": 11,
    "union_fee_income_amount": 12,
    "branch_annual_fee_income_amount": 13,
    "disability_fund_income_amount": 14,
    "personal_income_tax_income_amount": 15,
    "income_amount": 16,
    "expense_amount": 17,
    "reimbursement_amount": 18,
    "salary_amount": 19,
    "employee_social_security_amount": 20,
    "certificate_social_security_amount": 21,
    "deduction_refund_surcharge_amount": 22,
    "company_enterprise_income_tax_expense_amount": 23,
    "company_personal_income_tax_expense_amount": 24,
    "company_vat_surcharge_tax_bureau_amount": 25,
    "tender_fee_expense_amount": 26,
    "appearance_fee_expense_amount": 27,
    "company_operation_expense_amount": 28,
    "company_interest_expense_amount": 29,
    "disability_fund_expense_amount": 30,
    "union_fee_expense_amount": 31,
    "service_fee_expense_amount": 32,
}


def run(cmd: list[str], **kwargs) -> str:
    return subprocess.check_output(cmd, text=True, **kwargs)


def decimal(value: object) -> Decimal:
    text = str(value or "").strip().replace(",", "")
    if not text or text in {"一", "-", "None"}:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def colnum(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    number = 0
    for char in letters:
        number = number * 26 + ord(char) - 64
    return number


def read_excel(path: Path) -> dict[str, dict[str, Decimal]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", ns):
                shared.append("".join(t.text or "" for t in item.findall(".//a:t", ns)))
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: dict[int, dict[int, object]] = {}
        for row in sheet.findall(".//a:row", ns):
            row_number = int(row.attrib["r"])
            values: dict[int, object] = {}
            for cell in row.findall("a:c", ns):
                ref = cell.attrib["r"]
                raw = cell.find("a:v", ns)
                value: object = "" if raw is None else raw.text
                if cell.attrib.get("t") == "s" and value != "":
                    value = shared[int(str(value))]
                values[colnum(ref)] = value
            rows[row_number] = values
    data: dict[str, dict[str, Decimal]] = {}
    for row in rows.values():
        label = str(row.get(1) or "").strip()
        if not label.startswith("2026年-"):
            continue
        data[label] = {field: decimal(row.get(EXCEL_COLUMN_INDEX[field])) for field, _, _ in COLUMNS}
    return data


def read_legacy_proc(year: str = "2026") -> dict[str, dict[str, Decimal]]:
    sql = f"SET NOCOUNT ON; EXEC dbo.Report_GSJYQKB_BSJZ @YEAR='{year}', @KSSJ='', @JSSJ='';"
    raw = run(
        [
            "docker",
            "exec",
            LEGACY_CONTAINER,
            LEGACY_SQLCMD,
            "-S",
            "localhost",
            "-U",
            "sa",
            "-P",
            LEGACY_PASSWORD,
            "-C",
            "-d",
            LEGACY_DATABASE,
            "-W",
            "-s",
            "\t",
            "-Q",
            sql,
        ]
    )
    lines = [line for line in raw.splitlines() if line.strip()]
    rows = [line.split("\t") for line in lines if not set(line.replace("\t", "")) <= {"-"}]
    if not rows:
        return {}
    header = rows[0]
    data: dict[str, dict[str, Decimal]] = {}
    for row in rows[1:]:
        if len(row) != len(header) or not row[0].startswith("2026年-"):
            continue
        values = dict(zip(header, row))
        detail = {}
        for field, _, legacy_alias in COLUMNS:
            if legacy_alias:
                detail[field] = decimal(values.get(legacy_alias))
        income = sum(detail.get(field, Decimal("0")) for field, _, _ in COLUMNS[1:14])
        expense = sum(detail.get(field, Decimal("0")) for field, _, _ in COLUMNS[16:])
        detail["income_amount"] = income
        detail["expense_amount"] = expense
        detail["revenue_amount"] = income - expense
        data[row[0]] = detail
    return data


def read_runtime() -> dict[str, dict[str, Decimal]]:
    fields = ", ".join(["period_label"] + [field for field, _, _ in COLUMNS])
    raw = run(
        [
            "docker",
            "compose",
            "--env-file",
            ENV_FILE,
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "odoo",
            "-d",
            DB_NAME,
            "-At",
            "-F",
            "\t",
            "-c",
            f"SELECT {fields} FROM sc_company_operation_summary WHERE period_year=2026 ORDER BY period_month;",
        ],
        env={**os.environ, "COMPOSE_PROJECT_NAME": COMPOSE_PROJECT_NAME, "ENV": "dev", "ENV_FILE": ENV_FILE},
    )
    data: dict[str, dict[str, Decimal]] = {}
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) != len(COLUMNS) + 1:
            continue
        label = parts[0]
        data[label] = {field: decimal(parts[index + 1]) for index, (field, _, _) in enumerate(COLUMNS)}
    return data


def diff_row(label: str, field: str, excel, legacy, runtime) -> dict[str, object]:
    excel_value = excel.get(label, {}).get(field)
    legacy_value = legacy.get(label, {}).get(field)
    runtime_value = runtime.get(label, {}).get(field)
    item = {
        "period": label,
        "field": field,
        "excel": str(rounded(excel_value)) if excel_value is not None else None,
        "legacy_proc": str(rounded(legacy_value)) if legacy_value is not None else None,
        "runtime": str(rounded(runtime_value)) if runtime_value is not None else None,
    }
    if excel_value is not None and runtime_value is not None:
        item["excel_minus_runtime"] = str(rounded(excel_value - runtime_value))
    if legacy_value is not None and runtime_value is not None:
        item["legacy_proc_minus_runtime"] = str(rounded(legacy_value - runtime_value))
    return item


def main() -> int:
    ts = time.strftime("%Y%m%dT%H%M%S")
    out_dir = ARTIFACT_ROOT / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    excel = read_excel(EXCEL_PATH)
    legacy = read_legacy_proc()
    runtime = read_runtime()
    periods = sorted(set(excel) | set(legacy) | set(runtime))
    mismatches = []
    for label in periods:
        for field, title, _ in COLUMNS:
            item = diff_row(label, field, excel, legacy, runtime)
            item["title"] = title
            deltas = [Decimal(str(item[key])) for key in ("excel_minus_runtime", "legacy_proc_minus_runtime") if key in item]
            if any(abs(delta) > Decimal("0.01") for delta in deltas):
                mismatches.append(item)
    payload = {
        "excel_path": str(EXCEL_PATH),
        "legacy_container": LEGACY_CONTAINER,
        "db_name": DB_NAME,
        "periods": periods,
        "column_count": len(COLUMNS),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out_dir / "mismatches.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "period",
                "title",
                "field",
                "excel",
                "legacy_proc",
                "runtime",
                "excel_minus_runtime",
                "legacy_proc_minus_runtime",
            ],
        )
        writer.writeheader()
        for item in mismatches:
            writer.writerow({key: item.get(key) for key in writer.fieldnames})
    (out_dir / "README.md").write_text(
        "# 公司经营情况表来源审计\n\n"
        f"- Excel: `{EXCEL_PATH}`\n"
        f"- legacy proc: `Report_GSJYQKB_BSJZ`, year 2026, empty start/end date\n"
        f"- runtime DB: `{DB_NAME}`\n"
        f"- periods: `{', '.join(periods)}`\n"
        f"- mismatches: `{len(mismatches)}`\n\n"
        "See `summary.json` and `mismatches.csv` for column-level evidence.\n",
        encoding="utf-8",
    )
    print(json.dumps({"artifacts": str(out_dir), "mismatch_count": len(mismatches)}, ensure_ascii=False))
    return 1 if os.getenv("STRICT_COMPANY_OPERATION_AUDIT") == "1" and mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
