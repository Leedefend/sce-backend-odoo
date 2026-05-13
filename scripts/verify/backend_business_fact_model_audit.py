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
DEFAULT_REGISTRY = ROOT / "docs" / "architecture" / "backend_business_fact_model_standard_registry_v1.json"
DEFAULT_PROBLEM_MAP = ROOT / "docs" / "architecture" / "backend_business_model_problem_map_v1.md"
ALLOWED_SOLUTION_LAYERS = {"platform", "industry", "customer"}


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
            implementation_kind = classify_implementation_kind(model_name, inherit)
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
                    "implementation_kind": implementation_kind,
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


def classify_implementation_kind(model_name: str | None, inherit: Any) -> str:
    if model_name and inherit:
        return "custom_model_with_mixin_or_inherit"
    if model_name:
        return "custom_model"
    return "native_model_extension"


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


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"models": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def registry_maps(registry: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    model_map = {item["model"]: item for item in registry.get("models", [])}
    exception_map = {
        item["model"]: {exception["field"] for exception in item.get("standard_exceptions", [])}
        for item in registry.get("models", [])
    }
    return model_map, exception_map


def summarize(rows: list[dict[str, Any]], registry: dict[str, Any]) -> dict[str, Any]:
    bucket_counts = Counter(bucket for row in rows for bucket in row["buckets"])
    implementation_counts = Counter(row["implementation_kind"] for row in rows)
    formal_rows = [row for row in rows if "formal_fact" in row["buckets"]]
    legacy_rows = [row for row in rows if "legacy_fact" in row["buckets"]]
    projection_rows = [row for row in rows if "projection" in row["buckets"]]
    registry_model_map, registry_exception_map = registry_maps(registry)
    detected_formal_models = {row["model"] for row in formal_rows}
    registered_formal_models = set(registry_model_map)
    standard_gaps = []
    undeclared_standard_gaps = []
    for row in formal_rows:
        exceptions = registry_exception_map.get(row["model"], set())
        missing = [field for field, present in row["standard_fields"].items() if not present]
        raw_gap = {
            "model": row["model"],
            "path": row["path"],
            "missing_standard_fields": missing,
            "has_legacy_unique_constraint": row["has_legacy_unique_constraint"],
            "has_legacy_confirmed_write_guard": row["has_legacy_confirmed_write_guard"],
            "declared_exceptions": sorted(exceptions),
        }
        has_raw_gap = missing or not row["has_legacy_unique_constraint"] or not row["has_legacy_confirmed_write_guard"]
        if not has_raw_gap:
            continue
        standard_gaps.append(raw_gap)
        undeclared_missing = [field for field in missing if field not in exceptions]
        undeclared_policy_gaps = []
        if not row["has_legacy_unique_constraint"] and "legacy_source_unique_constraint" not in exceptions:
            undeclared_policy_gaps.append("legacy_source_unique_constraint")
        if not row["has_legacy_confirmed_write_guard"] and "legacy_confirmed_write_guard" not in exceptions:
            undeclared_policy_gaps.append("legacy_confirmed_write_guard")
        if undeclared_missing or undeclared_policy_gaps or row["model"] not in registered_formal_models:
            undeclared_standard_gaps.append(
                {
                    **raw_gap,
                    "undeclared_missing_standard_fields": undeclared_missing,
                    "undeclared_policy_gaps": undeclared_policy_gaps,
                    "registered": row["model"] in registered_formal_models,
                }
            )
    registry_path_gaps = []
    registry_shape_gaps = []
    solution_layer_counts: Counter[str] = Counter()
    for model, item in registry_model_map.items():
        solution_layer = item.get("solution_layer")
        if solution_layer in ALLOWED_SOLUTION_LAYERS:
            solution_layer_counts[solution_layer] += 1
        else:
            registry_shape_gaps.append(
                {
                    "model": model,
                    "field": "solution_layer",
                    "value": solution_layer,
                    "allowed_values": sorted(ALLOWED_SOLUTION_LAYERS),
                }
            )
        for required_field in ("target_problem", "promotion_policy", "business_logic", "business_domain"):
            if not str(item.get(required_field) or "").strip():
                registry_shape_gaps.append({"model": model, "field": required_field, "value": item.get(required_field)})
        for key in ("projection_scripts", "runtime_probes"):
            for raw_path in item.get(key, []):
                if not (ROOT / raw_path).exists():
                    registry_path_gaps.append({"model": model, "kind": key, "path": raw_path})
    return {
        "model_count": len(rows),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "implementation_counts": dict(sorted(implementation_counts.items())),
        "native_extension_count": implementation_counts.get("native_model_extension", 0),
        "custom_model_count": implementation_counts.get("custom_model", 0),
        "custom_model_with_mixin_or_inherit_count": implementation_counts.get("custom_model_with_mixin_or_inherit", 0),
        "legacy_fact_model_count": len(legacy_rows),
        "formal_fact_model_count": len(formal_rows),
        "projection_model_count": len(projection_rows),
        "registered_formal_model_count": len(registered_formal_models),
        "solution_layer_counts": dict(sorted(solution_layer_counts.items())),
        "unregistered_formal_models": sorted(detected_formal_models - registered_formal_models),
        "registered_models_not_detected": sorted(registered_formal_models - detected_formal_models),
        "raw_standard_gap_count": len(standard_gaps),
        "standard_gaps": standard_gaps,
        "undeclared_standard_gap_count": len(undeclared_standard_gaps),
        "undeclared_standard_gaps": undeclared_standard_gaps,
        "registry_path_gap_count": len(registry_path_gaps),
        "registry_path_gaps": registry_path_gaps,
        "registry_shape_gap_count": len(registry_shape_gaps),
        "registry_shape_gaps": registry_shape_gaps,
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
        f"- native_extension_count: {summary['native_extension_count']}",
        f"- custom_model_count: {summary['custom_model_count']}",
        f"- custom_model_with_mixin_or_inherit_count: {summary['custom_model_with_mixin_or_inherit_count']}",
        f"- legacy_fact_model_count: {summary['legacy_fact_model_count']}",
        f"- formal_fact_model_count: {summary['formal_fact_model_count']}",
        f"- projection_model_count: {summary['projection_model_count']}",
        f"- registered_formal_model_count: {summary['registered_formal_model_count']}",
        f"- solution_layer_counts: {json.dumps(summary['solution_layer_counts'], ensure_ascii=False, sort_keys=True)}",
        f"- raw_standard_gap_count: {summary['raw_standard_gap_count']}",
        f"- undeclared_standard_gap_count: {summary['undeclared_standard_gap_count']}",
        f"- registry_path_gap_count: {summary['registry_path_gap_count']}",
        f"- registry_shape_gap_count: {summary['registry_shape_gap_count']}",
        "",
        "## Bucket Counts",
        "",
    ]
    for key, value in summary["bucket_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Implementation Counts", ""])
    for key, value in summary["implementation_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Native Model Extensions", ""])
    for row in rows:
        if row["implementation_kind"] != "native_model_extension":
            continue
        lines.append(f"- `{row['inherit']}` ({row['path']})")
    lines.extend(["", "## Formal Fact Standard Gaps", ""])
    if summary["standard_gaps"]:
        lines.append("| model | missing fields | declared exceptions | legacy unique | legacy write guard | path |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for gap in summary["standard_gaps"]:
            missing = ", ".join(gap["missing_standard_fields"]) or "-"
            exceptions = ", ".join(gap["declared_exceptions"]) or "-"
            lines.append(
                "| {model} | {missing} | {exceptions} | {unique} | {guard} | {path} |".format(
                    model=gap["model"],
                    missing=missing,
                    exceptions=exceptions,
                    unique="yes" if gap["has_legacy_unique_constraint"] else "no",
                    guard="yes" if gap["has_legacy_confirmed_write_guard"] else "no",
                    path=gap["path"],
                )
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Registry Coverage", ""])
    lines.append(f"- unregistered_formal_models: {', '.join(summary['unregistered_formal_models']) or 'none'}")
    lines.append(f"- registered_models_not_detected: {', '.join(summary['registered_models_not_detected']) or 'none'}")
    if summary["registry_path_gaps"]:
        lines.append("")
        lines.append("| model | kind | missing path |")
        lines.append("| --- | --- | --- |")
        for gap in summary["registry_path_gaps"]:
            lines.append(f"| {gap['model']} | {gap['kind']} | {gap['path']} |")
    else:
        lines.append("- registry_path_gaps: none")
    if summary["registry_shape_gaps"]:
        lines.append("")
        lines.append("| model | field | value |")
        lines.append("| --- | --- | --- |")
        for gap in summary["registry_shape_gaps"]:
            lines.append(f"| {gap['model']} | {gap['field']} | {gap.get('value')} |")
    else:
        lines.append("- registry_shape_gaps: none")
    lines.extend(["", "## Solution Layers", ""])
    model_map, _ = registry_maps(report["registry"])
    for layer in sorted(ALLOWED_SOLUTION_LAYERS):
        layer_models = [item for item in model_map.values() if item.get("solution_layer") == layer]
        if not layer_models:
            continue
        lines.append(f"### {layer}")
        lines.append("")
        for item in layer_models:
            lines.append(f"- `{item['model']}`: {item.get('target_problem') or ''}")
        lines.append("")
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
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY.relative_to(ROOT)))
    parser.add_argument("--problem-map", default=str(DEFAULT_PROBLEM_MAP.relative_to(ROOT)))
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Fail when formal models are unregistered, registered paths are missing, or standard gaps are undeclared.",
    )
    args = parser.parse_args()

    rows = extract_models()
    registry = load_registry(ROOT / args.registry)
    report = {"summary": summarize(rows, registry), "registry": registry, "models": rows}
    report_path = ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, ROOT / args.markdown)
    summary = report["summary"]
    print("BACKEND_BUSINESS_FACT_MODEL_AUDIT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    if args.enforce:
        problem_map_path = ROOT / args.problem_map
        problem_map_text = problem_map_path.read_text(encoding="utf-8") if problem_map_path.exists() else ""
        blockers = {
            "unregistered_formal_models": summary["unregistered_formal_models"],
            "registered_models_not_detected": summary["registered_models_not_detected"],
            "undeclared_standard_gaps": summary["undeclared_standard_gaps"],
            "registry_path_gaps": summary["registry_path_gaps"],
            "registry_shape_gaps": summary["registry_shape_gaps"],
            "problem_map_gaps": []
            if problem_map_path.exists() and "## Boundary Conclusions" in problem_map_text
            else [{"path": str(problem_map_path.relative_to(ROOT)), "reason": "missing_problem_map_or_boundary_conclusions"}],
        }
        if any(blockers.values()):
            print("BACKEND_BUSINESS_FACT_MODEL_AUDIT_BLOCKERS=" + json.dumps(blockers, ensure_ascii=False, sort_keys=True))
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
