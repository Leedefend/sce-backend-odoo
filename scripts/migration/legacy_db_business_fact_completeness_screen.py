#!/usr/bin/env python3
"""Classify legacy SQL Server business fact completeness."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNTIME_JSON = Path(".runtime_artifacts/migration_assets/legacy_db_business_fact_completeness_screen_v1.json")
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_db_business_fact_completeness_screen_v1.md")


class LegacyDbCompletenessError(Exception):
    pass


@dataclass(frozen=True)
class LaneDefinition:
    lane: str
    source_table: str
    target_asset_status: str
    priority: int
    classification: str
    strategy: str
    reason: str


LANE_DEFINITIONS = {
    "BASE_SYSTEM_PROJECT": LaneDefinition(
        "project",
        "BASE_SYSTEM_PROJECT",
        "assetized",
        90,
        "core_master_already_assetized",
        "keep_baseline",
        "项目是业务主体锚点，已完成资产化；后续只补充辅助字段，不阻塞事实迁移。",
    ),
    "BASE_SYSTEM_USER": LaneDefinition(
        "user",
        "BASE_SYSTEM_USER",
        "assetized",
        80,
        "authority_anchor_already_assetized",
        "keep_baseline",
        "用户可作为项目成员和审批记录锚点，但旧库 active 标记较少，后续以已资产用户为准。",
    ),
    "BASE_SYSTEM_PROJECT_USER": LaneDefinition(
        "project_member",
        "BASE_SYSTEM_PROJECT_USER",
        "assetized",
        85,
        "relation_already_assetized_with_user_gap",
        "keep_staging_relation",
        "项目成员关系本身完整，但部分用户不是 active 用户资产，保持中性 staging 承载。",
    ),
    "T_ProjectContract_Out": LaneDefinition(
        "revenue_contract",
        "T_ProjectContract_Out",
        "assetized",
        75,
        "business_header_already_assetized_with_residual_blockers",
        "keep_current_scope",
        "收入合同头和金额线已资产化到当前可锚定范围；剩余阻断不应弱化项目主体规则。",
    ),
    "C_JFHKLR_receipt": LaneDefinition(
        "receipt",
        "C_JFHKLR",
        "assetized",
        70,
        "business_request_already_assetized",
        "closed_invalid_residuals",
        "收款核心事实已资产化，剩余阻断已按 Owner 口径认定为无效或不可完整承载。",
    ),
    "C_ZFSQGL_outflow_request": LaneDefinition(
        "outflow_request",
        "C_ZFSQGL",
        "assetized",
        78,
        "business_request_already_assetized",
        "keep_current_scope",
        "支出申请核心事实已资产化；实际付款、明细和审批流应分层后置。",
    ),
    "T_FK_Supplier_actual_outflow": LaneDefinition(
        "actual_outflow",
        "T_FK_Supplier",
        "not_assetized",
        100,
        "high_completeness_next_core_fact",
        "screen_then_assetize",
        "实际付款具备项目、对方、金额、日期，且多数可关联支出申请，是下一个最有价值事实层。",
    ),
    "T_GYSHT_INFO_supplier_contract": LaneDefinition(
        "supplier_contract",
        "T_GYSHT_INFO",
        "not_assetized",
        95,
        "high_completeness_contract_fact",
        "screen_mapping_model_then_assetize",
        "供应商合同量大且项目/供应商/金额完整度高，应在实际付款前后尽快建立合同锚点。",
    ),
    "C_ZFSQGL_CB_outflow_lines": LaneDefinition(
        "outflow_request_line",
        "C_ZFSQGL_CB",
        "not_assetized",
        88,
        "detail_fact_with_parent_anchor",
        "assetize_after_parent_request",
        "支出申请明细大部分有父单和金额，适合作为 outflow request 的 detail/辅助事实层。",
    ),
    "C_JFHKLR_CB_receipt_invoice_lines": LaneDefinition(
        "receipt_invoice",
        "C_JFHKLR_CB",
        "not_assetized",
        92,
        "high_completeness_auxiliary_fact",
        "assetize_as_auxiliary_fact",
        "收款发票明细几乎完整，但属于票据辅助事实，不应早于核心付款/供应商合同。",
    ),
    "BASE_SYSTEM_FILE_attachment": LaneDefinition(
        "attachment",
        "BASE_SYSTEM_FILE",
        "not_assetized",
        40,
        "evidence_auxiliary_large_volume",
        "defer_until_parent_assets_stable",
        "附件有较完整 BILLID/path，但体量大且依赖父业务单据稳定，后置。",
    ),
    "S_Execute_Approval_workflow": LaneDefinition(
        "workflow",
        "S_Execute_Approval",
        "not_assetized",
        30,
        "runtime_process_fact_high_volume",
        "defer_or_summarize",
        "审批流事实完整但属于运行过程轨迹；先迁核心事实，再按摘要/审计策略处理。",
    ),
}


SQL = r"""
SET NOCOUNT ON;
SELECT 'BASE_SYSTEM_PROJECT' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND NULLIF(LTRIM(RTRIM(ID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(XMMC)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(PROJECT_CODE)),'') IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(COMPANYID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN STATE IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.BASE_SYSTEM_PROJECT;
SELECT 'BASE_SYSTEM_USER' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND NULLIF(LTRIM(RTRIM(ID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(USERNAME)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(PERSON_NAME)),'') IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(PHONE_NUMBER)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN PERSON_STATE IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.BASE_SYSTEM_USER;
SELECT 'BASE_SYSTEM_PROJECT_USER' lane, COUNT(*) raw_rows, COUNT(*) active_rows, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(pu.ID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(pu.USERID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(pu.XMID)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN p.ID IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN u.ID IS NOT NULL THEN 1 ELSE 0 END) aux2, 0 aux3 FROM dbo.BASE_SYSTEM_PROJECT_USER pu LEFT JOIN dbo.BASE_SYSTEM_PROJECT p ON p.ID=pu.XMID AND ISNULL(p.DEL,0)=0 LEFT JOIN dbo.BASE_SYSTEM_USER u ON u.ID=pu.USERID AND ISNULL(u.DEL,0)=0;
SELECT 'T_ProjectContract_Out' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(c.DEL,0)=0 AND c.SCRID IS NULL AND c.SCRQ IS NULL THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(c.DEL,0)=0 AND c.SCRID IS NULL AND c.SCRQ IS NULL AND NULLIF(LTRIM(RTRIM(c.Id)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(c.XMID)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN p.ID IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN COALESCE(c.f_HTJK, c.GCYSZJ, c.D_SCBSJS_QYHTJ, c.D_SCBSJS_JSJE, c.YFK, c.ZLBZJ) > 0 THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(c.CBF)),'') IS NOT NULL OR NULLIF(LTRIM(RTRIM(c.FBF)),'') IS NOT NULL OR NULLIF(LTRIM(RTRIM(c.f_JSDW)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.T_ProjectContract_Out c LEFT JOIN dbo.BASE_SYSTEM_PROJECT p ON p.ID=c.XMID AND ISNULL(p.DEL,0)=0;
SELECT 'C_JFHKLR_receipt' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND f_JE>0 AND NULLIF(LTRIM(RTRIM(Id)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(WLDWID)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN f_JE>0 THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(WLDWID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(XMID)),'') IS NOT NULL OR NULLIF(LTRIM(RTRIM(LYXMID)),'') IS NOT NULL OR NULLIF(LTRIM(RTRIM(TSXMID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.C_JFHKLR;
SELECT 'C_ZFSQGL_outflow_request' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND SCRID IS NULL AND SCRQ IS NULL THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND SCRID IS NULL AND SCRQ IS NULL AND COALESCE(f_JHJE,f_JHFKJE,f_NEW_JHJE,f_SFJE,ZSJE,YJJE)>0 AND NULLIF(LTRIM(RTRIM(f_XMID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(f_GYSID)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN COALESCE(f_JHJE,f_JHFKJE,f_NEW_JHJE,f_SFJE,ZSJE,YJJE)>0 THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(f_XMID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(f_GYSID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.C_ZFSQGL;
SELECT 'T_FK_Supplier_actual_outflow' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND f_FKJE>0 AND NULLIF(LTRIM(RTRIM(Id)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(f_XMID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(f_SupplierID)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN f_FKJE>0 THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(f_ZFSQGLId)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(f_HTID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.T_FK_Supplier;
SELECT 'T_GYSHT_INFO_supplier_contract' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(g.DEL,0)=0 AND g.SCRID IS NULL AND g.SCRQ IS NULL THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(g.DEL,0)=0 AND g.SCRID IS NULL AND g.SCRQ IS NULL AND NULLIF(LTRIM(RTRIM(g.Id)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(g.XMID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(g.f_GYSID)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN p.ID IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN COALESCE(g.ZJE,g.ZJE_NO,g.ZSE,g.SE,g.GLYHTJE)>0 THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(g.f_GYSID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.T_GYSHT_INFO g LEFT JOIN dbo.BASE_SYSTEM_PROJECT p ON p.ID=g.XMID AND ISNULL(p.DEL,0)=0;
SELECT 'C_ZFSQGL_CB_outflow_lines' lane, COUNT(*) raw_rows, COUNT(*) active_rows, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.ZFSQID)),'') IS NOT NULL AND COALESCE(l.ZJE,l.CCZFJE,l.D_BYK_YFJE,l.BCZFHLJJE)>0 THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN z.Id IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN COALESCE(l.ZJE,l.CCZFJE,l.D_BYK_YFJE,l.BCZFHLJJE)>0 THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.SupplierId)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.C_ZFSQGL_CB l LEFT JOIN dbo.C_ZFSQGL z ON z.Id=l.ZFSQID;
SELECT 'C_JFHKLR_CB_receipt_invoice_lines' lane, COUNT(*) raw_rows, COUNT(*) active_rows, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.ZBID)),'') IS NOT NULL AND COALESCE(l.KPJE,l.CCSKJE,l.YKPJE)>0 THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN r.Id IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN COALESCE(l.KPJE,l.CCSKJE,l.YKPJE)>0 THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(l.FPHM)),'') IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.C_JFHKLR_CB l LEFT JOIN dbo.C_JFHKLR r ON r.Id=l.ZBID;
SELECT 'BASE_SYSTEM_FILE_attachment' lane, COUNT(*) raw_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 THEN 1 ELSE 0 END) active_rows, SUM(CASE WHEN ISNULL(DEL,0)=0 AND NULLIF(LTRIM(RTRIM(BILLID)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(ATTR_PATH)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(BILLID)),'') IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(ATTR_PATH)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN FILESIZE>0 THEN 1 ELSE 0 END) aux3 FROM dbo.BASE_SYSTEM_FILE;
SELECT 'S_Execute_Approval_workflow' lane, COUNT(*) raw_rows, COUNT(*) active_rows, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(Id)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(business_Id)),'') IS NOT NULL AND NULLIF(LTRIM(RTRIM(f_LRRId)),'') IS NOT NULL THEN 1 ELSE 0 END) core_complete, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(business_Id)),'') IS NOT NULL THEN 1 ELSE 0 END) aux1, SUM(CASE WHEN NULLIF(LTRIM(RTRIM(f_LRRId)),'') IS NOT NULL THEN 1 ELSE 0 END) aux2, SUM(CASE WHEN f_SPSJ IS NOT NULL THEN 1 ELSE 0 END) aux3 FROM dbo.S_Execute_Approval;
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LegacyDbCompletenessError(message)


def run_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -W -s '|'",
    ]
    completed = subprocess.run(cmd, input=SQL, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def parse_sqlcmd_tables(output: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 7:
            continue
        if parts[0] in {"lane", "----", ""}:
            continue
        try:
            rows.append(
                {
                    "source_key": parts[0],
                    "raw_rows": int(parts[1]),
                    "active_rows": int(parts[2]),
                    "core_complete": int(parts[3]),
                    "aux1": int(parts[4]),
                    "aux2": int(parts[5]),
                    "aux3": int(parts[6]),
                }
            )
        except ValueError:
            continue
    require(rows, "no sql rows parsed")
    return rows


def pct(value: int, total: int) -> float:
    return round(value * 100 / total, 2) if total else 0.0


def classify(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lanes: list[dict[str, Any]] = []
    for row in rows:
        definition = LANE_DEFINITIONS.get(row["source_key"])
        require(definition is not None, f"missing lane definition: {row['source_key']}")
        active_rows = int(row["active_rows"])
        core_complete = int(row["core_complete"])
        lane = {
            **row,
            "lane": definition.lane,
            "source_table": definition.source_table,
            "target_asset_status": definition.target_asset_status,
            "priority": definition.priority,
            "classification": definition.classification,
            "strategy": definition.strategy,
            "reason": definition.reason,
            "core_complete_rate_active": pct(core_complete, active_rows),
            "core_complete_rate_raw": pct(core_complete, int(row["raw_rows"])),
        }
        lanes.append(lane)
    next_order = [
        lane
        for lane in sorted(lanes, key=lambda item: (-int(item["priority"]), -int(item["core_complete"])))
        if lane["target_asset_status"] == "not_assetized"
    ]
    return {
        "status": "PASS",
        "source": "legacy-sqlserver:LegacyDb",
        "db_writes": 0,
        "odoo_shell": False,
        "lanes": lanes,
        "recommended_next_order": [
            {
                "rank": index + 1,
                "lane": lane["lane"],
                "source_table": lane["source_table"],
                "core_complete": lane["core_complete"],
                "active_rows": lane["active_rows"],
                "core_complete_rate_active": lane["core_complete_rate_active"],
                "strategy": lane["strategy"],
                "reason": lane["reason"],
            }
            for index, lane in enumerate(next_order)
        ],
        "decision": "prioritize_supplier_contract_and_actual_outflow_before_auxiliary_invoice_attachment_workflow",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_markdown(payload: dict[str, Any]) -> str:
    lane_rows = "\n".join(
        "| {lane} | {source_table} | {target_asset_status} | {raw_rows} | {active_rows} | {core_complete} | {core_complete_rate_active}% | {classification} |".format(
            **lane
        )
        for lane in payload["lanes"]
    )
    order_rows = "\n".join(
        "| {rank} | {lane} | {source_table} | {core_complete} | {core_complete_rate_active}% | {strategy} |".format(
            **row
        )
        for row in payload["recommended_next_order"]
    )
    reason_rows = "\n".join(
        f"- `{row['rank']}. {row['lane']}`: {row['reason']}" for row in payload["recommended_next_order"]
    )
    return f"""# Legacy DB Business Fact Completeness Screen v1

Status: `{payload["status"]}`

Source: `{payload["source"]}`

This screen connects directly to the legacy SQL Server database and runs
read-only aggregate queries. It classifies source business fact lanes by core
fact completeness before choosing the next migration assetization order.

## Lane Completeness

| Lane | Source table | Asset status | Raw | Active | Core complete | Core complete / active | Classification |
|---|---|---|---:|---:|---:|---:|---|
{lane_rows}

## Recommended Next Order

| priority | lane | source table | complete facts | complete / active | strategy |
|---:|---|---|---:|---:|---|
{order_rows}

## Reasoning

{reason_rows}

## Decision

`{payload["decision"]}`

## Boundary

- DB writes: `0`
- Odoo shell: `false`
- No asset generation in this screen
- Workflow, attachment, settlement, ledger, and accounting semantics stay out
  of the next core fact batch unless opened by a dedicated task.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy DB business fact completeness.")
    parser.add_argument("--out", default=str(RUNTIME_JSON))
    parser.add_argument("--doc", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rows = parse_sqlcmd_tables(run_sql())
        payload = classify(rows)
        write_json(Path(args.out), payload)
        doc_path = Path(args.doc)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(render_markdown(payload), encoding="utf-8")
    except (LegacyDbCompletenessError, subprocess.SubprocessError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_DB_BUSINESS_FACT_COMPLETENESS_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "LEGACY_DB_BUSINESS_FACT_COMPLETENESS_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "lanes": len(payload["lanes"]),
                "next_lane": payload["recommended_next_order"][0]["lane"],
                "next_core_complete": payload["recommended_next_order"][0]["core_complete"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
