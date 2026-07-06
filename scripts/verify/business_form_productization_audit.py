#!/usr/bin/env python3
"""Audit productization risks for formal business forms.

This report is intentionally local and read-only.  It combines the formal
business operation matrix with the latest runtime form-structure audit to
surface forms that are usable but still feel like dense data screens.
"""

from __future__ import annotations

import csv
import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/product/formal_business_operation_capability_matrix_v1.md"
STANDARD_PATH = ROOT / "docs/product/formal_business_form_productization_standard_v1.md"
STRUCTURE_CSV = ROOT / "docs/audit/native/form_structure_standardization_runtime/form_structure_standardization_audit.csv"
OUT_JSON = ROOT / "artifacts/backend/business_form_productization_audit.json"
OUT_MD = ROOT / "artifacts/backend/business_form_productization_audit.md"
PRODUCT_CONTRACT_GLOBS = (
    "addons/smart_construction_core/data/*form_productization_contract*.xml",
)

HIGH_DENSITY_THRESHOLD = 70
MEDIUM_DENSITY_THRESHOLD = 50
ENTRY_SURFACE_MODES = {"entry_semantic_surface", "semantic_entry_surface"}
STATUS_CONTEXT_FIELD_NAMES = {
    "approval_status",
    "can_review",
    "document_state",
    "document_state_label",
    "document_status",
    "state",
    "status",
    "validation_status",
    "workflow_state",
}


def _strip_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _norm_text(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "").strip())


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


def _productized_contracts_by_entry() -> dict[tuple[str, str], dict]:
    by_entry = {}
    paths = []
    for pattern in PRODUCT_CONTRACT_GLOBS:
        paths.extend(ROOT.glob(pattern))
    for path in sorted(set(paths)):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for record in root.findall(".//record"):
            if record.attrib.get("model") != "ui.business.config.contract":
                continue
            fields = {field.attrib.get("name"): field for field in record.findall("field")}
            model = (fields.get("model").text or "").strip() if fields.get("model") is not None else ""
            contract_field = fields.get("contract_json")
            if not model or contract_field is None:
                continue
            raw_payload = contract_field.attrib.get("eval") or contract_field.text or ""
            try:
                payload = ast.literal_eval(raw_payload)
            except (SyntaxError, ValueError):
                continue
            orchestration = payload.get("view_orchestration") if isinstance(payload, dict) else {}
            if not isinstance(orchestration, dict):
                continue
            context = orchestration.get("context") if isinstance(orchestration.get("context"), dict) else {}
            source = str(context.get("source") or "")
            source_status = str(context.get("source_status") or "")
            if "product_release" not in source and source_status != "product_release":
                continue
            views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
            form = views.get("form") if isinstance(views.get("form"), dict) else {}
            mode = str(form.get("composition_mode") or form.get("compositionMode") or "").strip()
            title = str(form.get("title") or "").strip()
            sections = form.get("sections") if isinstance(form.get("sections"), list) else []
            rows = form.get("fields") if isinstance(form.get("fields"), list) else []
            if not title or mode not in ENTRY_SURFACE_MODES or not sections or not rows or isinstance(form.get("layout"), list):
                continue
            field_names = [
                str(row.get("name") or "").strip()
                for row in rows
                if isinstance(row, dict) and str(row.get("name") or "").strip()
            ]
            action_field = fields.get("action_id")
            by_entry[(model, _norm_text(title))] = {
                "path": str(path.relative_to(ROOT)),
                "record_id": record.attrib.get("id") or "",
                "action_ref": action_field.attrib.get("ref") if action_field is not None else "",
                "title": title,
                "field_count": len(field_names),
                "has_status_context": bool(set(field_names) & STATUS_CONTEXT_FIELD_NAMES),
                "section_count": len(sections),
            }
    return by_entry


