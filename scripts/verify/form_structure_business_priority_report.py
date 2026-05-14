#!/usr/bin/env python3
"""Build a business-priority queue from the runtime form structure audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "docs/audit/native/form_structure_standardization_runtime/form_structure_standardization_audit.csv"
DEFAULT_OUTPUT_DIR = ROOT / "docs/audit/native/form_structure_business_priority"

BUSINESS_MODEL_PREFIXES = (
    "construction.",
    "project.",
    "quota.",
    "sc.",
    "tender.",
)
BUSINESS_MODEL_EXACT = {
    "payment.ledger",
    "payment.request",
    "payment.request.line",
}
TECHNICAL_MODEL_PREFIXES = (
    "base.",
    "bus.",
    "digest.",
    "fetchmail.",
    "iap.",
    "ir.",
    "mail.",
    "portal.",
    "res.config.",
    "res.config",
    "res.users.",
    "web.",
)
TECHNICAL_MODEL_TOKENS = (
    ".wizard",
    ".settings",
    ".config",
    ".installer",
)
LOW_PRIORITY_PREFIXES = (
    "sc.legacy.",
)
PLATFORM_PREFIXES = (
    "sc.capability",
    "sc.entitlement",
    "sc.ops.",
    "sc.pack.",
    "sc.scene",
    "sc.subscription",
    "sc.usage.",
    "sc.workbench.",
    "ui.form.",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def is_business_model(model: str) -> bool:
    if not model:
        return False
    if model.startswith(TECHNICAL_MODEL_PREFIXES):
        return False
    if model in BUSINESS_MODEL_EXACT:
        return True
    return model.startswith(BUSINESS_MODEL_PREFIXES)


def is_transient_or_setup(model: str) -> bool:
    return any(token in model for token in TECHNICAL_MODEL_TOKENS) or model.endswith(".wizard")


def surface_lane(model: str) -> str:
    if is_transient_or_setup(model):
        return "setup_or_wizard"
    if model.startswith(LOW_PRIORITY_PREFIXES):
        return "legacy_fact_carrier"
    if model.startswith(PLATFORM_PREFIXES):
        return "platform_configuration"
    return "business_document"


def domain_group(model: str) -> str:
    if model.startswith("project."):
        return "project"
    if model.startswith("construction."):
        return "contract"
    if model in BUSINESS_MODEL_EXACT:
        return "finance"
    if model.startswith("tender."):
        return "tender"
    if model.startswith("sc.material."):
        return "material"
    if model.startswith("sc.subcontract."):
        return "subcontract"
    if model.startswith("sc.labor."):
        return "labor"
    if model.startswith("sc.equipment."):
        return "equipment"
    if model.startswith("sc.safety."):
        return "safety"
    if model.startswith("sc.quality."):
        return "quality"
    if model.startswith("sc.legacy."):
        return "legacy"
    if model.startswith("sc."):
        return "sc_other"
    return "other"


def priority_lane(row: dict[str, str]) -> str:
    model = row.get("model", "")
    lane = surface_lane(model)
    classification = row.get("classification", "")
    if lane == "setup_or_wizard":
        return "P4_setup_or_wizard"
    if lane == "legacy_fact_carrier":
        return "P3_legacy_fact_default_tabs"
    if lane == "platform_configuration":
        return "P3_platform_configuration"
    if classification == "contract_auto_with_default_tabs":
        return "P0_contract_default_tabs"
    if classification == "needs_semantic_annotation":
        return "P1_semantic_annotation"
    if classification == "needs_xml_structure":
        return "P2_xml_structure"
    if classification == "auto_standardizable":
        return "P0_ready_baseline"
    return "P9_review"


def choose_runtime_default(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_model: dict[str, dict[str, str]] = {}
    for row in rows:
        model = row.get("model", "")
        if row.get("audit_mode") != "runtime_default":
            continue
        if not is_business_model(model):
            continue
        by_model.setdefault(model, row)
    return sorted(by_model.values(), key=lambda row: (priority_lane(row), domain_group(row.get("model", "")), row.get("model", "")))


def enrich_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        item = dict(row)
        item["surface_lane"] = surface_lane(item.get("model", ""))
        item["domain_group"] = domain_group(item.get("model", ""))
        item["priority_lane"] = priority_lane(item)
        out.append(item)
    return out


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "priority_lane",
        "domain_group",
        "surface_lane",
        "model",
        "xmlid",
        "view_name",
        "classification",
        "structural_score",
        "field_count",
        "group_count",
        "notebook_count",
        "page_count",
        "button_box_count",
        "statusbar_count",
        "source_trace_field_count",
        "recommendation",
        "gaps",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def md_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict) -> None:
    p0_tabs = [row for row in rows if row["priority_lane"] == "P0_contract_default_tabs"][:40]
    p1_anno = [row for row in rows if row["priority_lane"] == "P1_semantic_annotation"][:40]
    p2_xml = [row for row in rows if row["priority_lane"] == "P2_xml_structure"][:40]
    ready = [row for row in rows if row["priority_lane"] == "P0_ready_baseline"][:30]
    legacy = [row for row in rows if row["priority_lane"] == "P3_legacy_fact_default_tabs"][:30]
    fields = ["domain_group", "model", "classification", "structural_score", "gaps"]
    text = f"""# 业务表单结构统一优先级清单

## 摘要

- 运行态业务模型默认表单：{summary["total_business_default_forms"]}
- P0 可先做契约默认页签：{summary["by_priority"].get("P0_contract_default_tabs", 0)}
- P0 已可作为基线样本：{summary["by_priority"].get("P0_ready_baseline", 0)}
- P1 需补语义标注：{summary["by_priority"].get("P1_semantic_annotation", 0)}
- P2 需补 XML 主结构：{summary["by_priority"].get("P2_xml_structure", 0)}
- P3 legacy 承载低优先级：{summary["by_priority"].get("P3_legacy_fact_default_tabs", 0)}
- P3 平台配置低优先级：{summary["by_priority"].get("P3_platform_configuration", 0)}
- P4 wizard/setup 暂不纳入业务统一：{summary["by_priority"].get("P4_setup_or_wizard", 0)}

## 执行顺序

1. `P0_contract_default_tabs`：不改业务事实视图，先在契约标准化层为这批表单生成项目式默认页签。
2. `P1_semantic_annotation`：补少量 group/page 标题或 `data-sc-anchor`，再进入同一标准化器。
3. `P2_xml_structure`：只对正式业务单据补最小 `sheet/group` 骨架；wizard/setup 不进入主线。
4. `P3`：legacy 承载和平台配置先保持低优先级，除非它们是当前业务验收入口。

## P0 契约默认页签队列

{md_table(p0_tabs, fields)}

## P1 语义标注队列

{md_table(p1_anno, fields)}

## P2 XML 主结构队列

{md_table(p2_xml, fields)}

## P0 已可作为基线样本

{md_table(ready, fields)}

## P3 Legacy 承载队列

{md_table(legacy, fields)}
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build business priority queue from runtime form structure audit.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    rows = enrich_rows(choose_runtime_default(read_rows(Path(args.input))))
    summary = {
        "total_business_default_forms": len(rows),
        "by_priority": dict(Counter(row["priority_lane"] for row in rows)),
        "by_domain": dict(Counter(row["domain_group"] for row in rows)),
        "by_surface_lane": dict(Counter(row["surface_lane"] for row in rows)),
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "form_structure_business_priority.csv", rows)
    (out_dir / "form_structure_business_priority.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown(out_dir / "form_structure_business_priority.md", rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {out_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
