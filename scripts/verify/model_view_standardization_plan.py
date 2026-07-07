# -*- coding: utf-8 -*-
"""Build a model/view standardization plan from the fact-layer audit."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT_JSON = ROOT / "artifacts/backend/model_view_fact_layer_audit.json"
REPORT_JSON = ROOT / "artifacts/backend/model_view_standardization_plan.json"
REPORT_MD = ROOT / "docs/ops/audit/model_view_standardization_plan.md"


FRAMEWORKS = {
    "business_document": {
        "title": "业务单据模型",
        "must_have": ["tree", "form", "search", "read_access", "state", "date", "attachment", "chatter"],
        "list_frame": ["状态", "单据号/名称", "项目/公司", "往来单位", "金额", "业务日期", "录入人", "录入时间", "附件"],
        "form_frame": ["头部状态与动作", "基本信息", "业务信息", "金额/明细", "附件", "日志/沟通", "历史溯源"],
        "policy": "可创建/可编辑的承载业务事实模型，统一补齐附件、日志、状态和业务日期信号。",
    },
    "business_detail_line": {
        "title": "业务明细行模型",
        "must_have": ["tree", "form", "search", "read_access"],
        "list_frame": ["父单据", "项目/业务对象", "名称/编码", "数量", "单价", "金额", "备注"],
        "form_frame": ["父单据", "明细信息", "数量金额", "备注"],
        "policy": "明细行不强制独立状态/日志，附件按业务需要从父单据继承或关联。",
    },
    "report_summary": {
        "title": "报表汇总模型",
        "must_have": ["tree", "search", "read_access", "data"],
        "list_frame": ["期间/项目/公司", "分类维度", "指标金额", "累计值", "更新时间"],
        "form_frame": ["只读摘要", "维度信息", "指标明细", "来源说明"],
        "policy": "报表以只读列表和钻取为主，不强制附件/日志/状态。",
    },
    "legacy_fact": {
        "title": "历史事实模型",
        "must_have": ["tree", "form", "search", "read_access", "legacy_trace", "data"],
        "list_frame": ["历史编号", "项目/公司", "业务日期", "金额/数量", "来源模型", "历史录入人", "历史录入时间"],
        "form_frame": ["历史来源", "原始字段", "映射字段", "附件索引/历史文件", "投影去向"],
        "policy": "历史事实模型优先只读、可追溯，不强制 Odoo chatter；附件以历史文件索引或附件引用表达。",
    },
    "configuration": {
        "title": "配置/字典模型",
        "must_have": ["tree", "form", "search", "read_access"],
        "list_frame": ["名称/编码", "分类", "启用状态", "排序", "更新时间"],
        "form_frame": ["配置基本信息", "适用范围", "规则/参数", "变更说明"],
        "policy": "配置模型不按业务数据缺口处理，重点是可维护、可审计、权限边界明确。",
    },
    "master_data": {
        "title": "主数据/组织权限模型",
        "must_have": ["tree", "form", "search", "read_access"],
        "list_frame": ["名称", "编码/账号", "类型", "所属公司/部门", "启用状态", "更新时间"],
        "form_frame": ["基础身份", "组织关系", "联系方式/权限", "历史来源"],
        "policy": "主数据重点是身份一致性、去重、授权和历史来源。",
    },
}


DETAIL_LINE_SUFFIXES = (".line", ".alloc")
DETAIL_LINE_MODELS = {
    "project.boq.line",
    "project.budget.cost.alloc",
    "payment.request.line",
    "sc.receipt.invoice.line",
}
CONFIG_MODELS = {
    "payment.method",
    "project.cost.code",
    "project.dictionary",
    "project.project.stage",
    "project.tags",
    "sc.approval.policy",
    "sc.approval.scope",
    "sc.dictionary",
    "sc.fund.account",
    "sc.project.stage.requirement.item",
}
REPORT_MODEL_MARKERS = (
    ".summary",
    ".ledger",
    ".compare",
    ".metrics.",
    ".cockpit.",
)
REPORT_MODELS = {
    "sc.ar.ap.company.summary",
    "sc.ar.ap.project.summary",
    "sc.company.operation.summary",
    "sc.dashboard.cockpit.fact",
    "sc.operating.metrics.project",
    "sc.treasury.reconciliation",
}
MASTER_MODELS = {"res.partner", "res.users", "hr.department"}


def normalized_lane(row: dict) -> str:
    model = row["model"]
    if model in MASTER_MODELS:
        return "master_data"
    if model in CONFIG_MODELS:
        return "configuration"
    if row["lane"] == "legacy_fact" or model.startswith("sc.legacy."):
        return "legacy_fact"
    if model in REPORT_MODELS or any(marker in model for marker in REPORT_MODEL_MARKERS):
        return "report_summary"
    if model in DETAIL_LINE_MODELS or model.endswith(DETAIL_LINE_SUFFIXES):
        return "business_detail_line"
    return row["lane"] if row["lane"] in FRAMEWORKS else "business_document"


def missing_required(row: dict, lane: str) -> list[str]:
    missing = []
    signals = row.get("foundation_signals") or {}
    access = row.get("access") or {}
    if "tree" in FRAMEWORKS[lane]["must_have"] and row.get("tree_field_count", 0) <= 0:
        missing.append("tree")
    if "form" in FRAMEWORKS[lane]["must_have"] and row.get("form_field_count", 0) <= 0:
        missing.append("form")
    if "search" in FRAMEWORKS[lane]["must_have"] and row.get("search_control_count", 0) <= 0:
        missing.append("search")
    if "read_access" in FRAMEWORKS[lane]["must_have"] and access.get("read") is not True:
        missing.append("read_access")
    if "data" in FRAMEWORKS[lane]["must_have"] and not row.get("record_count"):
        missing.append("data")
    for signal in ("state", "date", "attachment", "chatter", "legacy_trace"):
        if signal in FRAMEWORKS[lane]["must_have"] and not signals.get(signal):
            missing.append(signal)
    return missing


def priority_for(row: dict, lane: str, missing: list[str]) -> str:
    if not missing:
        return "ok"
    model = row["model"]
    records = int(row.get("record_count") or 0)
    if lane == "business_document" and records > 0:
        return "P0"
    if lane == "business_detail_line" and ("tree" in missing or "form" in missing or "read_access" in missing):
        return "P0"
    if lane == "legacy_fact" and ("tree" in missing or "form" in missing or "search" in missing or "legacy_trace" in missing):
        return "P0"
    if model in {"res.partner", "res.users"} and missing:
        return "P0"
    if records == 0 and lane == "business_document":
        return "P1"
    if lane in {"report_summary", "configuration", "master_data"}:
        return "P1"
    return "P1"


def remediation(row: dict, lane: str, missing: list[str]) -> list[str]:
    actions = []
    if any(item in missing for item in ("tree", "form", "search")):
        actions.append("补齐 native tree/form/search XML 或统一契约投影")
    if "attachment" in missing:
        actions.append("补齐 attachment_ids 或附件索引信号")
    if "chatter" in missing:
        actions.append("按模型层级决定继承 mail.thread/activity.mixin 或只读历史日志投影")
    if "state" in missing:
        actions.append("补齐 state/status/validation_status 状态信号或显式声明只读无状态")
    if "date" in missing:
        actions.append("补齐业务日期字段或统一映射 create_date/document_date")
    if "legacy_trace" in missing:
        actions.append("补齐 legacy/source 溯源字段")
    if "data" in missing:
        actions.append("确认是否应回填历史数据；配置模型则标记为可空")
    if "read_access" in missing:
        actions.append("补齐业务配置管理员读取权限")
    return actions


def main() -> int:
    audit = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    rows = []
    for row in audit["rows"]:
        lane = normalized_lane(row)
        missing = missing_required(row, lane)
        priority = priority_for(row, lane, missing)
        rows.append({
            "model": row["model"],
            "model_label": row.get("model_label") or "",
            "domain": row["domain"],
            "original_lane": row["lane"],
            "lane": lane,
            "menu_count": row["menu_count"],
            "record_count": row["record_count"],
            "missing_required": missing,
            "priority": priority,
            "remediation": remediation(row, lane, missing),
            "menus": row.get("menus") or [],
        })

    priority_counts = Counter(row["priority"] for row in rows)
    lane_counts = Counter(row["lane"] for row in rows)
    p0 = [row for row in rows if row["priority"] == "P0"]
    p1 = [row for row in rows if row["priority"] == "P1"]
    payload = {
        "ok": True,
        "source": str(INPUT_JSON.relative_to(ROOT)),
        "summary": {
            "model_count": len(rows),
            "p0_count": len(p0),
            "p1_count": len(p1),
            "ok_count": priority_counts.get("ok", 0),
            "priority_counts": dict(sorted(priority_counts.items())),
            "lane_counts": dict(sorted(lane_counts.items())),
        },
        "frameworks": FRAMEWORKS,
        "rows": rows,
        "p0_queue": sorted(p0, key=lambda row: (row["lane"], row["domain"], row["model"])),
        "p1_queue": sorted(p1, key=lambda row: (row["lane"], row["domain"], row["model"])),
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Model View Standardization Plan",
        "",
        f"- source: `{payload['source']}`",
        f"- model_count: {payload['summary']['model_count']}",
        f"- P0: {payload['summary']['p0_count']}",
        f"- P1: {payload['summary']['p1_count']}",
        f"- OK: {payload['summary']['ok_count']}",
        "",
        "## Frameworks",
        "",
    ]
    for key, framework in FRAMEWORKS.items():
        lines.append(f"### {framework['title']} (`{key}`)")
        lines.append(f"- policy: {framework['policy']}")
        lines.append(f"- list_frame: {', '.join(framework['list_frame'])}")
        lines.append(f"- form_frame: {', '.join(framework['form_frame'])}")
        lines.append("")

    lines.extend([
        "## P0 Queue",
        "",
        "| lane | domain | model | records | missing | first action |",
        "|---|---|---|---:|---|---|",
    ])
    for row in payload["p0_queue"]:
        first_menu = row["menus"][0] if row["menus"] else {}
        lines.append(
            "| {lane} | {domain} | `{model}` | {records} | {missing} | {action} |".format(
                lane=row["lane"],
                domain=row["domain"],
                model=row["model"],
                records=row["record_count"] if row["record_count"] is not None else "-",
                missing=", ".join(row["missing_required"]) or "-",
                action=f"{first_menu.get('menu_name','-')} / {first_menu.get('action_id','-')}",
            )
        )

    lines.extend([
        "",
        "## P1 Queue",
        "",
        "| lane | domain | model | records | missing |",
        "|---|---|---|---:|---|",
    ])
    for row in payload["p1_queue"]:
        lines.append(
            "| {lane} | {domain} | `{model}` | {records} | {missing} |".format(
                lane=row["lane"],
                domain=row["domain"],
                model=row["model"],
                records=row["record_count"] if row["record_count"] is not None else "-",
                missing=", ".join(row["missing_required"]) or "-",
            )
        )

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print("[model_view_standardization_plan] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