def _risk_for_entry(entry: dict, structure: dict | None, productized_contract: dict | None) -> tuple[str, list[str], list[str], list[str]]:
    issues = []
    evidence = []
    suggestions = []
    form_count = entry["form_field_count"]
    is_productized = bool(productized_contract)
    if is_productized:
        evidence.append("productized_entry_semantic_surface")
        if int(productized_contract.get("section_count") or 0) > 0 and int(productized_contract.get("field_count") or 0) > 0:
            evidence.append("productized_contract_structure_evidence")
        if productized_contract.get("has_status_context"):
            evidence.append("productized_status_context")
        suggestions.append("保持 action 级产品化契约与原生模型解析边界分离")
    elif form_count >= HIGH_DENSITY_THRESHOLD:
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
        if not is_productized and (notebook_count == 0 or page_count == 0):
            issues.append("missing_business_tabs")
            suggestions.append("补齐按业务任务组织的页签，不让长表单单屏堆叠")
        if not is_productized and (labelled_group_count == 0 or (page_count and labelled_page_count == 0)):
            issues.append("weak_section_labels")
            suggestions.append("补 group/page 标题，让字段分组可扫描")
        if source_trace_count > 0 and is_productized:
            evidence.append("source_trace_sectioned")
            suggestions.append("来源追溯字段已由产品化契约放入独立追溯区")
        elif source_trace_count > 0:
            issues.append("source_trace_visible_risk")
            suggestions.append("确认来源/迁移字段只在内部审计区展示")
        if statusbar_count == 0 and entry["crud"] == "RCW" and not productized_contract.get("has_status_context"):
            issues.append("missing_status_context")
            suggestions.append("对办理型单据确认状态栏或等价状态提示")
        if not is_productized and button_box_count == 0 and form_count >= MEDIUM_DENSITY_THRESHOLD:
            issues.append("missing_summary_actions")
            suggestions.append("高密度表单补关联统计或摘要动作入口")
        if not is_productized and classification in {"contract_auto_with_default_tabs", "needs_semantic_annotation", "needs_xml_structure"}:
            issues.append(classification)
    else:
        if is_productized and int(productized_contract.get("section_count") or 0) > 0 and int(productized_contract.get("field_count") or 0) > 0:
            evidence.append("productized_contract_structure_evidence")
            suggestions.append("补跑 form_structure_standardization_runtime 可提升原生结构覆盖，但不阻塞已发布产品化入口")
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
    return severity, sorted(set(issues)), sorted(set(suggestions)), sorted(set(evidence))


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
    productized_contracts = _productized_contracts_by_entry()
    audited = []
    for entry in matrix_rows:
        structure = structures.get(entry["model"])
        productized_contract = productized_contracts.get((entry["model"], _norm_text(entry["entry"])))
        severity, issues, suggestions, evidence = _risk_for_entry(entry, structure, productized_contract)
        audited.append(
            {
                **entry,
                "severity": severity,
                "issues": issues,
                "evidence": evidence,
                "suggestions": suggestions,
                "productized_contract": productized_contract or {},
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
            "productized_entry_count": sum(1 for row in audited if row.get("productized_contract")),
            "productized_pass_count": sum(
                1 for row in audited if row.get("productized_contract") and row.get("severity") == "PASS"
            ),
            "source_trace_sectioned_count": sum(
                1 for row in audited if "source_trace_sectioned" in (row.get("evidence") or [])
            ),
            "productized_status_context_count": sum(
                1 for row in audited if "productized_status_context" in (row.get("evidence") or [])
            ),
            "productized_contract_structure_evidence_count": sum(
                1 for row in audited if "productized_contract_structure_evidence" in (row.get("evidence") or [])
            ),
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
            "productized": "Y" if row.get("productized_contract") else "",
            "issues": ",".join(row["issues"]),
            "evidence": ",".join(row.get("evidence") or []),
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
        f"- productized_entry_count: `{sum(1 for row in audited if row.get('productized_contract'))}`",
        f"- productized_pass_count: `{sum(1 for row in audited if row.get('productized_contract') and row.get('severity') == 'PASS')}`",
        f"- source_trace_sectioned_count: `{sum(1 for row in audited if 'source_trace_sectioned' in (row.get('evidence') or []))}`",
        f"- productized_status_context_count: `{sum(1 for row in audited if 'productized_status_context' in (row.get('evidence') or []))}`",
        f"- productized_contract_structure_evidence_count: `{sum(1 for row in audited if 'productized_contract_structure_evidence' in (row.get('evidence') or []))}`",
        f"- high_density_threshold: `{HIGH_DENSITY_THRESHOLD}`",
        f"- medium_density_threshold: `{MEDIUM_DENSITY_THRESHOLD}`",
        "",
        "## P1/P2 Queue",
        "",
        _markdown_table(table_rows, ["severity", "center", "entry", "model", "form_fields", "productized", "issues", "evidence"]),
        "",
        "## Interpretation",
        "",
        "- `P1`: high-density or structurally weak forms that should seed the first productization batch.",
        "- `P2`: moderate density or missing product cues that should enter follow-up batches.",
        "- `P3`: productized entries with missing status/runtime evidence, or low-density unproductized forms with trace or secondary cues; keep visible in the backlog but do not block the first batch.",
        "- `productized_entry_semantic_surface`: acceptance evidence, not a risk. The entry has an action-scoped product-release contract using `fields + sections + composition_mode=entry_semantic_surface`; native parser output remains the structural source and the backend orchestrator owns layout generation.",
        "- `productized_status_context`: acceptance evidence, not a risk. The productized entry exposes state/status/validation context even when the native XML does not use a statusbar widget.",
        "- `productized_contract_structure_evidence`: acceptance evidence, not a risk. The productized contract declares sections and fields for a published entry; missing stale runtime CSV coverage should be refreshed separately.",
        "- `source_trace_sectioned`: acceptance evidence, not a risk. Source-trace fields exist in the native model and have been placed into a dedicated productized source-trace section.",
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
