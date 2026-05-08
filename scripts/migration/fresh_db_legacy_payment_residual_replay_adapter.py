#!/usr/bin/env python3
"""Build replay payload for legacy payment facts not covered by runtime requests."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_payment_residual_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_payment_residual_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "source_table",
    "legacy_record_id",
    "legacy_pid",
    "payment_family",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "contract_legacy_id",
    "contract_no",
    "request_legacy_id",
    "planned_amount",
    "paid_amount",
    "invoice_amount",
    "payment_method",
    "bank_account",
    "handler_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "attachment_ref",
    "note",
    "active",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def date_sql(field: str) -> str:
    return f"COALESCE(CONVERT(varchar(23), {field}, 121), '')"


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-W",
        "-s",
        "\t",
        "-h",
        "-1",
        "-Q",
        sql,
    ]


def run_sql(sql: str) -> str:
    return subprocess.check_output(sqlcmd(sql), text=True)


def payload_sql() -> str:
    selects = [
        f"""
SELECT
  'C_ZFSQGL' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.PID")} AS legacy_pid,
  'outflow_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(10), h.f_SQRQ, 23), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.f_XMID")} AS project_legacy_id,
  {clean_sql("h.f_XMMC")} AS project_name,
  {clean_sql("h.f_GYSID")} AS partner_legacy_id,
  {clean_sql("h.f_GYSMC")} AS partner_name,
  {clean_sql("h.f_GYSHTID")} AS contract_legacy_id,
  {clean_sql("h.f_GYSHTBH")} AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.f_JHJE")} AS planned_amount,
  {clean_sql("h.f_SFJE")} AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.f_FKFSMC")} AS payment_method,
  {clean_sql("h.FKZH")} AS bank_account,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.f_LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.f_LRSJ, 121), '') AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("h.f_Remark")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'T_FK_Supplier' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'actual_outflow' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(10), h.f_FKRQ, 23), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(h.f_XMID)), ''), NULLIF(LTRIM(RTRIM(h.f_LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(h.XMMC, h.f_LYXM, h.TSXMMC)")} AS project_name,
  {clean_sql("h.f_SupplierID")} AS partner_legacy_id,
  {clean_sql("h.f_SupplierName")} AS partner_name,
  {clean_sql("h.f_HTID")} AS contract_legacy_id,
  {clean_sql("h.f_HTHB")} AS contract_no,
  {clean_sql("h.f_ZFSQGLId")} AS request_legacy_id,
  {clean_sql("h.f_FKJE")} AS planned_amount,
  {clean_sql("h.f_FKJE")} AS paid_amount,
  {clean_sql("h.f_FPJE")} AS invoice_amount,
  {clean_sql("h.f_FKFSMC")} AS payment_method,
  {clean_sql("h.FKZH")} AS bank_account,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.f_LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.f_LRSJ, 121), '') AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.f_BZ, h.Remark, h.BZ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_FK_Supplier h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_SD' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.f_PID")} AS legacy_pid,
  'manual_outflow_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.f_SQRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.f_XMID")} AS project_legacy_id,
  {clean_sql("h.f_XMMC")} AS project_name,
  {clean_sql("h.f_GYSID")} AS partner_legacy_id,
  {clean_sql("h.f_GYSMC")} AS partner_name,
  {clean_sql("h.f_GYSHTID")} AS contract_legacy_id,
  {clean_sql("h.f_GYSHTBH")} AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.f_JHJE")} AS planned_amount,
  {clean_sql("h.f_SFJE")} AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.f_FKFSMC")} AS payment_method,
  {clean_sql("CONCAT(COALESCE(h.f_KHH, ''), CASE WHEN NULLIF(h.f_ZH, '') IS NULL THEN '' ELSE ' / ' END, COALESCE(h.f_ZH, ''))")} AS bank_account,
  {clean_sql("h.f_TXR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.f_LRR")} AS creator_name,
  {date_sql("h.f_LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.f_Remark, h.f_ZXHTXX, h.XGBZ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL_SD h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_WJZ_WJZDJB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'tax_certificate_registration' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.LRSJ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.HTXDFMCNSRSBH")} AS partner_legacy_id,
  {clean_sql("h.HTXDFMC")} AS partner_name,
  '' AS contract_legacy_id,
  {clean_sql("h.HTBH")} AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.HTJE")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.JYFS")} AS payment_method,
  '' AS bank_account,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("CONCAT('合同名称:', COALESCE(h.HTMC, ''), '; 外经证地址:', COALESCE(h.KQYJYDZ, ''))")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_WJZ_WJZDJB h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_KKD' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'deduction_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.DJRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.KKDWID")} AS partner_legacy_id,
  {clean_sql("h.KKDW")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.KKJE")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.LX")} AS payment_method,
  '' AS bank_account,
  {clean_sql("h.LRR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.KKSY, h.D_GYXF_BZ, h.DJLY)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL_KKD h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_SJ_TP' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.f_PID")} AS legacy_pid,
  'tax_refund_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.f_QFRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.f_XMID")} AS project_legacy_id,
  {clean_sql("h.f_XMMC")} AS project_name,
  {clean_sql("h.f_SKDWID")} AS partner_legacy_id,
  {clean_sql("h.f_SKDWMC")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  {clean_sql("h.GLZFSQID")} AS request_legacy_id,
  {clean_sql("h.f_JHJE")} AS planned_amount,
  {clean_sql("h.f_SFJE")} AS paid_amount,
  {clean_sql("h.f_FPJE")} AS invoice_amount,
  {clean_sql("h.f_FKFSMC")} AS payment_method,
  {clean_sql("CONCAT(COALESCE(h.f_SKDWKHYH, ''), CASE WHEN NULLIF(h.f_SKDWZH, '') IS NULL THEN '' ELSE ' / ' END, COALESCE(h.f_SKDWZH, ''))")} AS bank_account,
  {clean_sql("h.f_LRR")} AS handler_name,
  {clean_sql("h.f_LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.f_LRR")} AS creator_name,
  {date_sql("h.f_LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.f_YT, h.f_Remark, h.f_SRLBMC)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL_SJ_TP h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_FKGL_YJDJ' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'deposit_payment_registration' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.DJRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.SKDWID")} AS partner_legacy_id,
  {clean_sql("h.SKDW")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.YJJE")} AS planned_amount,
  {clean_sql("h.YJJE")} AS paid_amount,
  '0' AS invoice_amount,
  '' AS payment_method,
  {clean_sql("COALESCE(h.SKZH, h.WSZFZH)")} AS bank_account,
  {clean_sql("h.DJR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.YT, h.BZ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_FKGL_YJDJ h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_BZJKD' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'deposit_borrow_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.DJRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.JKDWID")} AS partner_legacy_id,
  {clean_sql("h.JKDW")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.JKJE")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.LX")} AS payment_method,
  {clean_sql("h.ZHID")} AS bank_account,
  {clean_sql("h.LRR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.JKSY, h.DJLY, h.DXJE)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL_BZJKD h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_BZJGL_Pay_FBZJTHSQ' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'subcontract_deposit_refund_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.THRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(h.XMID, ''), NULLIF(h.TBXMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(h.XMMC, h.TBXMMC)")} AS project_name,
  {clean_sql("h.Y_SKDWID")} AS partner_legacy_id,
  {clean_sql("COALESCE(h.Y_SKDW, h.Y_JFMC)")} AS partner_name,
  {clean_sql("h.Y_ID")} AS contract_legacy_id,
  {clean_sql("h.Y_DJBH")} AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.THJE")} AS planned_amount,
  {clean_sql("h.THJE")} AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("COALESCE(h.FKFS, h.Y_FKFS)")} AS payment_method,
  {clean_sql("COALESCE(h.THZH, h.Y_ZFZH, h.Y_SKZH)")} AS bank_account,
  {clean_sql("h.TXR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.Y_BZ, h.Y_BZJLX)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_BZJGL_Pay_FBZJTHSQ h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_CWGL_FBXMJSFP' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'subcontract_settlement_invoice_header' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.JSRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  '' AS partner_legacy_id,
  {clean_sql("h.FBS")} AS partner_name,
  '' AS contract_legacy_id,
  {clean_sql("h.HTBH")} AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("COALESCE(h.LJYFK, 0) + COALESCE(h.WFKJE, 0)")} AS planned_amount,
  {clean_sql("h.LJYFK")} AS paid_amount,
  {clean_sql("COALESCE(h.LJYFK, 0) + COALESCE(h.WFKJE, 0)")} AS invoice_amount,
  '' AS payment_method,
  '' AS bank_account,
  {clean_sql("h.JSR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.BZ, h.SHKJ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_CWGL_FBXMJSFP h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_CWGL_FBXMJSFP_CB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'subcontract_settlement_invoice_line' AS payment_family,
  {clean_sql("COALESCE(parent.DJBH, h.ZBID)")} AS document_no,
  {date_sql("parent.JSRQ")} AS document_date,
  {clean_sql("parent.DJZT")} AS document_state,
  {clean_sql("parent.DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(h.XMID, ''), NULLIF(parent.XMID, ''))")} AS project_legacy_id,
  {clean_sql("parent.XMMC")} AS project_name,
  '' AS partner_legacy_id,
  {clean_sql("parent.FBS")} AS partner_name,
  '' AS contract_legacy_id,
  {clean_sql("parent.HTBH")} AS contract_no,
  {clean_sql("h.ZBID")} AS request_legacy_id,
  {clean_sql("h.YFJE")} AS planned_amount,
  '0' AS paid_amount,
  {clean_sql("h.YFJE")} AS invoice_amount,
  '' AS payment_method,
  '' AS bank_account,
  {clean_sql("parent.JSR")} AS handler_name,
  {clean_sql("parent.LRRID")} AS creator_legacy_user_id,
  {clean_sql("parent.LRR")} AS creator_name,
  {date_sql("parent.LRSJ")} AS created_time,
  {clean_sql("parent.FJ")} AS attachment_ref,
  {clean_sql("CONCAT('范围:', COALESCE(h.FBFW, ''), '; 材料发票:', COALESCE(h.CLFP, ''))")} AS note,
  CASE WHEN ISNULL(parent.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_CWGL_FBXMJSFP_CB h
LEFT JOIN dbo.ZJGL_CWGL_FBXMJSFP parent ON parent.Id = h.ZBID
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_SZQR_ZFQRB_CB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'payment_confirmation_line' AS payment_family,
  {clean_sql("h.ZBID")} AS document_no,
  '' AS document_date,
  '' AS document_state,
  '0' AS deleted_flag,
  '' AS project_legacy_id,
  '' AS project_name,
  {clean_sql("h.SKDWID")} AS partner_legacy_id,
  {clean_sql("h.SKDW")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  {clean_sql("h.ZFSQID")} AS request_legacy_id,
  {clean_sql("h.BCZFJE")} AS planned_amount,
  {clean_sql("h.BCZFJE")} AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.SFQDHT")} AS payment_method,
  {clean_sql("COALESCE(h.KHZH, h.KHH)")} AS bank_account,
  '' AS handler_name,
  '' AS creator_legacy_user_id,
  '' AS creator_name,
  '' AS created_time,
  '' AS attachment_ref,
  {clean_sql("COALESCE(h.FKNR, h.BZ, h.SKDW_LX)")} AS note,
  '1' AS active
FROM dbo.ZJGL_SZQR_ZFQRB_CB h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_SJ_CB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'tax_payment_budget_line' AS payment_family,
  {clean_sql("h.ZBID")} AS document_no,
  '' AS document_date,
  '' AS document_state,
  '0' AS deleted_flag,
  '' AS project_legacy_id,
  '' AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  {clean_sql("h.ZBID")} AS request_legacy_id,
  {clean_sql("h.JHJE")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.NKKMMC")} AS payment_method,
  '' AS bank_account,
  '' AS handler_name,
  '' AS creator_legacy_user_id,
  '' AS creator_name,
  '' AS created_time,
  '' AS attachment_ref,
  {clean_sql("CONCAT('内控科目:', COALESCE(h.NKKMBH, ''), '/', COALESCE(h.NKKMMC, ''), '; 是否内控控制:', COALESCE(CONVERT(varchar(max), h.SFNKKZ), ''))")} AS note,
  '1' AS active
FROM dbo.C_ZFSQGL_SJ_CB h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_SWGL_SJSWLXSZ' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_pid,
  'tax_business_type_setting' AS payment_family,
  {clean_sql("h.Guid")} AS document_no,
  {date_sql("h.f_Tree_importTime")} AS document_date,
  {clean_sql("h.f_Tree_del")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.f_Tree_XMID")} AS project_legacy_id,
  '' AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.SLBL")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.SWLX")} AS payment_method,
  '' AS bank_account,
  {clean_sql("h.f_Tree_importPerson")} AS handler_name,
  '' AS creator_legacy_user_id,
  {clean_sql("h.f_Tree_importPerson")} AS creator_name,
  {date_sql("h.f_Tree_importTime")} AS created_time,
  '' AS attachment_ref,
  {clean_sql("CONCAT('税务类型:', COALESCE(h.f_Tree_Name, ''), '; 计税类型:', COALESCE(h.JSJSLXMC, ''), '; 来源:', COALESCE(h.LY, ''))")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_SWGL_SJSWLXSZ h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_KKD_CB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'deduction_request_line' AS payment_family,
  {clean_sql("COALESCE(parent.DJBH, h.ZBID)")} AS document_no,
  {date_sql("parent.DJRQ")} AS document_date,
  {clean_sql("parent.DJZT")} AS document_state,
  {clean_sql("parent.DEL")} AS deleted_flag,
  {clean_sql("parent.XMID")} AS project_legacy_id,
  {clean_sql("parent.XMMC")} AS project_name,
  {clean_sql("parent.KKDWID")} AS partner_legacy_id,
  {clean_sql("parent.KKDW")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  {clean_sql("h.ZBID")} AS request_legacy_id,
  {clean_sql("h.KKJE")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.KKLX")} AS payment_method,
  '' AS bank_account,
  {clean_sql("parent.LRR")} AS handler_name,
  {clean_sql("parent.LRRID")} AS creator_legacy_user_id,
  {clean_sql("parent.LRR")} AS creator_name,
  {date_sql("parent.LRSJ")} AS created_time,
  {clean_sql("parent.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.KKSY, parent.KKSY)")} AS note,
  CASE WHEN ISNULL(parent.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL_KKD_CB h
LEFT JOIN dbo.C_ZFSQGL_KKD parent ON parent.Id = h.ZBID
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_SZQR_ZFQRB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'payment_confirmation_header' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.DJRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  {clean_sql("h.DKQRID")} AS request_legacy_id,
  {clean_sql("h.BCZFQR")} AS planned_amount,
  {clean_sql("h.BCZFQR")} AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.QS")} AS payment_method,
  '' AS bank_account,
  {clean_sql("h.TXR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("CONCAT('本期可用余额:', COALESCE(CONVERT(varchar(max), h.BQKYYE), ''), '; 下期可用余额:', COALESCE(CONVERT(varchar(max), h.XQKYYE), ''), '; ', COALESCE(h.BZ, ''))")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_SZQR_ZFQRB h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_SWGL_SJSWLXSZ_Templet' AS source_table,
  {clean_sql("h.ID")} AS legacy_record_id,
  '' AS legacy_pid,
  'tax_business_type_template' AS payment_family,
  {clean_sql("h.GUID")} AS document_no,
  {date_sql("h.F_TREE_IMPORTTIME")} AS document_date,
  {clean_sql("h.F_TREE_DEL")} AS document_state,
  {clean_sql("h.F_TREE_DEL")} AS deleted_flag,
  {clean_sql("h.F_TREE_XMID")} AS project_legacy_id,
  '' AS project_name,
  '' AS partner_legacy_id,
  '' AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.SLBL")} AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.SWLX")} AS payment_method,
  '' AS bank_account,
  {clean_sql("h.F_TREE_IMPORTPERSON")} AS handler_name,
  '' AS creator_legacy_user_id,
  {clean_sql("h.F_TREE_IMPORTPERSON")} AS creator_name,
  {date_sql("h.F_TREE_IMPORTTIME")} AS created_time,
  '' AS attachment_ref,
  {clean_sql("CONCAT('模板:', COALESCE(h.F_MBMC, ''), '; 税务类型:', COALESCE(h.F_TREE_NAME, ''), '; 计税类型:', COALESCE(h.JSJSLXMC, ''))")} AS note,
  CASE WHEN COALESCE(NULLIF(h.F_TREE_DEL, ''), '0') IN ('0', 'False', 'false') THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_SWGL_SJSWLXSZ_Templet h
WHERE h.ID IS NOT NULL
""",
        f"""
SELECT
  'ZJGL_ZSJYGL' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'certificate_borrowing' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  {date_sql("h.SQRQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(h.JYXMID, ''), NULLIF(h.XMID, ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(h.JYXMMC, h.XMMC)")} AS project_name,
  {clean_sql("h.JYRID")} AS partner_legacy_id,
  {clean_sql("h.JYR")} AS partner_name,
  '' AS contract_legacy_id,
  '' AS contract_no,
  '' AS request_legacy_id,
  '0' AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("COALESCE(h.JYXS_NR, h.JYXS)")} AS payment_method,
  '' AS bank_account,
  {clean_sql("h.FZRMC")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  {date_sql("h.LRSJ")} AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.BT, h.BZ, h.SDYJ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_ZSJYGL h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'C_ZFSQGL_GZ_CB' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_pid,
  'outflow_work_type_line' AS payment_family,
  {clean_sql("COALESCE(parent.DJBH, h.ZBID)")} AS document_no,
  {date_sql("parent.f_SQRQ")} AS document_date,
  {clean_sql("parent.DJZT")} AS document_state,
  {clean_sql("parent.DEL")} AS deleted_flag,
  {clean_sql("parent.f_XMID")} AS project_legacy_id,
  {clean_sql("parent.f_XMMC")} AS project_name,
  {clean_sql("parent.f_GYSID")} AS partner_legacy_id,
  {clean_sql("COALESCE(NULLIF(parent.f_GYSMC, ''), NULLIF(h.JSDW, ''))")} AS partner_name,
  {clean_sql("parent.f_GYSHTID")} AS contract_legacy_id,
  {clean_sql("parent.f_GYSHTBH")} AS contract_no,
  {clean_sql("h.ZBID")} AS request_legacy_id,
  '0' AS planned_amount,
  '0' AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.GZMC")} AS payment_method,
  '' AS bank_account,
  {clean_sql("parent.JBR")} AS handler_name,
  {clean_sql("parent.LRRID")} AS creator_legacy_user_id,
  {clean_sql("parent.f_LRR")} AS creator_name,
  {date_sql("parent.f_LRSJ")} AS created_time,
  {clean_sql("parent.FJ")} AS attachment_ref,
  {clean_sql("CONCAT('工种:', COALESCE(h.GZID, ''), '/', COALESCE(h.GZMC, ''), '; 工种单位:', COALESCE(h.GZDW, ''), '; 结算单位:', COALESCE(h.JSDW, ''), '; ', COALESCE(h.BZ, ''))")} AS note,
  CASE WHEN ISNULL(parent.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL_GZ_CB h
LEFT JOIN dbo.C_ZFSQGL parent ON parent.Id = h.ZBID
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
    ]
    return "\nSET NOCOUNT ON;\n" + "\nUNION ALL\n".join(selects) + "\nORDER BY source_table, legacy_record_id;\n"


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(payload_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(FIELDS)
            for line in proc.stdout:
                stripped = line.strip()
                if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                    continue
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) != len(FIELDS):
                    raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code})
    return count


def scalar(sql: str) -> int:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return int(stripped)
    return 0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    rows = write_csv_payload()
    table_counts: dict[str, int] = {}
    active_rows = 0
    planned_sum = Decimal("0")
    paid_sum = Decimal("0")
    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            table = row.get("source_table") or ""
            table_counts[table] = table_counts.get(table, 0) + 1
            if row.get("active") == "1":
                active_rows += 1
            for key in ("planned_amount", "paid_amount"):
                raw = (row.get(key) or "").strip()
                if not raw:
                    continue
                try:
                    amount = Decimal(raw)
                except InvalidOperation:
                    continue
                if key == "planned_amount":
                    planned_sum += amount
                else:
                    paid_sum += amount
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_payment_residual_replay_adapter",
        "total_rows": rows,
        "active_rows": active_rows,
        "outflow_request_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_ZFSQGL;"),
        "actual_outflow_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_FK_Supplier;"),
        "table_counts": table_counts,
        "planned_amount_sum": str(planned_sum),
        "paid_amount_sum": str(paid_sum),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_payment_residual_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_PAYMENT_RESIDUAL_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
