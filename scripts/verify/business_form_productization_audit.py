#!/usr/bin/env python3
"""Audit productization risks for formal business forms.

This report is intentionally local and read-only.  It combines the formal
business operation matrix with the latest runtime form-structure audit to
surface forms that are usable but still feel like dense data screens.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/product/formal_business_operation_capability_matrix_v1.md"
STANDARD_PATH = ROOT / "docs/product/formal_business_form_productization_standard_v1.md"
STRUCTURE_CSV = ROOT / "docs/audit/native/form_structure_standardization_runtime/form_structure_standardization_audit.csv"
OUT_JSON = ROOT / "artifacts/backend/business_form_productization_audit.json"
OUT_MD = ROOT / "artifacts/backend/business_form_productization_audit.md"

HIGH_DENSITY_THRESHOLD = 70
MEDIUM_DENSITY_THRESHOLD = 50


def _strip_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _parse_matrix_rows() -> list[dict]:
    rows = []
    pattern = re.compile(r"list=(?P<list>\d+)\s+form=(?P<form>\d+)\s+search=(?P<search>\d+)")
    for line in MATRIX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or "PASS" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 9 or cells[0] == "---" or cells[0] == "中心":
            continue
        counts = pattern.search(cells[6])
        if not counts:
            continue
        rows.append(
            {
                "center": cells[0],
                "domain": cells[1],
                "entry": cells[2],
                "model": _strip_code(cells[3]),
                "crud": _strip_code(cells[4]),
                "contract": _strip_code(cells[5]),
                "list_field_count": int(counts.group("list")),
                "form_field_count": int(counts.group("form")),
                "search_field_count": int(counts.group("search")),
                "url": _strip_code(cells[7]),
                "status": cells[8],
            }
        )
    return rows


def _runtime_structure_by_model() -> dict[str, dict]:
    if not STRUCTURE_CSV.is_file():
        return {}
    by_model = {}
    with STRUCTURE_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("audit_mode") != "runtime_default":
                continue
            model = row.get("model") or ""
            if not model:
                continue
            by_model[model] = row
    return by_model


def _risk_for_entry(entry: dict, structure: dict | None) -> tuple[str, list[str], list[str]]:
    issues = []
    suggestions = []
    form_count = entry["form_field_count"]
    if form_count >= HIGH_DENSITY_THRESHOLD:
        issues.append("high_density_form")
        suggestions.append("拆成主信息、业务明细、附件与备注、来源追溯等稳定页签")
    elif form_count >= MEDIUM_DENSITY_THRESHOLD:
        issues.append("medium_density_form")
        suggestions.append("检查首屏字段是否只保留办理必需信息")

    if structure:
        notebook_count = int(structure.get("notebook_count") or 0)
        page_count = int(structure.get("page_count") or 0)
        labelled_group_count = int(structure.get("labelled_group_count") or 0)
        labelled_page_count = int(structure.get("labelled_page_count") or 0)
        statusbar_count = int(structure.get("statusbar_count") or 0)
        button_box_count = int(structure.get("button_box_count") or 0)
        source_trace_count = int(structure.get("source_trace_field_count") or 0)
        classification = structure.get("classification") or ""
        if notebook_count == 0 or page_count == 0:
            issues.append("missing_business_tabs")
            suggestions.append("补齐按业务任务组织的页签，不让长表单单屏堆叠")
        if labelled_group_count == 0 or (page_count and labelled_page_count == 0):
            issues.append("weak_section_labels")
            suggestions.append("补 group/page 标题，让字段分组可扫描")
        if source_trace_count > 0:
            issues.append("source_trace_visible_risk")
            suggestions.append("确认来源/迁移字段只在内部审计区展示")
        if statusbar_count == 0 and entry["crud"] == "RCW":
            issues.append("missing_status_context")
            suggestions.append("对办理型单据确认状态栏或等价状态提示")
        if button_box_count == 0 and form_count >= MEDIUM_DENSITY_THRESHOLD:
            issues.append("missing_summary_actions")
            suggestions.append("高密度表单补关联统计或摘要动作入口")
        if classification in {"contract_auto_with_default_tabs", "needs_semantic_annotation", "needs_xml_structure"}:
            issues.append(classification)
    else:
        issues.append("missing_runtime_structure_evidence")
        suggestions.append("刷新 form_structure_standardization_runtime 审计")

    severity = "PASS"
    if "high_density_form" in issues or "needs_xml_structure" in issues:
        severity = "P1"
    elif "medium_density_form" in issues or "missing_business_tabs" in issues or "needs_semantic_annotation" in issues:
        severity = "P2"
    elif issues:
        severity = "P3"
    return severity, sorted(set(issues)), sorted(set(suggestions))


def _markdown_table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |")
    return "\n".join(lines)


def main() -> int:
    matrix_rows = _parse_matrix_rows()
    structures = _runtime_structure_by_model()
    audited = []
    for entry in matrix_rows:
        structure = structures.get(entry["model"])
        severity, issues, suggestions = _risk_for_entry(entry, structure)
        audited.append(
            {
                **entry,
                "severity": severity,
                "issues": issues,
                "suggestions": suggestions,
                "runtime_classification": (structure or {}).get("classification", "MISSING"),
                "runtime_structural_score": int((structure or {}).get("structural_score") or 0),
                "runtime_source_trace_field_count": int((structure or {}).get("source_trace_field_count") or 0),
            }
        )

    by_severity = Counter(row["severity"] for row in audited)
    by_center = defaultdict(Counter)
    for row in audited:
        by_center[row["center"]][row["severity"]] += 1

    risk_rows = [row for row in audited if row["severity"] != "PASS"]
    risk_rows.sort(key=lambda row: ({"P1": 0, "P2": 1}.get(row["severity"], 9), -row["form_field_count"], row["center"], row["entry"]))
    p1_rows = [row for row in risk_rows if row["severity"] == "P1"]

    payload = {
        "scope": "business_form_productization_audit",
        "standard_path": str(STANDARD_PATH.relative_to(ROOT)),
        "matrix_path": str(MATRIX_PATH.relative_to(ROOT)),
        "runtime_structure_csv": str(STRUCTURE_CSV.relative_to(ROOT)),
        "thresholds": {
            "high_density_form": HIGH_DENSITY_THRESHOLD,
            "medium_density_form": MEDIUM_DENSITY_THRESHOLD,
        },
        "summary": {
            "formal_business_entries": len(audited),
            "risk_entry_count": len(risk_rows),
            "p1_entry_count": len(p1_rows),
            "by_severity": dict(sorted(by_severity.items())),
            "by_center": {center: dict(counts) for center, counts in sorted(by_center.items())},
        },
        "p1_queue": p1_rows,
        "risk_rows": risk_rows,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    table_rows = [
        {
            "severity": row["severity"],
            "center": row["center"],
            "entry": row["entry"],
            "model": row["model"],
            "form_fields": row["form_field_count"],
            "issues": ",".join(row["issues"]),
        }
        for row in risk_rows[:40]
    ]
    md = [
        "# Business Form Productization Audit",
        "",
        f"- standard: `{STANDARD_PATH.relative_to(ROOT)}`",
        f"- formal_business_entries: `{len(audited)}`",
        f"- risk_entry_count: `{len(risk_rows)}`",
        f"- p1_entry_count: `{len(p1_rows)}`",
        f"- high_density_threshold: `{HIGH_DENSITY_THRESHOLD}`",
        f"- medium_density_threshold: `{MEDIUM_DENSITY_THRESHOLD}`",
        "",
        "## P1/P2 Queue",
        "",
        _markdown_table(table_rows, ["severity", "center", "entry", "model", "form_fields", "issues"]),
        "",
        "## Interpretation",
        "",
        "- `P1`: high-density or structurally weak forms that should seed the first productization batch.",
        "- `P2`: moderate density or missing product cues that should enter follow-up batches.",
        "- `P3`: low-density forms with trace or secondary cues; keep visible in the backlog but do not block the first batch.",
        "",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(
        "[business_form_productization_audit] PASS "
        f"entries={len(audited)} risks={len(risk_rows)} p1={len(p1_rows)}"
    )
    print(f"BUSINESS_FORM_PRODUCTIZATION_AUDIT={json.dumps(payload['summary'], ensure_ascii=False, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
