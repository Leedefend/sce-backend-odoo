#!/usr/bin/env python3
"""Build replay payload for legacy workflow detail facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_workflow_detail_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_workflow_detail_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "source_table",
    "legacy_record_id",
    "legacy_parent_id",
    "legacy_pid",
    "fact_type",
    "source_dataset",
    "document_no",
    "document_title",
    "business_table",
    "business_id",
    "project_legacy_id",
    "project_name",
    "actor_legacy_user_id",
    "actor_name",
    "target_legacy_user_id",
    "target_name",
    "event_time",
    "status_code",
    "step_legacy_id",
    "step_name",
    "template_legacy_id",
    "detail_status_legacy_id",
    "detail_step_legacy_id",
    "message",
    "note",
    "attachment_ref",
    "pc_url",
    "mobile_url",
    "active",
]

SOURCE_TABLES = [
    "S_Execute_DetailStatus",
    "S_Execute_Detail_Step",
    "S_Execute_OtherReader",
    "S_Execute_CancelRecord",
    "S_Execute_AdminAuditRecord",
    "S_MessageRecord",
    "S_Execute_PersonComment",
    "S_Execute_BackAuditPassBill",
    "S_Execute_Detail_Step_AddAuditPerson",
    "S_Execute_Consult",
    "S_NoticeMessage",
    "S_GeTui_UserAppCid",
    "S_MessageRecord_Read",
    "S_FieldMaintenance",
]


def text_sql(expr: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {expr}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def date_sql(expr: str) -> str:
    return f"COALESCE(CONVERT(varchar(23), {expr}, 121), '')"


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-b",
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
  'S_Execute_DetailStatus' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'detail_status' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  '' AS document_no,
  {text_sql("h.BT")} AS document_title,
  {text_sql("h.f_GLYWDLJ")} AS business_table,
  {text_sql("h.f_GLYWDID")} AS business_id,
  {text_sql("h.XMID")} AS project_legacy_id,
  '' AS project_name,
  {text_sql("COALESCE(h.TJRID, h.f_DJLRRId)")} AS actor_legacy_user_id,
  {text_sql("COALESCE(h.TJR, h.f_DJLRR)")} AS actor_name,
  {text_sql("h.f_DJLRRId")} AS target_legacy_user_id,
  {text_sql("h.f_DJLRR")} AS target_name,
  {date_sql("COALESCE(h.LRSJ, h.f_DJRQ, h.f_CYRQ, h.f_SHJSRQ)")} AS event_time,
  {text_sql("CONCAT('sfsjjs=', COALESCE(CONVERT(varchar(max), h.f_SFSHJS), ''), '; urgent=', COALESCE(CONVERT(varchar(max), h.SFJJ), ''))")} AS status_code,
  {text_sql("h.S_Setup_Step_IdS")} AS step_legacy_id,
  '' AS step_name,
  {text_sql("h.S_Setup_Template_Id")} AS template_legacy_id,
  {text_sql("h.Id")} AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.Bussiness_BZ")} AS message,
  {text_sql("h.BILL_FIELD_INFO")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_DetailStatus h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_Detail_Step' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.PARENTID")} AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'detail_step' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("COALESCE(h.f_DJBH, h.f_DJBH_Default)")} AS document_no,
  {text_sql("h.ADD_STEP_TEXT")} AS document_title,
  {text_sql("h.f_GLYWDLJ")} AS business_table,
  {text_sql("h.f_GLYWDID")} AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  {text_sql("COALESCE(h.CBRID, h.PARENT_BLR_ID, h.f_YBLRID)")} AS actor_legacy_user_id,
  {text_sql("COALESCE(h.CBR, h.YBLRNames)")} AS actor_name,
  {text_sql("h.f_DBLRID")} AS target_legacy_user_id,
  {text_sql("h.YBLRNames")} AS target_name,
  {date_sql("COALESCE(h.LRSJ, h.CBSJ, h.f_CXSJ)")} AS event_time,
  {text_sql("CONCAT('spzt=', COALESCE(CONVERT(varchar(max), h.f_SPZT), ''), '; timeout=', COALESCE(CONVERT(varchar(max), h.f_SFCS), ''), '; reject=', COALESCE(CONVERT(varchar(max), h.IsReject), ''))")} AS status_code,
  {text_sql("h.S_Setup_Step_Id")} AS step_legacy_id,
  {text_sql("h.f_BLSXLXMC")} AS step_name,
  '' AS template_legacy_id,
  {text_sql("h.S_Execute_DetailStatus_Id")} AS detail_status_legacy_id,
  {text_sql("h.Id")} AS detail_step_legacy_id,
  {text_sql("h.f_BZ")} AS message,
  {text_sql("CONCAT('传阅:', COALESCE(h.CSRNameS, ''), '; 办理人:', COALESCE(h.YBLRNames, ''))")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_Detail_Step h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_OtherReader' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.S_Execute_DetailStatus_Id")} AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'other_reader' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  '' AS document_no,
  {text_sql("h.Source")} AS document_title,
  '' AS business_table,
  {text_sql("COALESCE(h.business_Id, h.DJID)")} AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.f_SPRId")} AS actor_legacy_user_id,
  {text_sql("h.f_SPR")} AS actor_name,
  {text_sql("h.f_ZYRID")} AS target_legacy_user_id,
  {text_sql("h.f_SPR")} AS target_name,
  {date_sql("COALESCE(h.f_CYRQ, h.f_LRRQ)")} AS event_time,
  {text_sql("CONCAT('read=', COALESCE(h.f_SFYCY, ''), '; urgent=', COALESCE(h.JJCD, ''))")} AS status_code,
  {text_sql("h.S_Setup_Step_Id")} AS step_legacy_id,
  '' AS step_name,
  {text_sql("h.S_Setup_Template_Id")} AS template_legacy_id,
  {text_sql("h.S_Execute_DetailStatus_Id")} AS detail_status_legacy_id,
  {text_sql("h.S_Execute_Detail_Step_Id")} AS detail_step_legacy_id,
  {text_sql("h.f_BZ")} AS message,
  {text_sql("h.Source")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_OtherReader h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_CancelRecord' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'cancel_record' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {text_sql("h.YWMC")} AS document_title,
  {text_sql("h.BMC")} AS business_table,
  {text_sql("COALESCE(h.YWID, h.DJID)")} AS business_id,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("COALESCE(h.CXRID, h.TXRID)")} AS actor_legacy_user_id,
  {text_sql("h.CXR")} AS actor_name,
  {text_sql("h.TXRID")} AS target_legacy_user_id,
  {text_sql("h.TXR")} AS target_name,
  {date_sql("h.CXSJ")} AS event_time,
  {text_sql("CONCAT('result=', COALESCE(CONVERT(varchar(max), h.result), ''), '; type=', COALESCE(h.CXLX, ''))")} AS status_code,
  {text_sql("h.CONFIGID")} AS step_legacy_id,
  '' AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.CXLY")} AS message,
  {text_sql("h.DJTXR")} AS note,
  {text_sql("h.FJ")} AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_CancelRecord h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_AdminAuditRecord' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'admin_audit_record' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {text_sql("h.YWMC")} AS document_title,
  {text_sql("h.BMC")} AS business_table,
  {text_sql("h.DJID")} AS business_id,
  '' AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("h.DSRID")} AS actor_legacy_user_id,
  {text_sql("h.DSR")} AS actor_name,
  {text_sql("h.TZRIDPersonids")} AS target_legacy_user_id,
  {text_sql("h.DJTXR")} AS target_name,
  {date_sql("h.DSSJ")} AS event_time,
  {text_sql("h.DSLY")} AS status_code,
  {text_sql("h.S_Setup_Step_Id")} AS step_legacy_id,
  '' AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  {text_sql("h.S_Execute_Detail_Step_Id")} AS detail_step_legacy_id,
  {text_sql("h.DSLY")} AS message,
  {text_sql("h.TXR")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_AdminAuditRecord h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_MessageRecord' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.Pid")} AS legacy_pid,
  'message_record' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {text_sql("h.Function_Name")} AS document_title,
  {text_sql("h.TableName")} AS business_table,
  {text_sql("h.BillID")} AS business_id,
  {text_sql("h.XMID")} AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.CreateUserId")} AS actor_legacy_user_id,
  {text_sql("h.CreateUserName")} AS actor_name,
  {text_sql("h.ReceiveId")} AS target_legacy_user_id,
  '' AS target_name,
  {date_sql("h.SendTime")} AS event_time,
  {text_sql("CONCAT('up=', COALESCE(CONVERT(varchar(max), h.IsUp), ''), '; receive_type=', COALESCE(CONVERT(varchar(max), h.ReceiveType), ''), '; send_mode=', COALESCE(CONVERT(varchar(max), h.SendMode), ''), '; action=', COALESCE(h.Action, ''))")} AS status_code,
  '' AS step_legacy_id,
  '' AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.SendContent")} AS message,
  {text_sql("h.Function_BZ")} AS note,
  '' AS attachment_ref,
  {text_sql("h.Pc_VisitUrl")} AS pc_url,
  {text_sql("h.Mobile_VisitUrl")} AS mobile_url,
  CASE WHEN ISNULL(h.Del, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.S_MessageRecord h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_PersonComment' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.S_Execute_DetailStatus_Id")} AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'person_comment' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {text_sql("h.S_Setup_Business_Name")} AS document_title,
  {text_sql("h.BMC")} AS business_table,
  {text_sql("h.DJID")} AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.PLRID")} AS actor_legacy_user_id,
  {text_sql("h.PLR")} AS actor_name,
  '' AS target_legacy_user_id,
  '' AS target_name,
  {date_sql("h.PLSJ")} AS event_time,
  {text_sql("h.SPZT")} AS status_code,
  {text_sql("h.S_Setup_Business_Id")} AS step_legacy_id,
  '' AS step_name,
  '' AS template_legacy_id,
  {text_sql("h.S_Execute_DetailStatus_Id")} AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.PLNR")} AS message,
  '' AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_PersonComment h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_BackAuditPassBill' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.S_Execute_DetailStatus_ID")} AS legacy_parent_id,
  {text_sql("h.pid")} AS legacy_pid,
  'back_audit_pass_bill' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {text_sql("h.YWMC")} AS document_title,
  {text_sql("h.TableName")} AS business_table,
  {text_sql("h.DJID")} AS business_id,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("COALESCE(h.SQRUserId, h.SQRPersonId)")} AS actor_legacy_user_id,
  {text_sql("h.SQR")} AS actor_name,
  {text_sql("h.GlyUserIds")} AS target_legacy_user_id,
  {text_sql("h.GlyNames")} AS target_name,
  {date_sql("h.SQSJ")} AS event_time,
  '' AS status_code,
  '' AS step_legacy_id,
  '' AS step_name,
  {text_sql("h.S_Setup_Template_Id")} AS template_legacy_id,
  {text_sql("h.S_Execute_DetailStatus_ID")} AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.CXYY")} AS message,
  {text_sql("h.f_S_setup_business_Id")} AS note,
  '' AS attachment_ref,
  {text_sql("h.PC_Url")} AS pc_url,
  {text_sql("h.Mobile_Url")} AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_BackAuditPassBill h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_Detail_Step_AddAuditPerson' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.S_Execute_Detail_Step_Id")} AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'add_audit_person' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  '' AS document_title,
  {text_sql("h.tableName")} AS business_table,
  {text_sql("COALESCE(h.business_Id, h.DJID)")} AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.LRRID")} AS actor_legacy_user_id,
  {text_sql("h.LRR")} AS actor_name,
  {text_sql("h.AuditPersonId")} AS target_legacy_user_id,
  {text_sql("h.AuditPersonName")} AS target_name,
  {date_sql("h.LRSJ")} AS event_time,
  {text_sql("h.IsAllowUpdate")} AS status_code,
  {text_sql("h.Step_Id")} AS step_legacy_id,
  '' AS step_name,
  {text_sql("h.S_Setup_Template_Id")} AS template_legacy_id,
  {text_sql("h.S_Execute_DetailStatus_Id")} AS detail_status_legacy_id,
  {text_sql("h.S_Execute_Detail_Step_Id")} AS detail_step_legacy_id,
  '' AS message,
  {text_sql("h.f_GLYWDLJ")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_Execute_Detail_Step_AddAuditPerson h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_Execute_Consult' AS source_table,
  {text_sql("h.ID")} AS legacy_record_id,
  {text_sql("h.TREEPID")} AS legacy_parent_id,
  {text_sql("h.PID")} AS legacy_pid,
  'consult' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  '' AS document_no,
  {text_sql("h.ConsultType")} AS document_title,
  '' AS business_table,
  {text_sql("COALESCE(h.S_Setup_Business_Id, h.DJID)")} AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.FQRID")} AS actor_legacy_user_id,
  {text_sql("h.FQR")} AS actor_name,
  {text_sql("h.JSRIDS")} AS target_legacy_user_id,
  {text_sql("h.JSRS")} AS target_name,
  {date_sql("h.FQSJ")} AS event_time,
  {text_sql("CONCAT('finished=', COALESCE(h.SFYJGBHF, ''))")} AS status_code,
  {text_sql("h.S_Setup_Step_Id")} AS step_legacy_id,
  '' AS step_name,
  {text_sql("h.S_Setup_Template_Id")} AS template_legacy_id,
  {text_sql("h.S_EXECUTE_DETAILSTATUS_ID")} AS detail_status_legacy_id,
  {text_sql("h.S_EXECUTE_DETAIL_STEP_ID")} AS detail_step_legacy_id,
  {text_sql("h.ZXNR")} AS message,
  {text_sql("h.ApprovalPID")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.S_Execute_Consult h
WHERE NULLIF(LTRIM(RTRIM(h.ID)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_NoticeMessage' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.Pid")} AS legacy_pid,
  'notice_message' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("h.DJBH")} AS document_no,
  {text_sql("h.BT")} AS document_title,
  '' AS business_table,
  '' AS business_id,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("COALESCE(h.LRRID, h.PersonId)")} AS actor_legacy_user_id,
  {text_sql("COALESCE(h.LRR, h.FBR)")} AS actor_name,
  {text_sql("COALESCE(h.FBFW_RYIDS, h.FBFW_RYID, h.FBFW_JSID)")} AS target_legacy_user_id,
  {text_sql("COALESCE(h.FBFW_RY, h.FBFW_JS, h.CYFW)")} AS target_name,
  {date_sql("COALESCE(h.FBRQ, h.LRSJ)")} AS event_time,
  {text_sql("CONCAT('state=', COALESCE(CONVERT(varchar(max), h.State), ''), '; sticky=', COALESCE(CONVERT(varchar(max), h.SFZD), ''), '; type=', COALESCE(CONVERT(varchar(max), h.LX), ''))")} AS status_code,
  {text_sql("h.TGLXID")} AS step_legacy_id,
  {text_sql("h.TGLX")} AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.FBNR")} AS message,
  {text_sql("h.TX")} AS note,
  {text_sql("COALESCE(h.FJ, h.BTTP)")} AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  '1' AS active
FROM dbo.S_NoticeMessage h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_GeTui_UserAppCid' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  '' AS legacy_parent_id,
  {text_sql("h.Pid")} AS legacy_pid,
  'push_channel_binding' AS fact_type,
  '' AS source_dataset,
  '' AS document_no,
  {text_sql("h.Platform")} AS document_title,
  '' AS business_table,
  '' AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.UserId")} AS actor_legacy_user_id,
  {text_sql("h.UserName")} AS actor_name,
  {text_sql("h.UserId")} AS target_legacy_user_id,
  {text_sql("h.UserName")} AS target_name,
  {date_sql("h.LRSJ")} AS event_time,
  {text_sql("h.State")} AS status_code,
  '' AS step_legacy_id,
  '' AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("h.AppCid")} AS message,
  {text_sql("h.Platform")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  CASE WHEN ISNULL(h.State, 1) = 1 THEN '1' ELSE '0' END AS active
FROM dbo.S_GeTui_UserAppCid h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_MessageRecord_Read' AS source_table,
  {text_sql("h.Id")} AS legacy_record_id,
  {text_sql("h.S_MessageRecordId")} AS legacy_parent_id,
  '' AS legacy_pid,
  'message_read_receipt' AS fact_type,
  {text_sql("h.SJBMC")} AS source_dataset,
  {text_sql("msg.DJBH")} AS document_no,
  {text_sql("msg.Function_Name")} AS document_title,
  {text_sql("msg.TableName")} AS business_table,
  {text_sql("msg.BillID")} AS business_id,
  {text_sql("msg.XMID")} AS project_legacy_id,
  '' AS project_name,
  {text_sql("h.ReadUserId")} AS actor_legacy_user_id,
  {text_sql("h.ReadUserName")} AS actor_name,
  {text_sql("h.ReadPersonId")} AS target_legacy_user_id,
  {text_sql("h.ReadUserName")} AS target_name,
  {date_sql("msg.SendTime")} AS event_time,
  {text_sql("h.ReadModel")} AS status_code,
  '' AS step_legacy_id,
  '' AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("msg.SendContent")} AS message,
  {text_sql("CONCAT('read message:', COALESCE(h.S_MessageRecordId, ''))")} AS note,
  '' AS attachment_ref,
  {text_sql("msg.Pc_VisitUrl")} AS pc_url,
  {text_sql("msg.Mobile_VisitUrl")} AS mobile_url,
  '1' AS active
FROM dbo.S_MessageRecord_Read h
LEFT JOIN dbo.S_MessageRecord msg ON msg.Id = h.S_MessageRecordId
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
""",
        f"""
SELECT
  'S_FieldMaintenance' AS source_table,
  {text_sql("h.ID")} AS legacy_record_id,
  '' AS legacy_parent_id,
  '' AS legacy_pid,
  'field_maintenance' AS fact_type,
  '' AS source_dataset,
  {text_sql("h.FunctionId")} AS document_no,
  {text_sql("h.FunctionName")} AS document_title,
  {text_sql("h.FunctionId")} AS business_table,
  '' AS business_id,
  '' AS project_legacy_id,
  '' AS project_name,
  '' AS actor_legacy_user_id,
  {text_sql("h.ImprotPerson")} AS actor_name,
  '' AS target_legacy_user_id,
  '' AS target_name,
  {date_sql("h.ImportDate")} AS event_time,
  {text_sql("CONCAT('invalid=', COALESCE(h.IsInvalid, ''), '; field=', COALESCE(CONVERT(varchar(max), h.IsField), ''), '; export=', COALESCE(CONVERT(varchar(max), h.IsExport), ''))")} AS status_code,
  '' AS step_legacy_id,
  {text_sql("h.CommandName")} AS step_name,
  '' AS template_legacy_id,
  '' AS detail_status_legacy_id,
  '' AS detail_step_legacy_id,
  {text_sql("COALESCE(h.FieldNameCN, h.FieldName, h.FieldNameEN)")} AS message,
  {text_sql("CONCAT('字段:', COALESCE(h.FieldNameEN, ''), '/', COALESCE(h.FieldNameCN, ''), '; 类型:', COALESCE(h.FieldType, ''), '; 控件:', COALESCE(h.ContrType, ''), '; 宽度:', COALESCE(h.Width, ''))")} AS note,
  '' AS attachment_ref,
  '' AS pc_url,
  '' AS mobile_url,
  CASE WHEN COALESCE(NULLIF(h.IsInvalid, ''), '0') IN ('0', 'False', 'false') THEN '1' ELSE '0' END AS active
FROM dbo.S_FieldMaintenance h
WHERE h.ID IS NOT NULL
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
                if not stripped or (stripped.startswith("(") and stripped.endswith("rows affected)")):
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
    with OUTPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            table = row.get("source_table") or ""
            table_counts[table] = table_counts.get(table, 0) + 1
            if row.get("active") == "1":
                active_rows += 1
    source_counts = {
        table: scalar(f"SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.{table};")
        for table in SOURCE_TABLES
    }
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_workflow_detail_replay_adapter",
        "total_rows": rows,
        "active_rows": active_rows,
        "source_counts": source_counts,
        "table_counts": table_counts,
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_workflow_detail_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_WORKFLOW_DETAIL_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
