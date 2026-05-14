#!/usr/bin/env python3
"""Audit Odoo form view structure for contract-level standardization.

The report is intentionally static and read-only.  It scans declared XML views
and classifies how much of each form can be normalized by the contract layer,
using the project form as the target structural profile.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

_SCRIPT_PATH = Path(__file__).resolve()
ROOT = Path(os.environ.get("SC_REPO_ROOT") or (_SCRIPT_PATH.parents[2] if len(_SCRIPT_PATH.parents) > 2 else Path.cwd())).resolve()
DEFAULT_OUTPUT_DIR = ROOT / "docs/audit/native/form_structure_standardization"
DEFAULT_RUNTIME_OUTPUT_DIR = ROOT / "docs/audit/native/form_structure_standardization_runtime"
VIEW_GLOBS = (
    "addons/*/views/**/*.xml",
    "addons/*/actions/**/*.xml",
    "addons/*/wizard/**/*views.xml",
)
STANDARD_PROFILE = {
    "sheet",
    "group",
    "notebook",
    "page",
    "statusbar",
    "button_box",
}
TRACE_FIELD_PATTERNS = (
    "legacy",
    "source",
    "origin",
    "external",
    "import",
    "migration",
    "trace",
    "old_",
)


@dataclass
class FormViewAuditRow:
    audit_mode: str
    module: str
    file: str
    xmlid: str
    view_name: str
    model: str
    inherit_id: str
    arch_root: str
    arch_kind: str
    field_count: int
    group_count: int
    labelled_group_count: int
    notebook_count: int
    page_count: int
    labelled_page_count: int
    statusbar_count: int
    header_button_count: int
    button_box_count: int
    stat_button_count: int
    chatter_count: int
    x2many_inline_count: int
    data_anchor_count: int
    source_trace_field_count: int
    structural_score: int
    classification: str
    recommendation: str
    gaps: str


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def module_name(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    if len(parts) >= 2 and parts[0] == "addons":
        return parts[1]
    return ""


def iter_xml_files(paths: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for raw in paths:
        path = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
        if path.is_file():
            files.add(path)
            continue
        for pattern in VIEW_GLOBS:
            files.update(ROOT.glob(pattern))
    return sorted(item for item in files if item.is_file())


def text_of(node, xpath: str) -> str:
    rows = find_nodes(node, xpath)
    if not rows:
        return ""
    value = rows[0]
    return str(value.text or "").strip()


def attr_of(node, xpath: str, attr: str) -> str:
    rows = find_nodes(node, xpath)
    if not rows:
        return ""
    return str(rows[0].get(attr) or "").strip()


def parse_arch_fragment(raw: str):
    if not raw.strip():
        return None, "missing"
    try:
        return ET.fromstring(raw), ""
    except Exception as exc:
        try:
            return ET.fromstring(f"<root>{raw}</root>"), ""
        except Exception:
            return None, str(exc)


def strip_ns(tag: str) -> str:
    return str(tag or "").rsplit("}", 1)[-1]


def iter_desc(root):
    if root is None:
        return
    for item in root.iter():
        yield item


def find_nodes(node, xpath: str):
    if xpath == "./field[@name='model']":
        return [item for item in list(node) if strip_ns(item.tag) == "field" and item.get("name") == "model"]
    if xpath == "./field[@name='name']":
        return [item for item in list(node) if strip_ns(item.tag) == "field" and item.get("name") == "name"]
    if xpath == "./field[@name='inherit_id']":
        return [item for item in list(node) if strip_ns(item.tag) == "field" and item.get("name") == "inherit_id"]
    if xpath == "./field[@name='arch']":
        return [item for item in list(node) if strip_ns(item.tag) == "field" and item.get("name") == "arch"]
    return []


def node_attr_contains(node, attr: str, needle: str) -> bool:
    return needle in str(node.get(attr) or "").split()


def descendant_count(root, xpath: str) -> int:
    if root is None:
        return 0
    if xpath == ".//sheet":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "sheet")
    if xpath == ".//group":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "group")
    if xpath == ".//group[@string]":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "group" and node.get("string"))
    if xpath == ".//notebook":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "notebook")
    if xpath == ".//page":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "page")
    if xpath == ".//page[@string]":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "page" and node.get("string"))
    if xpath == ".//field[contains(@widget, 'statusbar')]":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "field" and "statusbar" in str(node.get("widget") or ""))
    if xpath == ".//header//button":
        return sum(
            1
            for header in iter_desc(root)
            if strip_ns(header.tag) == "header"
            for node in header.iter()
            if strip_ns(node.tag) == "button"
        )
    if xpath == ".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_button_box ')]":
        return sum(1 for node in iter_desc(root) if node_attr_contains(node, "class", "oe_button_box"))
    if xpath == ".//button[contains(concat(' ', normalize-space(@class), ' '), ' oe_stat_button ')]":
        return sum(1 for node in iter_desc(root) if strip_ns(node.tag) == "button" and node_attr_contains(node, "class", "oe_stat_button"))
    if xpath == ".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_chatter ')]":
        return sum(1 for node in iter_desc(root) if node_attr_contains(node, "class", "oe_chatter"))
    if xpath == ".//field[tree or form or list]":
        return sum(
            1
            for node in iter_desc(root)
            if strip_ns(node.tag) == "field"
            and any(strip_ns(child.tag) in {"tree", "form", "list"} for child in list(node))
        )
    if xpath == ".//*[@data-sc-anchor or @data-tab or @name]":
        return sum(1 for node in iter_desc(root) if node.get("data-sc-anchor") or node.get("data-tab") or node.get("name"))
    return 0


def field_names(root) -> list[str]:
    out = []
    seen = set()
    for field in iter_desc(root):
        if strip_ns(field.tag) != "field" or not field.get("name"):
            continue
        name = str(field.get("name") or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def classify_arch(root) -> str:
    if root is None:
        return "parse_error"
    tag = strip_ns(root.tag)
    if tag == "form":
        return "full_form"
    if tag == "xpath" or any(strip_ns(node.tag) == "xpath" for node in iter_desc(root)):
        return "inherited_fragment"
    if any(strip_ns(node.tag) == "form" for node in iter_desc(root)):
        return "nested_form"
    return "non_form_arch"


def standard_score(metrics: dict[str, int], arch_kind: str) -> tuple[int, list[str]]:
    score = 0
    gaps: list[str] = []
    if arch_kind == "full_form":
        score += 2
    else:
        gaps.append("not_full_form")
    checks = (
        ("sheet", metrics["sheet_count"] > 0, 2),
        ("group", metrics["group_count"] > 0, 2),
        ("labelled_group", metrics["labelled_group_count"] > 0, 1),
        ("notebook", metrics["notebook_count"] > 0, 2),
        ("page", metrics["page_count"] > 0, 2),
        ("labelled_page", metrics["labelled_page_count"] > 0, 1),
        ("statusbar", metrics["statusbar_count"] > 0, 1),
        ("button_box", metrics["button_box_count"] > 0, 1),
        ("chatter", metrics["chatter_count"] > 0, 1),
        ("semantic_anchor", metrics["data_anchor_count"] > 0, 1),
    )
    for key, ok, weight in checks:
        if ok:
            score += weight
        else:
            gaps.append(f"missing_{key}")
    return score, gaps


def classify_recommendation(score: int, gaps: list[str], arch_kind: str, metrics: dict[str, int]) -> tuple[str, str]:
    if arch_kind == "parse_error":
        return "manual_review", "XML 解析失败，先修复视图声明"
    if arch_kind == "inherited_fragment":
        return "inherit_fragment", "继承片段需运行态合并后再判定；静态层只做补丁风险识别"
    if arch_kind not in {"full_form", "nested_form"}:
        return "not_target", "不是表单主结构，不纳入本轮统一"
    if "missing_sheet" in gaps or "missing_group" in gaps:
        return "needs_xml_structure", "缺少 sheet/group，契约层难以稳定推断主信息区"
    if metrics["notebook_count"] == 0 or metrics["page_count"] == 0:
        return "contract_auto_with_default_tabs", "可由契约层生成标准 notebook，但需确认页签语义"
    if metrics["labelled_group_count"] == 0 or metrics["labelled_page_count"] == 0 or metrics["data_anchor_count"] == 0:
        return "needs_semantic_annotation", "结构基本可用，建议补 group/page 标题或 data-sc-anchor"
    if score >= 12:
        return "auto_standardizable", "可直接作为项目式结构标准化输入"
    return "needs_semantic_annotation", "结构接近标准，少量语义标注后可统一"


def audit_arch(
    *,
    audit_mode: str,
    module: str = "",
    file: str = "",
    xmlid: str = "",
    view_name: str = "",
    model_name: str = "",
    inherit_id: str = "",
    arch_xml: str = "",
) -> FormViewAuditRow | None:
    arch_root, parse_error = parse_arch_fragment(arch_xml)
    arch_kind = classify_arch(arch_root)
    if arch_kind in {"non_form_arch"} and not model_name:
        return None

    fields = field_names(arch_root) if arch_root is not None else []
    metrics = {
        "sheet_count": descendant_count(arch_root, ".//sheet") if arch_root is not None else 0,
        "group_count": descendant_count(arch_root, ".//group") if arch_root is not None else 0,
        "labelled_group_count": descendant_count(arch_root, ".//group[@string]") if arch_root is not None else 0,
        "notebook_count": descendant_count(arch_root, ".//notebook") if arch_root is not None else 0,
        "page_count": descendant_count(arch_root, ".//page") if arch_root is not None else 0,
        "labelled_page_count": descendant_count(arch_root, ".//page[@string]") if arch_root is not None else 0,
        "statusbar_count": descendant_count(arch_root, ".//field[contains(@widget, 'statusbar')]") if arch_root is not None else 0,
        "header_button_count": descendant_count(arch_root, ".//header//button") if arch_root is not None else 0,
        "button_box_count": descendant_count(arch_root, ".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_button_box ')]") if arch_root is not None else 0,
        "stat_button_count": descendant_count(arch_root, ".//button[contains(concat(' ', normalize-space(@class), ' '), ' oe_stat_button ')]") if arch_root is not None else 0,
        "chatter_count": descendant_count(arch_root, ".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_chatter ')]") if arch_root is not None else 0,
        "x2many_inline_count": descendant_count(arch_root, ".//field[tree or form or list]") if arch_root is not None else 0,
        "data_anchor_count": descendant_count(arch_root, ".//*[@data-sc-anchor or @data-tab or @name]") if arch_root is not None else 0,
        "source_trace_field_count": len([
            name for name in fields
            if any(pattern in name.lower() for pattern in TRACE_FIELD_PATTERNS)
        ]),
    }
    score, gaps = standard_score(metrics, arch_kind)
    classification, recommendation = classify_recommendation(score, gaps, arch_kind, metrics)
    if parse_error:
        gaps.append(f"parse_error:{parse_error}")

    return FormViewAuditRow(
        audit_mode=audit_mode,
        module=module,
        file=file,
        xmlid=xmlid,
        view_name=view_name,
        model=model_name,
        inherit_id=inherit_id,
        arch_root=strip_ns(getattr(arch_root, "tag", "") or ""),
        arch_kind=arch_kind,
        field_count=len(fields),
        group_count=metrics["group_count"],
        labelled_group_count=metrics["labelled_group_count"],
        notebook_count=metrics["notebook_count"],
        page_count=metrics["page_count"],
        labelled_page_count=metrics["labelled_page_count"],
        statusbar_count=metrics["statusbar_count"],
        header_button_count=metrics["header_button_count"],
        button_box_count=metrics["button_box_count"],
        stat_button_count=metrics["stat_button_count"],
        chatter_count=metrics["chatter_count"],
        x2many_inline_count=metrics["x2many_inline_count"],
        data_anchor_count=metrics["data_anchor_count"],
        source_trace_field_count=metrics["source_trace_field_count"],
        structural_score=score,
        classification=classification,
        recommendation=recommendation,
        gaps=";".join(gaps),
    )


def audit_view_record(xml_file: Path, record) -> FormViewAuditRow | None:
    model_name = text_of(record, "./field[@name='model']")
    arch_field = find_nodes(record, "./field[@name='arch']")
    if not arch_field:
        return None
    arch_xml = "".join(ET.tostring(child, encoding="unicode") for child in list(arch_field[0]))
    if not arch_xml.strip() and (arch_field[0].text or "").strip():
        arch_xml = str(arch_field[0].text or "")
    return audit_arch(
        audit_mode="static_xml",
        module=module_name(xml_file),
        file=repo_rel(xml_file),
        xmlid=str(record.get("id") or "").strip(),
        view_name=text_of(record, "./field[@name='name']"),
        model_name=model_name,
        inherit_id=attr_of(record, "./field[@name='inherit_id']", "ref"),
        arch_xml=arch_xml,
    )


def audit_files(files: list[Path]) -> list[FormViewAuditRow]:
    rows: list[FormViewAuditRow] = []
    for xml_file in files:
        try:
            root = ET.parse(str(xml_file)).getroot()
        except Exception:
            continue
        for record in root.iter():
            if strip_ns(record.tag) != "record" or record.get("model") != "ir.ui.view":
                continue
            row = audit_view_record(xml_file, record)
            if row and row.arch_kind != "non_form_arch":
                rows.append(row)
    return rows


def external_xmlid(env, record) -> str:
    try:
        mapping = record.get_external_id()
        return str(mapping.get(record.id) or "").strip()
    except Exception:
        return ""


def runtime_form_view_candidates(env, limit: int = 0):
    View = env["ir.ui.view"].sudo()
    domain = [("type", "=", "form"), ("model", "!=", False)]
    views = View.search(domain, order="model,id", limit=limit or 0)
    by_model: dict[str, list] = defaultdict(list)
    for view in views:
        model = str(view.model or "").strip()
        if not model or model not in env:
            continue
        by_model[model].append(view)
    return by_model


def get_runtime_form_arch(env, model: str, view_id: int | None = None) -> str:
    Model = env[model].sudo()
    try:
        if view_id:
            data = Model.get_view(view_id=view_id, view_type="form")
        else:
            data = Model.get_view(view_type="form")
    except Exception:
        try:
            data = Model.fields_view_get(view_id=view_id or None, view_type="form", toolbar=False)
        except Exception:
            return ""
    if isinstance(data, dict):
        return str(data.get("arch") or "")
    return ""


def audit_runtime_views(env, limit: int = 0) -> list[FormViewAuditRow]:
    rows: list[FormViewAuditRow] = []
    candidates = runtime_form_view_candidates(env, limit=limit)
    for model in sorted(candidates):
        views = candidates[model]
        default_arch = get_runtime_form_arch(env, model)
        if default_arch:
            default_view = views[0] if views else None
            rows.append(audit_arch(
                audit_mode="runtime_default",
                module="runtime",
                file="odoo.registry",
                xmlid=external_xmlid(env, default_view) if default_view else "",
                view_name=f"{model}.runtime.default.form",
                model_name=model,
                inherit_id="",
                arch_xml=default_arch,
            ))
        for view in views:
            if not view.id:
                continue
            arch = get_runtime_form_arch(env, model, int(view.id))
            if not arch:
                continue
            rows.append(audit_arch(
                audit_mode="runtime_view",
                module="runtime",
                file="odoo.registry",
                xmlid=external_xmlid(env, view),
                view_name=str(view.name or ""),
                model_name=model,
                inherit_id=external_xmlid(env, view.inherit_id) if view.inherit_id else "",
                arch_xml=arch,
            ))
    return [row for row in rows if row is not None]


def write_json(path: Path, rows: list[FormViewAuditRow], summary: dict) -> None:
    path.write_text(
        json.dumps({"summary": summary, "rows": [asdict(row) for row in rows]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[FormViewAuditRow]) -> None:
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(FormViewAuditRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def markdown_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    headers = list(rows[0].keys())
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(header, "")).replace("|", "\\|") for header in headers) + " |")
    return "\n".join(out)


def write_markdown(path: Path, rows: list[FormViewAuditRow], summary: dict) -> None:
    by_class = Counter(row.classification for row in rows)
    by_module = Counter(row.module for row in rows)
    full_forms = [row for row in rows if row.arch_kind == "full_form"]
    weak = sorted(
        [row for row in full_forms if row.classification in {"needs_xml_structure", "contract_auto_with_default_tabs", "needs_semantic_annotation"}],
        key=lambda item: (item.structural_score, item.module, item.xmlid),
    )[:40]
    strong = sorted(
        [row for row in full_forms if row.classification == "auto_standardizable"],
        key=lambda item: (-item.structural_score, item.module, item.xmlid),
    )[:20]
    module_rows = [
        {"module": module, "views": count}
        for module, count in by_module.most_common(20)
    ]
    class_rows = [
        {"classification": key, "views": value}
        for key, value in by_class.most_common()
    ]
    weak_rows = [
        {
            "model": row.model,
            "xmlid": row.xmlid,
            "score": row.structural_score,
            "classification": row.classification,
            "gaps": row.gaps,
        }
        for row in weak
    ]
    strong_rows = [
        {
            "model": row.model,
            "xmlid": row.xmlid,
            "score": row.structural_score,
            "features": ",".join(
                key for key in ("statusbar", "button_box", "notebook", "chatter")
                if getattr(row, f"{key}_count", 0) > 0
            ),
        }
        for row in strong
    ]
    mode_label = str(summary.get("audit_mode") or "static_xml")
    title = "运行态表单结构标准化审计" if mode_label.startswith("runtime") else "表单结构标准化静态审计"
    runtime_note = "本审计通过 Odoo registry 读取运行态合并后的 form arch。" if mode_label.startswith("runtime") else "本审计只读扫描声明式 XML，不连接数据库，不合并运行态继承视图。继承片段需要下一阶段通过 Odoo registry 合并后的 `fields_view_get/get_view` 再做运行态确认。"
    text = f"""# {title}

