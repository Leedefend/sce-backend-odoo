#!/usr/bin/env python3
"""Static audit for backend business fact model shape.

The audit intentionally avoids a live Odoo registry. It reads model source files
and reports which models carry legacy facts, runtime business documents,
projection/read models, and source-trace fields.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MODEL_ROOT = ROOT / "addons" / "smart_construction_core" / "models"

STANDARD_FIELDS = [
    "source_origin",
    "state",
    "project_id",
    "company_id",
    "partner_id",
    "currency_id",
    "legacy_source_model",
    "legacy_source_table",
    "legacy_record_id",
    "legacy_document_state",
    "active",
]

TRACE_FIELD_RE = re.compile(r"^(legacy_|source_(origin|kind|model|table|res_id)|creator_legacy_user_id)")
AMOUNT_FIELD_RE = re.compile(r"(amount|qty|quantity|price|balance|total|tax|rate|count)")


def literal(node: ast.AST) -> Any:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return f"{func.value.id}.{func.attr}"
    return ""


def extract_models() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(MODEL_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            model_name = None
            inherit = None
            description = None
            constraints: list[Any] = []
            fields: list[dict[str, str]] = []
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                target_names = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
                if "_name" in target_names:
                    model_name = literal(stmt.value)
                if "_inherit" in target_names:
                    inherit = literal(stmt.value)
                if "_description" in target_names:
                    description = literal(stmt.value)
                if "_sql_constraints" in target_names:
                    constraints = literal(stmt.value) or []
                for target in stmt.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    field_call = call_name(stmt.value)
                    if not field_call.startswith("fields."):
                        continue
                    comodel = ""
                    if isinstance(stmt.value, ast.Call) and stmt.value.args:
                        first_arg = literal(stmt.value.args[0])
                        if isinstance(first_arg, str):
                            comodel = first_arg
                    fields.append(
                        {
                            "name": target.id,
                            "type": field_call.split(".", 1)[1],
                            "comodel": comodel,
                        }
                    )
            if not model_name and not inherit:
                continue
            field_names = {field["name"] for field in fields}
            field_types = {field["name"]: field["type"] for field in fields}
            path_text = str(path.relative_to(ROOT))
            buckets = classify_model(path_text, model_name, inherit, description, field_names, field_types)
            constraint_text = json.dumps(constraints, ensure_ascii=False)
            rows.append(
                {
                    "path": path_text,
                    "class": node.name,
                    "model": model_name,
                    "inherit": inherit,
                    "description": description,
                    "field_count": len(fields),
                    "fields": fields,
                    "buckets": buckets,
                    "standard_fields": {field: field in field_names for field in STANDARD_FIELDS},
                    "has_legacy_unique_constraint": "legacy_source_unique" in constraint_text
                    or "unique(legacy_source_model, legacy_record_id)" in constraint_text,
                    "has_legacy_confirmed_write_guard": "legacy_confirmed" in source
                    and "source_origin" in source
                    and "def write" in source,
                }
            )
    return rows


def classify_model(
    path: str,
    model_name: str | None,
    inherit: Any,
    description: str | None,
    field_names: set[str],
    field_types: dict[str, str],
) -> list[str]:
    text = " ".join([path, model_name or "", str(inherit or ""), description or ""])
    buckets: set[str] = set()
    if "/core/" in path:
        buckets.add("core")
    if "/support/" in path:
        buckets.add("support")
    if "/projection/" in path or re.search(r"(summary|ledger|cockpit|workbench)", model_name or ""):
        buckets.add("projection")
    if model_name and model_name.startswith("sc.legacy"):
        buckets.add("legacy_fact")
    if any(TRACE_FIELD_RE.search(field_name) for field_name in field_names):
        buckets.add("traceable")
    if "state" in field_names:
        buckets.add("stateful")
    if any(field_types.get(name) in {"Monetary", "Float", "Integer"} and AMOUNT_FIELD_RE.search(name) for name in field_names):
        buckets.add("quantitative")
    if "source_origin" in field_names and "legacy_source_model" in field_names and "legacy_record_id" in field_names:
        buckets.add("formal_fact")
    if "sc.business.fact.mixin" in text:
        buckets.add("business_fact_mixin")
    return sorted(buckets)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_counts = Counter(bucket for row in rows for bucket in row["buckets"])
    formal_rows = [row for row in rows if "formal_fact" in row["buckets"]]
    legacy_rows = [row for row in rows if "legacy_fact" in row["buckets"]]
    projection_rows = [row for row in rows if "projection" in row["buckets"]]
    standard_gaps = []
    for row in formal_rows:
        missing = [field for field, present in row["standard_fields"].items() if not present]
        if missing or not row["has_legacy_unique_constraint"] or not row["has_legacy_confirmed_write_guard"]:
            standard_gaps.append(
                {
                    "model": row["model"],
                    "path": row["path"],
                    "missing_standard_fields": missing,
                    "has_legacy_unique_constraint": row["has_legacy_unique_constraint"],
                    "has_legacy_confirmed_write_guard": row["has_legacy_confirmed_write_guard"],
                }
            )
    return {
        "model_count": len(rows),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "legacy_fact_model_count": len(legacy_rows),
        "formal_fact_model_count": len(formal_rows),
        "projection_model_count": len(projection_rows),
        "standard_gap_count": len(standard_gaps),
        "standard_gaps": standard_gaps,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    rows = report["models"]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Backend Business Fact Model Static Audit",
        "",
        "## Summary",
        "",
        f"- model_count: {summary['model_count']}",
        f"- legacy_fact_model_count: {summary['legacy_fact_model_count']}",
        f"- formal_fact_model_count: {summary['formal_fact_model_count']}",
        f"- projection_model_count: {summary['projection_model_count']}",
        f"- standard_gap_count: {summary['standard_gap_count']}",
        "",
        "## Bucket Counts",
        "",
    ]
    for key, value in summary["bucket_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Formal Fact Standard Gaps", ""])
    if summary["standard_gaps"]:
        lines.append("| model | missing fields | legacy unique | legacy write guard | path |")
        lines.append("| --- | --- | --- | --- | --- |")
        for gap in summary["standard_gaps"]:
            missing = ", ".join(gap["missing_standard_fields"]) or "-"
            lines.append(
                "| {model} | {missing} | {unique} | {guard} | {path} |".format(
                    model=gap["model"],
                    missing=missing,
                    unique="yes" if gap["has_legacy_unique_constraint"] else "no",
                    guard="yes" if gap["has_legacy_confirmed_write_guard"] else "no",
                    path=gap["path"],
                )
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Formal Fact Models", ""])
    for row in rows:
        if "formal_fact" not in row["buckets"]:
            continue
        lines.append(f"- `{row['model']}`: {row.get('description') or ''} ({row['path']})")
    lines.extend(["", "## Legacy Fact Models", ""])
    for row in rows:
        if "legacy_fact" not in row["buckets"]:
            continue
        lines.append(f"- `{row['model']}`: {row.get('description') or ''} ({row['path']})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="artifacts/backend/backend_business_fact_model_audit.json")
    parser.add_argument("--markdown", default="artifacts/backend/backend_business_fact_model_audit.md")
    args = parser.parse_args()

    rows = extract_models()
    report = {"summary": summarize(rows), "models": rows}
    report_path = ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, ROOT / args.markdown)
    print("BACKEND_BUSINESS_FACT_MODEL_AUDIT=" + json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
