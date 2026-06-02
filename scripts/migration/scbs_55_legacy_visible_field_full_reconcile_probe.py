#!/usr/bin/env python3
"""Strict full-field reconciliation gate for SCBS55 user-visible delivery.

This probe is deliberately stricter than the generic availability probes:
every user-visible list field must have an explicit legacy-source rule before
the delivery can pass. Rules that are present are reconciled across all matched
records, not only samples.
"""

from __future__ import annotations

import ast
import csv
import gzip
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_legacy_visible_field_full_reconcile_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_legacy_visible_field_full_reconcile_probe_report_v1.md"
MAX_MISMATCH_SAMPLES = 50
WRITE_VISIBLE_ALIAS = (
    os.getenv("SCBS55_RECONCILE_WRITE_VISIBLE_ALIAS") == "1"
    or os.getenv("MIGRATION_SCBS55_RECONCILE_WRITE_VISIBLE_ALIAS") == "1"
)


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_legacy_visible_field_reconcile/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_legacy_visible_field_reconcile/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_visible_alias_payload_table() -> None:
    env.cr.execute(  # noqa: F821
        """
        CREATE TABLE IF NOT EXISTS sc_p1_legacy_visible_alias_payload (
            model varchar NOT NULL,
            res_id integer NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            write_date timestamp without time zone NOT NULL DEFAULT now(),
            PRIMARY KEY (model, res_id)
        )
        """
    )


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    if isinstance(value, tuple):
        return clean(value[1] if len(value) > 1 else value[0])
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def clean_amount(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except Exception:
        return text
    if abs(number - round(number)) < 0.000001:
        return str(int(round(number)))
    return ("%.6f" % number).rstrip("0").rstrip(".")


def clean_nonzero_amount(value: object) -> str:
    amount = clean_amount(value)
    return "" if amount in {"", "0"} else amount


def numeric_amount(value: object) -> float:
    text = clean_amount(value)
    if not text:
        return 0.0
    try:
        return float(text)
    except Exception:
        return 0.0


def clean_alias_text(value: object) -> str:
    text = clean(value)
    if len(text) >= 8 and len(text) % 2 == 0 and not text.isdigit():
        half = len(text) // 2
        if text[:half] == text[half:]:
            return text[:half].strip()
    return text


def clean_date(value: object) -> str:
    return clean(value)[:10]


def clean_datetime(value: object) -> str:
    return clean(value).replace("T", " ")[:19]


def state_label(value: object) -> str:
    return {
        "-1": "已作废",
        "0": "未审核",
        "1": "审核中",
        "2": "审核通过",
        "3": "已驳回",
        "4": "已作废",
    }.get(clean(value), clean(value))


def fund_confirmation_state_label(value: object) -> str:
    return {
        "-1": "已驳回",
        "0": "草稿",
        "1": "审核中",
        "2": "审核通过",
    }.get(clean(value), clean(value))


def payment_residual_state_label(value: object) -> str:
    return {
        "0": "草稿",
        "1": "审批中",
        "2": "审核通过",
        "3": "已驳回",
        "4": "已作废",
        "5": "已关闭",
    }.get(clean(value), clean(value))


def payment_request_state_label(value: object) -> str:
    return {
        "-1": "已作废",
        "0": "未审核",
        "1": "审核中",
        "2": "已审核",
    }.get(clean(value), clean(value))


def business_document_state_label(value: object) -> str:
    return {
        "-1": "已作废",
        "0": "未审核",
        "1": "审核中",
        "2": "审核通过",
        "3": "已驳回",
        "4": "已作废",
    }.get(clean(value), clean(value))


def tender_approval_state_label(value: object) -> str:
    return {
        "-1": "已驳回",
        "0": "草稿",
        "1": "审批中",
        "2": "已通过",
        "3": "已驳回",
    }.get(clean(value), clean(value))


def yes_no_label(value: object) -> str:
    text = clean(value)
    return "是" if text in {"1", "true", "True", "是", "Y", "y"} else "否"


def legacy_confirmed_label(value: object) -> str:
    return "历史已确认" if clean(value) else ""


def first_line_business_note(value: object) -> str:
    lines = [
        line.strip()
        for line in clean(value).splitlines()
        if line.strip()
        and not line.strip().startswith("[migration:")
        and line.strip() not in {"company_financial_income", "receipt_confirmation", "customer_receipt", "income", "inflow"}
    ]
    return " ".join(lines)


def clean_visible_note(value: object) -> str:
    text = clean(value).replace("|", " ")
    return "" if text in {"==请选择==", "请选择"} else text


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def action_domain(action) -> list[Any]:
    try:
        return ast.literal_eval(action.domain or "[]")
    except Exception:
        return []


def user_visible_domain(plan, rule: dict[str, Any]) -> list[Any]:
    domain = action_domain(plan.target_action_id)
    if domain:
        return list(domain)
    return list(rule.get("domain") or [])


def contract_labels(record) -> list[str]:
    labels: list[str] = []
    for item in record.list_field_contract or []:
        if isinstance(item, dict):
            label = clean(item.get("legacy_label"))
            if label:
                labels.append(label)
    return labels


def read_csv_rows(path: Path, key: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise RuntimeError({"missing_legacy_visible_csv": str(path)})
    if path.suffix in {".gz", ".json"} or path.name.endswith(".json.gz"):
        rows: dict[str, dict[str, str]] = {}
        for index, raw_row in enumerate(read_old_dump_rows(path), start=1):
            row = {clean(column): clean(value) for column, value in raw_row.items()}
            if key == "__company_archive_row_key__":
                header = clean(row.get("ID") or row.get("Id") or row.get("Pid"))
                child = clean(
                    row.get("Id$SGZL_RZRJ_CB")
                    or row.get("pid$SGZL_RZRJ_CB")
                    or row.get("RowIndex")
                    or index
                )
                row_key = f"{header}:{child}"
            else:
                row_key = clean(row.get(key))
            if row_key:
                rows[row_key] = row
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        first_line = sample.splitlines()[0] if sample else ""
        dialect = csv.excel()
        if first_line.count("|") > first_line.count(","):
            dialect.delimiter = "|"
        elif "\t" in first_line and first_line.count("\t") > first_line.count(","):
            dialect.delimiter = "\t"
        else:
            dialect.delimiter = ","
        rows: dict[str, dict[str, str]] = {}
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames:
            reader.fieldnames = [clean(field_name) for field_name in reader.fieldnames]
        for row in reader:
            row_key = clean(row.get(key))
            if row_key:
                clean_row = {column: clean(value) for column, value in row.items()}
                if clean_row.get("raw_payload"):
                    try:
                        raw = json.loads(clean_row["raw_payload"])
                    except Exception:
                        raw = {}
                    for raw_key, raw_value in raw.items():
                        clean_row.setdefault(raw_key, clean(raw_value))
                rows[row_key] = clean_row
                if "#" in row_key:
                    rows.setdefault(row_key.split("#", 1)[0], clean_row)
        return rows


def merge_csv_rows(rows: dict[str, dict[str, str]], path: Path, key: str) -> None:
    lookup = read_csv_rows(path, key)
    for row_key, row in rows.items():
        raw = lookup.get(row_key)
        if raw:
            row.update({column: value for column, value in raw.items() if value})


def source_value(row: dict[str, str], columns: list[str], normalizer: Callable[[object], str] = clean) -> str:
    for column in columns:
        if column.startswith("__CONST__:"):
            return normalizer(column.split(":", 1)[1])
        value = normalizer(row.get(column))
        if value:
            return value
    return ""


def fund_confirmation_computed_value(
    legacy: dict[str, str],
    line_sums: dict[str, float],
    column: str,
) -> str:
    header_id = clean(legacy.get("legacy_header_id"))
    actual = numeric_amount(legacy.get("actual_fund_amount"))
    deducted = line_sums.get(header_id, 0.0)
    if column == "__COMPUTED__:deducted_amount_total":
        return clean_amount(deducted)
    if column == "__COMPUTED__:paid_amount_total":
        return clean_amount(max(actual - deducted, 0.0))
    return ""


def visible_value(record, label: str) -> str:
    field_name = alias_field_name(label)
    if field_name not in record._fields:
        return "<MISSING_ALIAS_FIELD>"
    return clean(record[field_name])


def write_visible_alias_values(record, values: dict[str, str]) -> int:
    ensure_visible_alias_payload_table()
    env.cr.execute(  # noqa: F821
        "SELECT payload FROM sc_p1_legacy_visible_alias_payload WHERE model = %s AND res_id = %s",
        [record._name, record.id],
    )
    row = env.cr.fetchone()  # noqa: F821
    payload = row[0] if row and isinstance(row[0], dict) else {}
    payload = {**payload, **values}
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_p1_legacy_visible_alias_payload(model, res_id, payload, write_date)
        VALUES (%s, %s, %s::jsonb, now())
        ON CONFLICT (model, res_id)
        DO UPDATE SET payload = EXCLUDED.payload, write_date = now()
        """,
        [record._name, record.id, json.dumps(payload, ensure_ascii=False)],
    )
    return len(values)


def record_legacy_key(record, rule: dict[str, Any]) -> str:
    def normalize_record_key(value: str) -> str:
        if rule.get("strip_record_key_suffix"):
            value = value.split("#", 1)[0]
        if rule.get("strip_record_key_colon_suffix"):
            value = value.split(":", 1)[0]
        return value

    if rule.get("record_key_regex"):
        text = clean(record[rule.get("record_key_field", "note")])
        match = re.search(rule["record_key_regex"], text)
        return clean(match.group(1)) if match else ""
    record_key = rule["record_key"]
    if isinstance(record_key, (list, tuple)):
        for field_name in record_key:
            if field_name in record._fields:
                value = clean(record[field_name])
                if value:
                    return normalize_record_key(value)
        return ""
    if record_key not in record._fields:
        return ""
    value = clean(record[record_key])
    return normalize_record_key(value)


def spec_source_key(spec: Any) -> str:
    if len(spec) >= 3:
        return clean(spec[2])
    return ""


def record_secondary_key(record, source_rule: dict[str, Any]) -> str:
    if source_rule.get("record_key_regex"):
        text = clean(record[source_rule.get("record_key_field", "legacy_record_id")])
        match = re.search(source_rule["record_key_regex"], text)
        return clean(match.group(1)) if match else ""
    return clean(record[source_rule.get("record_key", "legacy_record_id")])


TENDER_GUARANTEE_FACT_CSV = "/mnt/artifacts/migration/scbs_tender_registration_fact_visible_payload_v1.csv"
BUSINESS_ENTITY_VISIBLE_TSV = Path("/mnt/artifacts/migration/scbs_business_entity_visible_unified.tsv")


def latest_scbs55_old_dump_dir() -> Path | None:
    explicit = [
        os.getenv("MIGRATION_SCBS55_OLD_FULL_DUMP_DIR"),
        os.getenv("SCBS55_OLD_FULL_DUMP_DIR"),
    ]
    candidates = [Path(item) for item in explicit if item]
    for pattern in (
        "artifacts/migration/live_old_system_strict_parity_gate/*/scbs55_old_live_rows",
        "/mnt/artifacts/migration/live_old_system_strict_parity_gate/*/scbs55_old_live_rows",
    ):
        candidates.extend(sorted(Path().glob(pattern) if not pattern.startswith("/") else Path("/").glob(pattern[1:])))
    usable = [candidate for candidate in candidates if candidate.exists() and candidate.is_dir()]
    return sorted(usable)[-1] if usable else None


def read_old_dump_rows(path: Path) -> list[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else []


def refresh_business_entity_visible_unified_tsv() -> None:
    dump_dir = latest_scbs55_old_dump_dir()
    if not dump_dir:
        return
    files = sorted(dump_dir.glob("scbs_55_old_live_full_rows_seq001_*.json*"))
    files.extend(sorted(dump_dir.glob("scbs_55_old_live_full_rows_seq002_*.json*")))
    if not files:
        return

    rows: list[dict[str, str]] = []
    columns: set[str] = {"legacy_xmid", "legacy_record_id", "source_seq", "raw_payload"}
    for file_path in files:
        seq_match = re.search(r"seq0*(\d+)_", file_path.name)
        source_seq = seq_match.group(1) if seq_match else ""
        for raw_row in read_old_dump_rows(file_path):
            if not isinstance(raw_row, dict):
                continue
            legacy_id = clean(raw_row.get("Id"))
            if not legacy_id:
                continue
            row = {clean(key): clean(value) for key, value in raw_row.items()}
            row["legacy_xmid"] = legacy_id
            row["legacy_record_id"] = legacy_id
            row["source_seq"] = source_seq
            row["raw_payload"] = json.dumps(raw_row, ensure_ascii=False, sort_keys=True)
            columns.update(row.keys())
            rows.append(row)

    if not rows:
        return
    ordered_columns = ["legacy_xmid", "legacy_record_id", "source_seq"] + sorted(
        column for column in columns if column not in {"legacy_xmid", "legacy_record_id", "source_seq"}
    )
    BUSINESS_ENTITY_VISIBLE_TSV.parent.mkdir(parents=True, exist_ok=True)
    with BUSINESS_ENTITY_VISIBLE_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered_columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


FIELD_RULES: dict[int, dict[str, Any]] = {
    10: {
        "name": "供应商/合作单位",
        "model": "sc.business.entity",
        "legacy_table": "SCBS_FACT_BUSINESS_ENTITY_CANDIDATE",
        "legacy_csv": "/mnt/artifacts/migration/scbs_business_entity_visible_unified.tsv",
        "legacy_key": "legacy_xmid",
        "record_key": "legacy_xmid",
        "domain": [],
        "fields": {
            "单据状态": (["DJZTText", "DJZT"], business_document_state_label),
            "推送结果": (["TSJG"], clean),
            "项目名称": (["XMMC"], clean_alias_text),
            "单位编号": (["DJBH"], clean),
            "合作类型": (["HZLX"], clean),
            "单位名称": (["DWMC"], clean_alias_text),
            "开户银行": (["KHYH"], clean),
            "账号": (["KHZH"], clean),
            "统一社会信用代码": (["TYSHXYDM"], clean),
            "主税率": (["ZSLV"], clean),
            "录入人": (["LRR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
        },
    },
    20: {
        "name": "往来单位",
        "model": "sc.business.entity",
        "legacy_table": "SCBS_FACT_BUSINESS_ENTITY_CANDIDATE",
        "legacy_csv": "/mnt/artifacts/migration/scbs_business_entity_visible_unified.tsv",
        "legacy_key": "legacy_xmid",
        "record_key": "legacy_xmid",
        "domain": [],
        "fields": {
            "单据状态": (["DJZTText", "DJZT"], business_document_state_label),
            "项目名称": (["XMMC"], clean_alias_text),
            "单位名称": (["DWMC"], clean_alias_text),
            "收款金额": (["SKJE"], clean_amount),
            "付款金额": (["FKJE"], clean_amount),
            "开户姓名": (["KHXM$T_Base_CooperatCompany_Account"], clean),
            "开户账号": (["KHZH$T_Base_CooperatCompany_Account"], clean),
            "开户银行": (["KHYH$T_Base_CooperatCompany_Account"], clean),
            "录入人": (["LRR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
            "银行账号": (["D_SCBSJS_YHZH"], clean),
        },
    },
    30: {
        "name": "施工合同",
        "model": "construction.contract",
        "legacy_table": "SCBS_CONSTRUCTION_CONTRACT_VISIBLE_UNIFIED",
        "legacy_csv": "/mnt/artifacts/migration/scbs_construction_contract_visible_unified.tsv",
        "legacy_key": "legacy_contract_id",
        "record_key": "legacy_contract_id",
        "domain": [("legacy_contract_id", "!=", False)],
        "fields": {
            "单据状态": (["legacy_visible_document_state"], state_label),
            "单据编号": (["legacy_visible_document_no"], clean),
            "合同订立日期": (["legacy_visible_contract_date"], clean_date),
            "原件是否归档": (["legacy_visible_archived"], clean),
            "发包人": (["legacy_visible_counterparty"], clean_alias_text),
            "项目名称": (["legacy_visible_project_name"], clean_alias_text),
            "合同标题": (["legacy_visible_title"], clean_alias_text),
            "工程类别": (["legacy_visible_category"], clean),
            "合同编号": (["legacy_visible_contract_no"], clean),
            "合同金额": (["legacy_visible_amount"], clean_amount),
            "结算金额": (["legacy_visible_settlement_amount"], clean_amount),
            "累计开票": (["legacy_visible_invoice_amount"], clean_amount),
            "累计收款": (["legacy_visible_received_amount"], clean_amount),
            "未收款": (["legacy_visible_unreceived_amount"], clean_amount),
            "未收款比例": (["legacy_visible_unreceived_rate"], clean),
            "挂靠人": (["legacy_visible_affiliated_person"], clean),
            "工程地址": (["legacy_visible_engineering_address"], clean_alias_text),
            "工程内容": (["legacy_visible_engineering_content"], clean_visible_note),
            "录入人": (["legacy_visible_creator_name"], clean),
            "录入时间": (["legacy_visible_created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    40: {
        "name": "公司资料存档",
        "model": "sc.document.admin.document",
        "legacy_table": "online_old_scbs:SGZL_RZRJ:list856",
        "legacy_csv": "/tmp/scbs_55_old_live_full_rows_seq004_company_archive.json.gz",
        "legacy_key": "__company_archive_row_key__",
        "record_key": "legacy_source_id",
        "domain": [("legacy_source_table", "=", "online_old_scbs:SGZL_RZRJ:list856")],
        "fields": {
            "单据状态": (["DJZT"], business_document_state_label),
            "项目名称": (["f_GCMC"], clean),
            "资料类型": (["ZLMC$SGZL_RZRJ_CB", "ZLMC"], clean),
            "资料说明": (["ZLSM$SGZL_RZRJ_CB", "f_SM"], clean),
            "录入人": (["LRR", "f_LRR"], clean),
            "备注": (["BZ"], clean_visible_note),
            "录入时间": (["LRSJ", "f_LRSJ", "f_SJ"], clean_datetime),
        },
    },
    50: {
        "name": "请假/休假审批单",
        "model": "sc.office.admin.document",
        "legacy_table": "BGGL_HBZJ_XZD_QJXJSPB",
        "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_business_fact_residual_replay_payload_v1.csv",
        "legacy_key": "legacy_record_id",
        "record_key": "legacy_source_id",
        "domain": [("fact_type", "=", "leave_request")],
        "fields": {
            "单据状态": (["DJZT"], business_document_state_label),
            "单据编号": (["DJBH"], clean),
            "项目名称": (["XMMC", "project_name"], clean_alias_text),
            "申请人姓名": (["SQRXM"], clean),
            "所在部门": (["SZBM"], clean),
            "请假天数": (["QJTS"], clean_amount),
            "请假类型": (["QJLX"], clean),
            "请假时间": (["QJSJ"], clean_datetime),
            "销假时间": (["SJXJSJ", "XJSJ"], clean_datetime),
            "备注": (["BZ"], clean_visible_note),
            "请假时长": (["QJSC"], clean_amount),
            "录入人": (["LRR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
        },
    },
    60: {
        "name": "印章使用审批表",
        "model": "sc.office.admin.document",
        "legacy_table": "BGGL_XZD_YZSYSPB",
        "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_business_fact_residual_replay_payload_v1.csv",
        "legacy_key": "legacy_record_id",
        "record_key": "legacy_source_id",
        "domain": [("fact_type", "=", "seal_use")],
        "fields": {
            "单据状态": (["DJZT"], business_document_state_label),
            "单据编号": (["DJBH"], clean),
            "用印时间": (["YYSJ"], clean_date),
            "用印部门": (["YYBM"], clean),
            "用印申请人": (["YYSQR"], clean),
            "用印部门负责人签字": (["YYBMFZRQZ"], clean),
            "用印种类": (["YYZL"], clean),
            "用印文本名称及文号": (["YYWBMCJWH", "GZWJNBGY"], clean_visible_note),
            "经办人签字": (["JBRQZ"], clean),
            "领导签字": (["LDQZ"], clean),
            "份数": (["FS"], clean_amount),
            "备注": (["BZ"], clean_visible_note),
            "归还时间": (["GHSJ"], clean_date),
            "合同金额": (["HTJE"], clean_amount),
            "合同编号": (["HTBH"], clean),
            "所属公司": (["SSGS"], clean),
            "使用印章公司": (["D_JCLY_SYYZGS"], clean),
            "是否外带": (["D_JCLY_SFWD"], clean),
            "录入人": (["LRR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    150: {
        "name": "借阅申请",
        "model": "sc.document.admin.document",
        "legacy_table": "BGGL_TZXX_WJPYCJ/BGGL_TZXX_WJHQ",
        "legacy_csv": "/mnt/artifacts/migration/BGGL_TZXX_document_borrow_visible.tsv",
        "legacy_key": "Id",
        "record_key": "legacy_source_id",
        "domain": [("fact_type", "=", "document_borrow")],
        "fields": {
            "单据状态": (["DJZT"], business_document_state_label),
            "单据编号": (["DJBH"], clean),
            "借阅项目名称": (["XMMC"], clean_alias_text),
            "证件名称": (["WJBT", "WJMC", "LXMC"], clean_alias_text),
            "申请日期": (["DJRQ", "WJTJRQ"], clean_date),
            "借阅部门或项目部名称": (["SSDW", "SS单位", "FWBM"], clean),
            "借阅人": (["QSR", "WJNGR"], clean),
            "联系方式": (["__CONST__:"], clean),
            "借阅形式": (["JJCD", "WJLX", "LXMC"], clean),
            "借阅日期": (["DJRQ", "WJTJRQ"], clean_date),
            "负责人": (["__CONST__:"], clean),
            "归还申请日期": (["HQWCSJ"], clean_date),
            "申请归还时间": (["HQWCSJ"], clean_datetime),
            "是否归还": (["returned_flag"], yes_no_label),
            "确认归还时间": (["HQWCSJ"], clean_datetime),
            "归还日期": (["HQWCSJ"], clean_date),
            "录入人": (["LRR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
            "备注": (["WJNR"], clean_visible_note),
            "修改人": (["XGR"], clean),
            "修改日期": (["XGSJ"], clean_datetime),
            "修改备注": (["__CONST__:"], clean),
            "审定人": (["__CONST__:"], clean),
            "审定时间": (["__CONST__:"], clean_datetime),
            "审定意见": (["__CONST__:"], clean),
        },
        "optional_labels": {"附件"},
    },
    240: {
        "name": "报销申请",
        "model": "sc.expense.claim",
        "legacy_table": "CWGL_FYBX_CB",
        "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv",
        "legacy_key": "legacy_line_id",
        "record_key": "legacy_record_id",
        "domain": [("legacy_source_table", "=", "CWGL_FYBX_CB")],
        "fields": {
            "单据状态": (["document_state"], business_document_state_label),
            "单据编号": (["document_no"], clean),
            "所属公司": (["company_name"], clean),
            "日期": (["document_date"], clean_date),
            "部门": (["department_name"], clean),
            "报销人": (["applicant_name"], clean),
            "报销类别": (["reimbursement_type"], clean),
            "事项说明": (["summary"], clean_visible_note),
            "报销金额": (["amount"], clean_amount),
            "收款人": (["payee"], clean),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    180: {
        "name": "自筹保证金",
        "model": "tender.guarantee",
        "legacy_table": "sc_legacy_tender_registration_fact",
        "legacy_csv": TENDER_GUARANTEE_FACT_CSV,
        "legacy_key": "id",
        "record_key": "legacy_fact_id",
        "domain": [],
        "fields": {
            "状态": (["document_state"], business_document_state_label),
            "单据编号": (["document_no"], clean),
            "投标项目名称": (["project_name"], clean_alias_text),
            "项目名称": (["project_name"], clean_alias_text),
            "所属公司": (["__CONST__:"], clean),
            "金额": (["guarantee_amount"], clean_amount),
            "已退保证金金额": (["__CONST__:"], clean_amount),
            "转款单位": (["__CONST__:"], clean),
            "汇款方式": (["__CONST__:"], clean),
            "保证金类型": (["__CONST__:"], clean),
            "收款账户": (["__CONST__:"], clean),
            "收款账户名称": (["__CONST__:"], clean),
            "备注": (["note"], clean_visible_note),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    190: {
        "name": "自筹保证金退回",
        "model": "tender.guarantee",
        "legacy_table": "sc_legacy_tender_registration_fact",
        "legacy_csv": TENDER_GUARANTEE_FACT_CSV,
        "legacy_key": "id",
        "record_key": "legacy_fact_id",
        "domain": [],
        "fields": {
            "状态": (["document_state"], business_document_state_label),
            "收保证金单号": (["document_no"], clean),
            "单据编号": (["document_no"], clean),
            "项目名称": (["project_name"], clean_alias_text),
            "投标项目名称": (["project_name"], clean_alias_text),
            "退还金额": (["__CONST__:"], clean_amount),
            "备注": (["note"], clean_visible_note),
            "退还账号": (["__CONST__:"], clean),
            "退还开户行": (["__CONST__:"], clean),
            "单位": (["__CONST__:"], clean),
            "收款开户行": (["__CONST__:"], clean),
            "收款账号": (["__CONST__:"], clean),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    200: {
        "name": "付款还保证金",
        "model": "tender.guarantee",
        "legacy_table": "sc_legacy_tender_registration_fact",
        "legacy_csv": TENDER_GUARANTEE_FACT_CSV,
        "legacy_key": "id",
        "record_key": "legacy_fact_id",
        "domain": [],
        "fields": {
            "状态": (["document_state"], business_document_state_label),
            "推送结果": (["__CONST__:"], clean),
            "金蝶单据编号": (["__CONST__:"], clean),
            "单据编号": (["document_no"], clean),
            "投标项目": (["project_name"], clean_alias_text),
            "工程项目": (["project_name"], clean_alias_text),
            "保证金类型": (["__CONST__:"], clean),
            "所属公司": (["__CONST__:"], clean),
            "保证金金额": (["guarantee_amount"], clean_amount),
            "已退金额": (["__CONST__:"], clean_amount),
            "未退金额": (["__CONST__:"], clean_amount),
            "是否需要退回": (["__CONST__:"], clean),
            "收款单位": (["__CONST__:"], clean),
            "支付账户": (["__CONST__:"], clean),
            "备注": (["note"], clean_visible_note),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    210: {
        "name": "付款还保证金退回",
        "model": "tender.guarantee",
        "legacy_table": "sc_legacy_tender_registration_fact",
        "legacy_csv": TENDER_GUARANTEE_FACT_CSV,
        "legacy_key": "id",
        "record_key": "legacy_fact_id",
        "domain": [],
        "fields": {
            "状态": (["document_state"], business_document_state_label),
            "推送结果": (["__CONST__:"], clean),
            "退回单编号": (["document_no"], clean),
            "所属公司": (["__CONST__:"], clean),
            "投标项目名称": (["project_name"], clean_alias_text),
            "保证金类型": (["__CONST__:"], clean),
            "退回项目": (["project_name"], clean_alias_text),
            "退回金额": (["__CONST__:"], clean_amount),
            "退回账户": (["__CONST__:"], clean),
            "收款单位": (["__CONST__:"], clean),
            "备注": (["note"], clean_visible_note),
            "录入人": (["creator_name"], clean),
            "退回日期": (["__CONST__:"], clean_date),
        },
        "optional_labels": {"附件"},
    },
    250: {
        "name": "收入",
        "model": "sc.receipt.income",
        "legacy_table": "C_CWSFK_GSCWSR",
        "legacy_csv": "/tmp/c_cwsfk_gscwsr_visible.csv",
        "legacy_key": "Id",
        "record_key": "legacy_record_id",
        "domain": [("legacy_source_table", "=", "C_CWSFK_GSCWSR")],
        "fields": {
            "单据状态": (["DJZT"], state_label),
            "项目名称": (["XMMC"], clean),
            "单据编号": (["DJBH"], clean),
            "填写人": (["LRR", "TXR"], clean),
            "收款账户": (["SKZH"], clean),
            "进账金额": (["JZJE"], clean_amount),
            "收入类别": (["D_SCBSJS_CWSRLB", "SKLB"], clean),
            "收款时间": (["SKSJ"], clean_date),
            "备注": (["BZ"], clean_visible_note),
            "录入人": (["LRR", "TXR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    260: {
        "name": "公司财务支出",
        "model": "sc.expense.claim",
        "legacy_table": "C_CWSFK_GSCWZC",
        "legacy_csv": "/tmp/c_cwsfk_gscwzc_visible.csv",
        "legacy_key": "Id",
        "record_key": "legacy_record_id",
        "domain": [("legacy_source_table", "=", "C_CWSFK_GSCWZC")],
        "fields": {
            "单据状态": (["DJZT"], clean),
            "推送结果": (["D_SCBSJS_IsPush"], clean),
            "单据编号": (["DJBH"], clean),
            "付款时间": (["FKSJ"], clean_date),
            "付款金额": (["FKJE"], clean_amount),
            "成本类别": (["D_SCBSJS_CWZCLB", "CBLBMC"], clean),
            "收款单位名称": (["SKDWMC"], clean),
            "付款账户名称": (["FKZHMC"], clean),
            "备注": (["BZ"], clean_visible_note),
            "录入人": (["LRR"], clean),
            "录入时间": (["LRSJ"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    290: {
        "name": "支付申请",
        "model": "payment.request",
        "legacy_table": "C_ZFSQGL",
        "legacy_csv": "/tmp/c_zfsqgl_visible.csv",
        "legacy_key": "Id",
        "record_key": "legacy_record_id",
        "domain": [("legacy_source_table", "=", "C_ZFSQGL")],
        "fields": {
            "单据状态": (["DJZT"], payment_request_state_label),
            "单据编号": (["DJBH"], clean),
            "项目名称": (["f_XMMC"], clean),
            "申请日期": (["f_SQRQ"], clean_date),
            "收款单位": (["f_GYSMC"], clean),
            "申请付款金额": (["f_JHJE"], clean_amount),
            "实际付款金额": (["f_SFJE"], clean_amount),
            "可用余额": (["SJKYYE", "ZMYE"], clean_amount),
            "成本分类名称": (["f_CBFLMC"], clean),
            "备注": (["f_Remark"], clean_visible_note),
            "付款账号": (["FKZH"], clean),
            "金额大写": (["JEDX"], clean),
            "户名": (["HM", "f_GYSMC"], clean),
            "开户行": (["f_KHH"], clean_alias_text),
            "账号": (["f_ZH"], clean),
            "填写人": (["f_TXR", "LRR"], clean),
            "录入时间": (["f_LRSJ"], clean_datetime),
        },
        "optional_labels": {"附件", "是否关联单据"},
    },
    310: {
        "name": "往来单位付款",
        "model": "sc.payment.execution",
        "legacy_table": "T_FK_Supplier",
        "legacy_csv": "/tmp/t_fk_supplier_visible.csv",
        "legacy_key": "Id",
        "secondary_sources": {
            "line": {
                "legacy_csv": "/tmp/t_fk_supplier_cb_visible.csv",
                "legacy_key": "Id",
                "record_key": "legacy_record_id",
                "record_key_regex": r"actual_outflow_line:([^;\n]+)",
            }
        },
        "record_key": "legacy_record_id",
        "record_key_field": "note",
        "record_key_regex": r"legacy_parent_id=([^;\\n]+)",
        "domain": [("legacy_source_table", "=", "T_FK_Supplier_CB")],
        "fields": {
            "单据状态": (["DJZT"], legacy_confirmed_label),
            "单据编号": (["DJBH"], clean),
            "項目名称": (["XMMC"], clean),
            "供应商名称": (["f_SupplierName"], clean),
            "付款日期": (["f_FKRQ"], clean_date),
            "付款金额": (["CCZFJE", "ZJE"], clean_nonzero_amount, "line"),
            "备注": (["f_BZ"], clean_visible_note),
            "其他备注": (["BZ"], clean_visible_note),
            "付款方式名称": (["f_FKFSMC"], clean),
            "填写人": (["f_TXR"], clean),
            "开户行": (["KHH"], clean_alias_text),
            "账户": (["ZH"], clean),
            "付款账户": (["FKZH"], clean),
            "付款账户名称": (["FKZHMC"], clean),
            "支付申请单号": (["ZFSQDH"], clean),
        },
        "optional_labels": {"附件", "推送结果", "金蝶单据编号"},
    },
    350: {
        "name": "到款确认表",
        "model": "sc.legacy.fund.confirmation.document",
        "legacy_table": "ZJGL_SZQR_DKQRB",
        "legacy_csv": "/tmp/zjgl_szqr_dkqrb_header_visible.csv",
        "legacy_key": "legacy_header_id",
        "secondary_sources": {
            "line": {
                "legacy_csv": "/tmp/zjgl_szqr_dkqrb_line_visible.csv",
                "legacy_key": "legacy_line_id",
            }
        },
        "record_key": "legacy_header_id",
        "domain": [],
        "fields": {
            "单据状态": (["document_state"], fund_confirmation_state_label),
            "单据编号": (["document_no"], clean),
            "时间": (["receipt_time"], clean_datetime),
            "项目名称": (["project_name"], clean),
            "期数": (["period_no"], clean),
            "本期收款": (["actual_fund_amount"], clean_amount),
            "本期代扣代缴合计": (["__COMPUTED__:deducted_amount_total"], clean_amount),
            "本期拨付金额合计": (["__COMPUTED__:paid_amount_total"], clean_amount),
            "施工单位": (["contract_name"], clean),
            "合同金额": (["contract_amount"], clean_amount),
            "目前形象进度": (["current_project_stage"], clean),
            "累计开票金额": (["accumulated_invoice_amount"], clean_amount),
            "上期留存余额": (["__CONST__:0"], clean_amount),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
    360: {
        "name": "资金日报表",
        "model": "sc.legacy.fund.daily.line",
        "legacy_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB",
        "legacy_csv": "/tmp/d_scbsjs_zjgl_zjsz_zjrbb_line_visible.csv",
        "legacy_key": "legacy_line_id",
        "record_key": "legacy_line_id",
        "domain": [("source_table", "in", ["D_SCBSJS_ZJGL_ZJSZ_ZJRBB", "D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB"])],
        "fields": {
            "单据状态": (["document_state"], clean),
            "单据编号": (["document_no"], clean),
            "单据日期": (["document_date"], clean_date),
            "账号名称": (["account_name"], clean),
            "银行账号": (["bank_account_no"], clean),
            "当前账户余额": (["current_account_balance"], clean_amount),
            "当前账户银行余额": (["current_bank_balance"], clean_amount),
            "银行系统差额": (["bank_system_difference"], clean_amount),
            "当日累计收入": (["daily_income"], clean_amount),
            "当日累计支出": (["daily_expense"], clean_amount),
            "账户往来": (["__CONST__:"], clean),
            "备注": (["note", "header_note"], clean_visible_note),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
    },
    410: {
        "name": "预缴税款",
        "model": "sc.invoice.registration",
        "legacy_table": "C_JXXP_YJSKDJ/C_JXXP_YJSKDJ_CB",
        "legacy_csv": "/tmp/legacy_income_invoice_visible.csv",
        "legacy_key": "legacy_record_id",
        "record_key": "legacy_record_id",
        "domain": [("source_kind", "=", "prepaid_tax"), ("direction", "=", "prepaid"), ("amount_total", "!=", 0)],
        "fields": {
            "状态": (["document_state"], state_label),
            "项目名称": (["project_name"], clean),
            "单据编号": (["document_no"], clean),
            "受票方名称": (["partner_name"], clean),
            "交税类型": (["tax_type"], clean),
            "金额": (["amount_total"], clean_amount),
            "不含税金额": (["amount_no_tax"], clean_amount),
            "税额": (["tax_amount"], clean_amount),
            "发票开具日期": (["expected_receipt_date"], clean_date),
            "预缴税款日期": (["invoice_date"], clean_date),
            "完税凭证号码": (["tax_certificate_no"], clean),
            "数据类型": (["source_dataset", "__CONST__:预缴税"], clean),
            "录入人": (["creator_name"], clean),
        },
        "optional_labels": {"附件"},
    },
    430: {
        "name": "抵扣登记",
        "model": "sc.tax.deduction.registration",
        "legacy_table": "C_JXXP_DKDJ_CB",
        "legacy_csv": "/tmp/legacy_tax_deduction_visible.csv",
        "legacy_key": "legacy_line_id",
        "record_key": "legacy_record_id",
        "domain": [("legacy_source_table", "in", ["C_JXXP_DKDJ_New", "C_JXXP_DKDJ_CB"])],
        "fields": {
            "单据状态": (["document_state"], state_label),
            "单据编号": (["document_no"], clean),
            "是否转出": (["is_transfer_out"], yes_no_label),
            "项目名称": (["project_name"], clean),
            "开票单位": (["partner_name"], clean),
            "发票号": (["invoice_no"], clean),
            "抵扣税额": (["deduction_tax_amount"], clean_amount),
            "抵扣总额": (["deduction_amount"], clean_amount),
            "抵扣附加税": (["deduction_surcharge_amount"], clean_amount),
            "备注": (["note"], clean_visible_note),
            "录入人": (["creator_name"], clean),
            "单据日期": (["document_date"], clean_date),
        },
    },
    440: {
        "name": "外经证登记",
        "model": "sc.legacy.payment.residual.fact",
        "legacy_table": "ZJGL_WJZ_WJZDJB",
        "legacy_csv": "/tmp/legacy_payment_residual_visible.csv",
        "legacy_key": "legacy_record_id",
        "record_key": "legacy_record_id",
        "domain": [("source_table", "in", ["ZJGL_WJZ_WJZDJB"])],
        "fields": {
            "单据状态": (["document_state"], payment_residual_state_label),
            "单据编号": (["document_no"], clean),
            "项目名称": (["project_name"], clean),
            "纳税人名称": (["taxpayer_name"], clean),
            "纳税人识别号": (["taxpayer_identifier"], clean),
            "经办人手机": (["handler_phone"], clean),
            "区域涉税事项联系人": (["regional_tax_contact"], clean),
            "区域涉税事项联系人座机手机": (["regional_tax_contact_phone"], clean),
            "跨区域经营地址": (["operation_address"], clean_alias_text),
            "经营方式": (["payment_method"], clean),
            "合同名称": (["contract_name"], clean),
            "合同金额": (["planned_amount"], clean_amount),
            "合同开始日期": (["contract_start_date"], clean_date),
            "合同结束日期": (["contract_end_date"], clean_date),
            "合同相对方名称": (["partner_name"], clean),
            "合同相对方名称编号": (["counterparty_tax_identifier"], clean),
            "跨区域涉税事项报验管理编号": (["tax_report_management_no"], clean),
            "录入人": (["creator_name"], clean),
            "录入时间": (["created_time"], clean_datetime),
        },
        "optional_labels": {"附件"},
    },
}


FIELD_RULES.update(
    {
        80: {
            "name": "公司人员名册（配置）",
            "model": "sc.legacy.user.profile",
            "legacy_table": "BASE_SYSTEM_USER",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv",
            "legacy_key": "legacy_user_id",
            "record_key": "legacy_user_id",
            "domain": [("source_table", "in", ["BASE_SYSTEM_USER"])],
            "fields": {
                "姓名": (["display_name"], clean),
                "用户名": (["source_login", "generated_login"], clean),
                "部门": (["department_name", "department_scope_summary"], clean),
                "职务": (["professional_title"], clean),
                "岗位": (["professional_qualification", "professional_title"], clean),
                "电话号码": (["phone"], clean),
                "性别": (["sex"], clean),
                "账号类型": (["account_type"], clean),
                "是否测试账号": (["user_type", "account_type"], clean),
                "证件类型": (["credential_type"], clean),
                "证件号": (["credential_no"], clean),
                "居住地址": (["residence_address"], clean),
                "是否购买社保": (["person_state"], clean),
                "员工工号": (["employee_no", "tr_user_job_number"], clean),
                "出生日期": (["birth_date"], clean_date),
                "政治面貌": (["political_status"], clean),
                "民族": (["nation"], clean),
                "籍贯": (["native_place"], clean),
                "毕业院校": (["graduation_school"], clean),
                "毕业时间": (["graduation_date"], clean_date),
                "所学专业": (["major"], clean),
                "学历": (["education"], clean),
                "入职日期": (["onboarding_date"], clean_date),
                "人员类型": (["personnel_type", "user_type", "person_state"], clean),
                "录入人": (["display_name", "source_login"], clean),
                "录入时间": (["legacy_created_at"], clean_datetime),
            },
            "optional_labels": {"操作"},
        },
        90: {
            "name": "社保人员登记",
            "model": "sc.hr.payroll.document",
            "legacy_table": "D_SCBSJS_BGGL_XZ_SBRY",
            "legacy_csv": "/mnt/artifacts/migration/scbs_legacy_social_person_visible_payload_v1.tsv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_source_id",
            "strip_record_key_suffix": True,
            "domain": [("legacy_source_table", "in", ["D_SCBSJS_BGGL_XZ_SBRY"])],
            "fields": {
                "单据编号": (["DJBH", "document_no"], clean),
                "单据日期": (["DJRQ", "document_date"], clean_date),
                "姓名": (["XM"], clean),
                "人员类型": (["RYLX"], clean),
                "身份证号码": (["SFZHM"], clean),
                "联系方式": (["LXFS"], clean),
                "证书费用": (["ZSFY"], clean_amount),
                "社保基数": (["SBJS"], clean_amount),
                "社保购买单位": (["ZS", "XMMC", "project_name"], clean),
                "人员状态": (["RYZT"], clean),
                "备注": (["BZ"], clean_visible_note),
                "录入人": (["LRR"], clean),
                "录入时间": (["LRSJ"], clean_datetime),
            },
            "optional_labels": {"个人证书"},
        },
        100: {
            "name": "社保登记",
            "model": "sc.hr.payroll.document",
            "legacy_table": "fresh_db_legacy_salary_line",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv",
            "legacy_key": "legacy_line_id",
            "record_key": "legacy_source_id",
            "domain": [("fact_type", "=", "social_registration")],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "单据编号": (["document_no"], clean),
                "社保购买单位": (["payer_unit", "company_name"], clean),
                "姓名": (["person_name"], clean),
                "类型": (["source_dataset"], clean),
                "购买人数": (["payment_people_count", "header_people_count"], clean_amount),
                "年度": (["salary_year"], clean_amount),
                "月份": (["salary_month"], clean_amount),
                "缴费金额": (["social_security"], clean_amount),
                "备注": (["line_note", "source_note"], clean_visible_note),
                "登记人": (["creator_name"], clean),
                "登记时间": (["created_time"], clean_datetime),
            },
            "optional_labels": {"联系方式"},
        },
        110: {
            "name": "工资登记",
            "model": "sc.hr.payroll.document",
            "legacy_table": "fresh_db_legacy_salary_line",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv",
            "legacy_key": "legacy_line_id",
            "record_key": "legacy_source_id",
            "domain": [("fact_type", "=", "salary_registration")],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "单据编号": (["document_no"], clean),
                "标题": (["title"], clean),
                "年份": (["salary_year"], clean_amount),
                "月份": (["salary_month"], clean_amount),
                "部门": (["department_name"], clean),
                "姓名": (["person_name"], clean),
                "发放单位": (["payer_unit", "company_name"], clean),
                "应发工资": (["gross_amount"], clean_amount),
                "实发工资": (["net_salary"], clean_amount),
                "备注": (["line_note", "source_note"], clean_visible_note),
                "发放人数": (["payment_people_count", "header_people_count"], clean_amount),
                "录入人": (["creator_name"], clean),
                "录入时间": (["created_time"], clean_datetime),
            },
            "optional_labels": {"附件", "财务支出登记状态"},
        },
        120: {
            "name": "补助",
            "model": "sc.hr.payroll.document",
            "legacy_table": "BGGL_XZ_BZ",
            "legacy_csv": "/mnt/artifacts/migration/scbs_legacy_subsidy_visible_payload_v1.tsv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_source_id",
            "domain": [("fact_type", "=", "subsidy")],
            "fields": {
                "状态": (["DJZT"], business_document_state_label),
                "项目名称": (["XMMC", "project_name"], clean),
                "单据编号": (["DJBH", "document_no"], clean),
                "补助事由": (["D_SCBSJS_BZSX", "SY"], clean_visible_note),
                "补助人": (["BZR", "RY"], clean),
                "补助金额": (["BZJE", "JE", "amount_total"], clean_amount),
                "录入人": (["LRR"], clean),
                "录入时间": (["LRSJ"], clean_datetime),
            },
            "optional_labels": {"年度", "月份", "部门"},
        },
        160: {
            "name": "投标报名管理",
            "model": "tender.bid",
            "legacy_table": "P_ZTB_GCBMGL",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_tender_registration_replay_payload_v1.csv",
            "legacy_key": "document_no",
            "record_key": "name",
            "domain": [("legacy_visible_project_name", "!=", False)],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "单据编号": (["document_no"], clean),
                "开标时间": (["opening_time", "bid_time"], clean_datetime),
                "项目名称": (["project_name"], clean_alias_text),
                "登记时间": (["registration_time", "created_time"], clean_datetime),
                "录入人": (["creator_name"], clean),
            },
            "optional_labels": {"推送结果"},
        },
        170: {
            "name": "投标报名费申请",
            "model": "tender.doc.purchase",
            "legacy_table": "BGGL_ZTBJHT_TBBM_TBBMFSQ",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_tender_doc_purchase_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "domain": [("legacy_source_table", "in", ["BGGL_ZTBJHT_TBBM_TBBMFSQ"])],
            "fields": {
                "单据状态": (["document_state"], tender_approval_state_label),
                "项目名称": (["project_name"], clean),
                "单据编号": (["document_no"], clean),
                "申请人": (["applicant_name"], clean),
                "申请日期": (["apply_date"], clean_date),
                "收款账号": (["receipt_bank_account"], clean),
                "开户行": (["receipt_bank_name"], clean_alias_text),
                "金额": (["amount"], clean_amount),
                "备注": (["note"], clean_visible_note),
                "收款人": (["receipt_payee_name", "receipt_partner_name"], clean),
                "付款方式": (["payment_method"], clean),
                "录入人": (["creator_name"], clean),
                "录入时间": (["created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        220: {
            "name": "借款申请",
            "model": "sc.financing.loan",
            "legacy_table": "BGGL_JHK_JKSQ",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_employee_loan_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "record_key_field": "legacy_record_id",
            "record_key_regex": r"BGGL_JHK_JKSQ:([0-9a-fA-F]+)",
            "domain": [("legacy_source_table", "=", "BGGL_JHK_JKSQ")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/BGGL_JHK_JKSQ_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "单据状态": (["DJZT", "legacy_state"], business_document_state_label),
                "项目名称": (["XMMC", "project_name"], clean_alias_text),
                "单据编号": (["DJBH", "document_no"], clean),
                "申请部门": (["SQBM"], clean),
                "申请时间": (["SQSJ"], clean_datetime),
                "申请人": (["SQR"], clean),
                "是否预算内": (["SFYSN"], clean),
                "实际借款金额": (["JKJE", "amount"], clean_amount),
                "主要资金使用安排": (["ZYZJSYAP", "purpose"], clean_visible_note),
                "收款人": (["SKR"], clean),
                "收款账户": (["SKZH"], clean),
                "开户银行": (["KHYH"], clean),
                "公司名称": (["GSMC"], clean),
                "备注": (["BZ"], clean_visible_note),
                "付款单位": (["FKDW"], clean),
                "收款单位": (["SKDW"], clean),
                "往来单位名称": (["WLDWMC"], clean),
                "往来单位账户": (["WLDWZH"], clean),
                "借款账号": (["ZKZH"], clean),
                "实际批复金额": (["SJPFJE"], clean_amount),
                "申请金额": (["SQJE"], clean_amount),
                "预计归还时间": (["YJGHSJ", "due_date"], clean_datetime),
                "借款类型": (["SJBMC", "source_type_label"], clean),
                "录入人": (["LRR", "creator_name"], clean),
                "录入时间": (["LRSJ", "created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        230: {
            "name": "还款登记",
            "model": "sc.financing.loan",
            "legacy_table": "BGGL_JHK_HKDJ",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_employee_loan_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "record_key_field": "legacy_record_id",
            "record_key_regex": r"BGGL_JHK_HKDJ:([0-9a-fA-F]+)",
            "domain": [("legacy_source_table", "=", "BGGL_JHK_HKDJ")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/BGGL_JHK_HKDJ_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "项目名称": (["XMMC", "project_name"], clean_alias_text),
                "单据状态": (["DJZT", "legacy_state"], business_document_state_label),
                "单据编号": (["DJBH", "document_no"], clean),
                "申请部门": (["SQBM"], clean),
                "申请时间": (["SQSJ"], clean_datetime),
                "申请人": (["SQR"], clean),
                "是否预算内": (["SFYSN"], clean),
                "借款金额": (["JKJE"], clean_amount),
                "往来单位名称": (["WLDWMC"], clean),
                "录入人": (["LRR", "creator_name"], clean),
                "录入时间": (["LRSJ", "created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        270: {
            "name": "承包人还项目款",
            "model": "sc.expense.claim",
            "legacy_table": "ZJGL_ZCDFSZ_FXJK_HK",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "strip_record_key_colon_suffix": True,
            "domain": [("legacy_source_table", "=", "ZJGL_ZCDFSZ_FXJK_HK")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/ZJGL_ZCDFSZ_FXJK_HK_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "单据状态": (["DJZT", "document_state"], business_document_state_label),
                "单据编号": (["DJBH", "document_no"], clean),
                "项目名称": (["XMMC", "project_name"], clean_alias_text),
                "借款人": (["JKR", "source_summary"], clean),
                "借款金额": (["JKJE"], clean_amount),
                "还款金额": (["HKJE", "amount"], clean_amount),
                "用途": (["YT"], clean_visible_note),
                "借款利率": (["JKLX"], clean_amount),
                "利息": (["LX"], clean_amount),
                "还款时间": (["HKSJ", "transaction_date"], clean_datetime),
                "备注": (["BZ", "note"], clean_visible_note),
                "录入人": (["LRR", "creator_name"], clean),
                "录入时间": (["LRSJ", "created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        280: {
            "name": "承包人借项目款",
            "model": "sc.financing.loan",
            "legacy_table": "ZJGL_ZCDFSZ_FXJK_JK",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_financing_loan_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "domain": [("legacy_source_table", "=", "ZJGL_ZCDFSZ_FXJK_JK")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/ZJGL_ZCDFSZ_FXJK_JK_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "单据状态": (["DJZT", "legacy_state"], business_document_state_label),
                "单据编号": (["DJBH", "document_no"], clean),
                "项目名称": (["XMMC", "legacy_project_name"], clean_alias_text),
                "借款人": (["JKR"], clean),
                "借款金额": (["JKJE", "source_amount"], clean_amount),
                "用途": (["YT", "purpose"], clean_visible_note),
                "约定期限": (["YDQX", "due_date"], clean_datetime),
                "借款利息": (["JKLX", "source_type_label"], clean_amount),
                "备注": (["BZ", "note"], clean_visible_note),
                "录入人": (["LRR"], clean),
                "录入时间": (["LRSJ"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        370: {
            "name": "项目借公司款登记",
            "model": "sc.financing.loan",
            "legacy_table": "ZJGL_ZJSZ_DKGL_DKDJ",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_financing_loan_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "domain": [("legacy_source_table", "=", "ZJGL_ZJSZ_DKGL_DKDJ")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/ZJGL_ZJSZ_DKGL_DKDJ_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "单据状态": (["DJZT", "legacy_state"], business_document_state_label),
                "单据编号": (["DJBH", "document_no"], clean),
                "项目名称": (["XMMC", "legacy_project_name"], clean_alias_text),
                "贷款金额": (["DKJE", "source_amount"], clean_amount),
                "到期利息": (["LX"], clean_amount),
                "还款金额": (["__CONST__:"], clean_amount),
                "未还款金额": (["__CONST__:"], clean_amount),
                "贷款日期": (["DKRQ", "document_date"], clean_datetime),
                "还款日期": (["HKRQ", "due_date"], clean_datetime),
                "贷款天数": (["DKSJ"], clean),
                "年利率": (["DKLL"], clean),
                "贷款账户": (["DKZH", "source_extra_label"], clean),
                "贷款银行": (["DKYH"], clean),
                "备注": (["BZ", "note"], clean_visible_note),
                "录入人": (["LRR"], clean),
                "录入时间": (["LRSJ"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        380: {
            "name": "项目还公司款登记",
            "model": "sc.financing.loan",
            "legacy_table": "ZJGL_ZJSZ_DKGL_HKDJ",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "strip_record_key_colon_suffix": True,
            "domain": [("legacy_source_table", "=", "ZJGL_ZJSZ_DKGL_HKDJ")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/ZJGL_ZJSZ_DKGL_HKDJ_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "单据状态": (["DJZT", "document_state"], business_document_state_label),
                "单据编号": (["DJBH", "document_no"], clean),
                "项目名称": (["XMMC", "project_name"], clean_alias_text),
                "还款金额": (["HKJE", "amount"], clean_amount),
                "实际还款天数": (["D_SCBSJS_SJHKTS"], clean_amount),
                "实际年利率": (["D_SCBSJS_SJNLL"], clean_amount),
                "贷款利息": (["DKLX"], clean_amount),
                "贷款银行": (["DKYH"], clean),
                "贷款账户": (["DKZH"], clean),
                "还款账户": (["HKZH"], clean),
                "填写人": (["TXR"], clean),
                "备注": (["BZ", "note"], clean_visible_note),
                "录入人": (["LRR", "creator_name"], clean),
                "录入时间": (["LRSJ", "created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        390: {
            "name": "开票申请",
            "model": "sc.invoice.registration",
            "legacy_table": "C_JXXP_KJFPSQ",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_income_invoice_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "domain": [("legacy_source_table", "=", "C_JXXP_KJFPSQ")],
            "merge_sources": [
                {"legacy_csv": "/mnt/artifacts/migration/C_JXXP_KJFPSQ_visible.tsv", "legacy_key": "legacy_record_id"}
            ],
            "fields": {
                "状态": (["DJZT", "document_state"], business_document_state_label),
                "开票状态": (["DJZT", "document_state"], business_document_state_label),
                "合同编号": (["HTBH", "contract_no"], clean),
                "项目名称": (["XMMC", "project_name"], clean_alias_text),
                "单据编号": (["DJBH", "document_no"], clean),
                "申请人": (["SQR", "creator_name"], clean),
                "预计回款日期": (["YJHKRQ", "expected_receipt_date"], clean_date),
                "申请日期": (["SQRQ", "document_date"], clean_date),
                "受票方名称": (["SPF_MC", "partner_name"], clean),
                "累计开票金额": (["LJKPJE"], clean_amount),
                "合同额": (["HTE", "amount_contract"], clean_amount),
                "本次开票张数": (["SQKPCS", "BCKP_ZS"], clean_amount),
                "本次开票金额": (["BCKPJE", "BCKP_JE", "amount_total"], clean_amount),
                "备注": (["BZ", "KPF_BZ", "note"], clean_visible_note),
                "录入人": (["LRR", "creator_name"], clean),
                "录入时间": (["LRSJ", "created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        400: {
            "name": "开票登记",
            "model": "sc.invoice.registration",
            "legacy_table": "C_JXXP_XXKPDJ",
            "legacy_csv": "/mnt/artifacts/migration/C_JXXP_XXKPDJ_visible.tsv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "domain": [("legacy_source_table", "=", "C_JXXP_XXKPDJ")],
            "fields": {
                "单据状态": (["DJZT"], business_document_state_label),
                "推送结果": (["D_SCBSJS_IsPush"], clean),
                "金蝶单据编号": (["OTHER_SYSTEM_CODE", "GJID"], clean),
                "单据编号": (["DJBH"], clean),
                "项目名称": (["XMMC"], clean_alias_text),
                "受票方名称": (["SPFMC"], clean),
                "含税金额": (["KPZJE", "KPZJE_1"], clean_amount),
                "税额": (["ZSE"], clean_amount),
                "不含税金额": (["BHSJE"], clean_amount),
                "附加税": (["D_SCBSJS_FJS"], clean_amount),
                "开票张数": (["KPZS", "KPZS_1"], clean_amount),
                "税率": (["__CONST__:"], clean),
                "关联回款金额": (["SKZJE"], clean_amount),
                "发票号": (["__CONST__:"], clean),
                "发票种类": (["FPZL"], clean),
                "开票单位": (["KPDW"], clean),
                "录入人": (["LRR"], clean),
                "开票日期": (["FPKJRQ"], clean_date),
                "录入时间": (["LRSJ"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        300: {
            "name": "扣款单",
            "model": "sc.tax.deduction.registration",
            "legacy_table": "C_ZFSQGL_KKD",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "record_key_field": "legacy_record_id",
            "record_key_regex": r"C_ZFSQGL_KKD:([0-9a-fA-F]+)",
            "domain": [("legacy_source_table", "in", ["C_ZFSQGL_KKD"])],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "单据编号": (["document_no"], clean),
                "项目名称": (["project_name"], clean_alias_text),
                "扣款单位": (["partner_name"], clean),
                "扣款金额": (["planned_amount"], clean_amount),
                "扣款事由": (["note"], first_line_business_note),
                "单据日期": (["document_date"], clean_date),
                "录入人": (["creator_name"], clean),
                "录入时间": (["created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        320: {
            "name": "账户间资金往来",
            "model": "sc.fund.account.operation",
            "legacy_table": "account_transaction",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "strip_record_key_colon_suffix": True,
            "domain": [("legacy_source_table", "in", ["C_FKGL_ZHJZJWL"])],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "项目名称": (["project_name"], clean_alias_text),
                "单据编号": (["document_no"], clean),
                "发生时间": (["transaction_date"], clean_date),
                "账户号码": (["account_name"], clean),
                "收款账户": (["counterparty_account_name"], clean),
                "金额": (["amount"], clean_amount),
                "转账类别": (["source_summary", "category"], clean),
                "事由": (["note", "source_summary"], clean_visible_note),
                "备注": (["note"], clean_visible_note),
                "录入人": (["creator_name"], clean),
                "录入时间": (["created_time"], clean_datetime),
            },
            "optional_labels": {"附件"},
        },
        330: {
            "name": "扣款实缴登记",
            "model": "sc.expense.claim",
            "legacy_table": "deduction_adjustment_line",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv",
            "legacy_key": "legacy_line_id",
            "record_key": "legacy_record_id",
            "strip_record_key_colon_suffix": True,
            "domain": [("claim_type", "=", "expense"), ("expense_type", "=", "扣款实缴登记")],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "单据编号": (["document_no"], clean),
                "项目名称": (["project_name"], clean_alias_text),
                "单据日期": (["document_date"], clean_date),
                "标题": (["title"], clean),
                "本次实缴数": (["current_actual_amount"], clean_amount),
                "是否退回": (["returned_flag"], clean),
                "上缴内容": (["adjustment_item_name"], clean),
                "本次计划已缴数": (["current_planned_amount"], clean_amount),
                "录入人": (["creator_name"], clean),
                "录入时间": (["created_time"], clean_datetime),
            },
        },
        340: {
            "name": "扣款实缴退回",
            "model": "sc.expense.claim",
            "legacy_table": "account_transaction",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "strip_record_key_colon_suffix": True,
            "domain": [("claim_type", "=", "deduction_refund"), ("expense_type", "=", "扣款实缴退回")],
            "fields": {
                "单据状态": (["document_state"], business_document_state_label),
                "项目名称": (["project_name"], clean_alias_text),
                "单据编号": (["document_no"], clean),
                "本次实缴数": (["amount"], clean_amount),
                "本次退回数": (["amount"], clean_amount),
                "上缴内容": (["category", "counterparty_account_name"], clean),
                "备注": (["note"], clean_visible_note),
                "录入人": (["creator_name"], clean),
                "单据日期": (["transaction_date"], clean_date),
            },
            "optional_labels": {"附件"},
        },
        420: {
            "name": "进项上报",
            "model": "sc.legacy.invoice.tax.fact",
            "legacy_table": "legacy_invoice_tax",
            "legacy_csv": "/mnt/artifacts/migration/fresh_db_legacy_invoice_tax_replay_payload_v1.csv",
            "legacy_key": "legacy_record_id",
            "record_key": "legacy_record_id",
            "domain": [],
            "fields": {
                "状态": (["legacy_state"], business_document_state_label),
                "单据编号": (["document_no"], clean),
                "项目名称": (["legacy_project_name"], clean_alias_text),
                "发票开具日期": (["document_date"], clean_date),
                "开票单位": (["legacy_partner_name"], clean),
                "发票提供人/单位": (["legacy_partner_name"], clean),
                "价税合计": (["source_amount"], clean_amount),
                "税额": (["source_tax_amount"], clean_amount),
                "不含税金额": (["source_amount"], clean_amount),
                "发票号码": (["document_no"], clean),
                "发票类型": (["invoice_type"], clean),
                "发票备注": (["note"], clean_visible_note),
            },
            "optional_labels": {"推送结果", "金蝶单据编号", "发票公司类型", "附件", "录入人", "录入时间"},
        },
    }
)


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 Legacy Visible Field Full Reconcile Probe",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | menu | status | records | fields | mismatches | unmapped labels |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {name} | {status} | {matched_records} | {mapped_field_count}/{contract_field_count} | "
            "{mismatch_count} | {unmapped_labels_text} |".format(**row)
        )
    lines.extend(["", "## Blocking Rows", "", "```json", json.dumps(payload["blocking_rows"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


artifact_dir = artifact_root()
ensure_visible_alias_payload_table()
refresh_business_entity_visible_unified_tsv()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
plans = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")

rows: list[dict[str, Any]] = []
for plan in plans:
    seq = int(plan.priority_sequence or 0)
    labels = contract_labels(plan)
    rule = FIELD_RULES.get(seq)
    row = {
        "seq": seq,
        "name": clean(plan.legacy_menu_name),
        "model": clean(plan.target_model),
        "contract_field_count": len(labels),
        "mapped_field_count": 0,
        "matched_records": 0,
        "missing_records": 0,
        "extra_new_records": 0,
        "mismatch_count": 0,
        "updated_field_count": 0,
        "mismatches": [],
        "unmapped_labels": [],
        "unmapped_labels_text": "",
        "status": "PASS",
    }
    if not labels:
        row["status"] = "NO_LIST_FIELDS"
        rows.append(row)
        continue
    if not rule:
        model_name = clean(plan.target_model)
        if model_name in env:  # noqa: F821
            domain = action_domain(plan.target_action_id)
            active_count = env[model_name].sudo().with_context(active_test=True).search_count(domain)  # noqa: F821
            row["matched_records"] = active_count
            if active_count == 0:
                row["status"] = "PASS"
                row["zero_active_record_reason"] = "no active records in user-visible action domain"
                rows.append(row)
                continue
        row["status"] = "FAIL_UNMAPPED_ENTRY_RULE"
        row["unmapped_labels"] = labels
        row["unmapped_labels_text"] = ";".join(labels)
        rows.append(row)
        continue

    optional = set(rule.get("optional_labels") or ())
    field_rules = rule.get("fields") or {}
    model_name = rule["model"]
    unmapped = [label for label in labels if label not in field_rules and label not in optional]
    row["mapped_field_count"] = len([label for label in labels if label in field_rules])
    row["unmapped_labels"] = unmapped
    row["unmapped_labels_text"] = ";".join(unmapped)
    if unmapped:
        domain = user_visible_domain(plan, rule)
        active_count = env[model_name].sudo().with_context(active_test=True).search_count(domain) if model_name in env else None  # noqa: F821
        if active_count == 0:
            row["status"] = "PASS"
            row["matched_records"] = 0
            row["zero_active_record_reason"] = "no active records in user-visible action domain"
            rows.append(row)
            continue
        row["status"] = "FAIL_UNMAPPED_FIELD_RULE"

    if model_name not in env:  # noqa: F821
        row["status"] = "FAIL_MODEL_MISSING"
        rows.append(row)
        continue

    legacy_rows = read_csv_rows(Path(rule["legacy_csv"]), rule["legacy_key"])
    for source in rule.get("merge_sources") or []:
        merge_csv_rows(legacy_rows, Path(source["legacy_csv"]), source["legacy_key"])
    secondary_rows = {
        name: read_csv_rows(Path(source["legacy_csv"]), source["legacy_key"])
        for name, source in (rule.get("secondary_sources") or {}).items()
    }
    fund_line_sums: dict[str, float] = {}
    if seq == 350 and "line" in secondary_rows:
        for line in secondary_rows["line"].values():
            if clean(line.get("active")) not in {"", "1", "True", "true"}:
                continue
            header_id = clean(line.get("legacy_header_id"))
            if not header_id:
                continue
            fund_line_sums[header_id] = fund_line_sums.get(header_id, 0.0) + max(numeric_amount(line.get("current_actual_amount")), 0.0)
    domain = user_visible_domain(plan, rule)
    records = env[model_name].sudo().with_context(active_test=True).search(domain)  # noqa: F821
    row["matched_records"] = len(records)
    for record in records:
        write_values: dict[str, str] = {}
        legacy_id = record_legacy_key(record, rule)
        legacy = legacy_rows.get(legacy_id)
        if not legacy:
            row["extra_new_records"] += 1
            if len(row["mismatches"]) < MAX_MISMATCH_SAMPLES:
                row["mismatches"].append({"id": record.id, "legacy_id": legacy_id, "note": "extra_new_record_not_in_legacy_snapshot"})
            continue
        for label, spec in field_rules.items():
            columns, normalizer = spec[0], spec[1]
            source_key = spec_source_key(spec)
            expected_row = legacy
            expected_legacy_id = legacy_id
            if source_key:
                source_rule = (rule.get("secondary_sources") or {}).get(source_key) or {}
                expected_legacy_id = record_secondary_key(record, source_rule)
                expected_row = secondary_rows.get(source_key, {}).get(expected_legacy_id)
                if not expected_row:
                    row["missing_records"] += 1
                    if len(row["mismatches"]) < MAX_MISMATCH_SAMPLES:
                        row["mismatches"].append(
                            {
                                "id": record.id,
                                "legacy_id": expected_legacy_id,
                                "label": label,
                                "source": source_key,
                                "error": "missing_secondary_legacy_row",
                            }
                        )
                    continue
            if columns and columns[0].startswith("__COMPUTED__:"):
                expected = normalizer(fund_confirmation_computed_value(legacy, fund_line_sums, columns[0]))
            else:
                expected = source_value(expected_row, columns, normalizer)
            actual = normalizer(visible_value(record, label))
            if seq == 350 and label in {"本期收款", "本期代扣代缴合计", "本期拨付金额合计", "合同金额", "累计开票金额", "上期留存余额"} and expected == "" and actual == "0":
                expected = "0"
            if seq == 360 and label in {"当前账户余额", "当前账户银行余额", "银行系统差额", "当日累计收入", "当日累计支出"} and expected == "" and actual == "0":
                expected = "0"
            if seq == 410 and label in {"金额", "不含税金额", "税额"} and expected == "" and actual == "0":
                expected = "0"
            if seq == 390 and label in {"合同额"} and expected == "" and actual == "0":
                expected = "0"
            if seq == 400 and label in {"税额", "不含税金额", "附加税", "关联回款金额"} and expected == "" and actual == "0":
                expected = "0"
            if expected != actual:
                if WRITE_VISIBLE_ALIAS:
                    write_values[label] = expected
                    continue
                row["mismatch_count"] += 1
                if len(row["mismatches"]) < MAX_MISMATCH_SAMPLES:
                    row["mismatches"].append(
                        {
                            "id": record.id,
                            "legacy_id": expected_legacy_id,
                            "source": source_key or "main",
                            "label": label,
                            "columns": columns,
                            "expected": expected,
                            "actual": actual,
                        }
                    )
        if write_values:
            row["updated_field_count"] += write_visible_alias_values(record, write_values)
    if row["missing_records"] or row["mismatch_count"]:
        row["status"] = "FAIL_VALUE_MISMATCH"
    rows.append(row)

blocking_rows = [row for row in rows if row["status"] not in {"PASS", "NO_LIST_FIELDS"}]
db_writes = sum(row.get("updated_field_count", 0) for row in rows)
if WRITE_VISIBLE_ALIAS and db_writes:
    env.cr.commit()  # noqa: F821
payload = {
    "status": "PASS" if not blocking_rows else "FAIL",
    "mode": "scbs_55_legacy_visible_field_full_reconcile_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "row_count": len(rows),
    "pass_count": len([row for row in rows if row["status"] == "PASS"]),
    "blocking_count": len(blocking_rows),
    "mapped_entry_count": len(FIELD_RULES),
    "required_entry_count": len([row for row in rows if row["contract_field_count"]]),
    "rows": rows,
    "blocking_rows": blocking_rows,
    "db_writes": db_writes,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print(
    "SCBS_55_LEGACY_VISIBLE_FIELD_FULL_RECONCILE="
    + json.dumps(
        {
            "status": payload["status"],
            "row_count": payload["row_count"],
            "pass_count": payload["pass_count"],
            "blocking_count": payload["blocking_count"],
            "mapped_entry_count": payload["mapped_entry_count"],
            "required_entry_count": payload["required_entry_count"],
            "output_json": str(artifact_dir / OUTPUT_JSON_NAME),
            "output_report": str(artifact_dir / OUTPUT_REPORT_NAME),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if blocking_rows:
    raise SystemExit(2)