## 结论摘要

- 扫描 XML form 视图：{summary["total_views"]}
- 完整 form：{summary["full_form_views"]}
- 继承片段：{summary["inherit_fragment_views"]}
- 可直接标准化：{summary["auto_standardizable"]}
- 需契约层生成默认页签：{summary["contract_auto_with_default_tabs"]}
- 需补语义标注：{summary["needs_semantic_annotation"]}
- 需补 XML 主结构：{summary["needs_xml_structure"]}

{runtime_note}

## 分类分布

{markdown_table(class_rows)}

## 模块分布

{markdown_table(module_rows)}

## 可作为标准化输入的样本

{markdown_table(strong_rows)}

## 优先处理缺口样本

{markdown_table(weak_rows)}

## 判定口径

- `auto_standardizable`：已有 `sheet/group/notebook/page`，并带有足够标题或锚点，可直接进入项目式契约标准化。
- `contract_auto_with_default_tabs`：已有主信息区，但缺少 notebook/page，可由契约层生成“主信息/明细/来源追溯/备注”等默认页签。
- `needs_semantic_annotation`：结构基本存在，但缺少标题或 `data-sc-anchor`，建议补少量语义标注。
- `needs_xml_structure`：缺少 `sheet` 或 `group`，契约层难以稳定判断主信息结构，建议先补 XML 主骨架。
- `inherit_fragment`：静态 XML 只是继承补丁，需运行态合并后确认。
"""
    path.write_text(text, encoding="utf-8")


def build_summary(rows: list[FormViewAuditRow]) -> dict:
    by_class = Counter(row.classification for row in rows)
    modes = Counter(row.audit_mode for row in rows)
    return {
        "audit_mode": ",".join(sorted(modes)) if modes else "",
        "total_views": len(rows),
        "full_form_views": sum(1 for row in rows if row.arch_kind == "full_form"),
        "inherit_fragment_views": sum(1 for row in rows if row.arch_kind == "inherited_fragment"),
        "auto_standardizable": by_class.get("auto_standardizable", 0),
        "contract_auto_with_default_tabs": by_class.get("contract_auto_with_default_tabs", 0),
        "needs_semantic_annotation": by_class.get("needs_semantic_annotation", 0),
        "needs_xml_structure": by_class.get("needs_xml_structure", 0),
        "inherit_fragment": by_class.get("inherit_fragment", 0),
        "manual_review": by_class.get("manual_review", 0),
        "by_classification": dict(sorted(by_class.items())),
        "by_audit_mode": dict(sorted(modes.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form view structures for contract-level standardization.")
    parser.add_argument("paths", nargs="*", help="Optional XML files or directories. Defaults to addon view/action XML.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for json/csv/md reports.")
    parser.add_argument("--runtime", action="store_true", help="Run inside `odoo shell` and audit merged runtime form arches.")
    parser.add_argument("--limit", type=int, default=0, help="Optional runtime ir.ui.view limit for quick probes.")
    args = parser.parse_args()

    if args.runtime:
        env_obj = globals().get("env")
        if env_obj is None:
            print("--runtime must be executed inside odoo shell where `env` is available", file=sys.stderr)
            return 2
        rows = audit_runtime_views(env_obj, limit=args.limit)
    else:
        files = iter_xml_files(args.paths or ["addons"])
        rows = audit_files(files)
    rows.sort(key=lambda row: (row.module, row.model, row.xmlid, row.file))
    summary = build_summary(rows)

    out_dir = Path(args.out_dir)
    if args.runtime and args.out_dir == str(DEFAULT_OUTPUT_DIR):
        out_dir = DEFAULT_RUNTIME_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "form_structure_standardization_audit.json", rows, summary)
    write_csv(out_dir / "form_structure_standardization_audit.csv", rows)
    write_markdown(out_dir / "form_structure_standardization_audit.md", rows, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {repo_rel(out_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
