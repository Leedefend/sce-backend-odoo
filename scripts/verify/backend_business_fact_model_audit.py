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
DEFAULT_RESPONSIBILITY_MATRIX = ROOT / "docs" / "architecture" / "backend_business_model_responsibility_matrix_v1.md"
DEFAULT_OBJECT_HIERARCHY = ROOT / "docs" / "architecture" / "backend_business_object_hierarchy_v1.md"
DEFAULT_FAMILY_REGISTRY = ROOT / "docs" / "architecture" / "backend_business_model_family_registry_v1.json"
DEFAULT_OWNERSHIP_SPECS = ROOT / "docs" / "architecture" / "backend_business_model_ownership_specs_v1.json"
DEFAULT_AUDIT_FINDINGS = ROOT / "docs" / "architecture" / "backend_business_model_audit_findings_v1.md"
DEFAULT_OVERLAP_ANALYSIS = ROOT / "docs" / "architecture" / "backend_business_model_overlap_analysis_v1.md"
DEFAULT_PROJECTION_REGISTRY = ROOT / "docs" / "architecture" / "backend_business_projection_registry_v1.json"
DEFAULT_MANAGEMENT_HIERARCHY = ROOT / "docs" / "architecture" / "backend_business_management_hierarchy_v1.json"
ALLOWED_SOLUTION_LAYERS = {"platform", "industry", "customer"}
ALLOWED_RESPONSIBILITY_TYPES = {
    "native system-of-record",
    "industry source-of-truth",
    "projection/read model",
    "legacy source carrier",
    "governance/config",
    "compatibility/bridge",
}
ALLOWED_BUSINESS_OBJECTS = {
    "company",
    "business",
    "income",
    "expense",
    "bilateral_mixed",
    "project",
    "projection",
    "legacy",
    "governance",
    "platform",
}
ALLOWED_PROJECTION_MODES = {
    "sql_view",
    "physical_refresh_table",
    "controlled_generated_ledger",
    "computed_runtime_summary",
    "runtime_workbench_fact",
}
ALLOWED_MANAGEMENT_SUBJECTS = {"platform", "company", "business", "project", "source_system"}
ALLOWED_MANAGED_OBJECTS = {
    "company",
    "business",
    "project",
    "business_fact",
    "identity",
    "policy",
    "visibility",
    "evidence",
    "capability",
}
ALLOWED_PROJECT_CARRIER_ROLES = {
    "primary",
    "optional",
    "pre_project",
    "company_level",
    "not_applicable",
    "derived",
}


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
            model_family = classify_model_family(path_text, model_name, inherit, buckets)
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
                    "model_family": model_family,
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


def model_ref(model_name: str | None, inherit: Any) -> str:
    if model_name:
        return model_name
    if isinstance(inherit, str):
        return inherit
    if isinstance(inherit, list):
        return " ".join(item for item in inherit if isinstance(item, str))
    return ""


def classify_model_family(path: str, model_name: str | None, inherit: Any, buckets: list[str]) -> str:
    ref = model_ref(model_name, inherit)
    text = " ".join([path, ref])

    if "projection" in buckets:
        return "projection summaries and management visibility"
    if ref.startswith("sc.legacy") or ref == "sc.history.todo" or "legacy_" in path:
        return "legacy replay and historical evidence"
    if any(key in ref for key in ("sc.scene", "sc.capability", "sc.subscription", "sc.entitlement", "sc.usage.counter", "sc.ops.job")):
        return "scene capability subscription and frontend contract runtime"
    if any(key in ref for key in ("sc.workflow", "sc.approval", "sc.dictionary", "sc.audit", "sc.data.validator", "tier.definition")):
        return "workflow approval dictionary audit and validation"
    if any(key in ref for key in ("res.company", "res.config.settings", "res.users", "res.groups", "sc.business.entity", "sc.pack")):
        return "company and business governance"
    if any(key in ref for key in ("res.partner", "res.partner.bank", "sc.supplier.type", "sc.partner.import.review")):
        return "partner and counterparty identity"
    if any(key in ref for key in ("product.template", "product.category", "sc.material.catalog", "sc.material.price")):
        return "product and material identity"
    if (
        ref.startswith("project.")
        and not any(key in ref for key in ("project.budget", "project.boq", "project.cost", "project.material", "project.progress", "project.risk", "project.settlement"))
    ) or any(key in ref for key in ("project.task", "project.wbs", "construction.work.breakdown", "sc.project.structure", "sc.project.member", "sc.project.next_action", "sc.project.stage")):
        return "project identity and execution carrier"
    if "tender." in ref or ref == "construction.contract.income":
        return "income contract and tender business"
    if any(key in ref for key in ("sc.general.contract", "construction.contract.expense", "construction.contract.line")):
        return "expense contract and procurement commitment"
    if ref == "construction.contract" or any(key in ref for key in ("construction.contract.professional.mixin", "sc.contract.event", "sc.contract.recon")):
        return "income contract and tender business"
    if any(key in ref for key in ("payment.request", "payment.ledger", "sc.payment.execution", "sc.expense.claim")):
        return "payment request and payment execution"
    if any(key in ref for key in ("sc.receipt", "sc.invoice", "sc.tax.deduction", "sc.financing.loan")):
        return "receipt income invoice and tax realization"
    if any(key in ref for key in ("sc.fund", "sc.treasury")):
        return "treasury account reconciliation and ledger"
    if any(key in ref for key in ("project.budget", "project.boq", "project.cost", "project.funding", "project.settlement", "sc.settlement")):
        return "project budget BOQ and cost control"
    if any(key in ref for key in ("project.material", "sc.material", "purchase.order", "stock.")):
        return "material lifecycle"
    if any(key in ref for key in ("sc.labor", "sc.equipment", "sc.subcontract", "sc.attendance")):
        return "labor equipment and subcontract lifecycle"
    if any(
        key in ref
        for key in (
            "project.progress",
            "project.risk",
            "sc.quality",
            "sc.safety",
            "sc.risk",
            "sc.hazard",
            "sc.check",
            "sc.site.photo",
            "sc.construction.diary",
            "sc.plan",
        )
    ):
        return "progress quality safety risk and diary"
    if any(key in ref for key in ("sc.document", "sc.office", "sc.hr.payroll", "hr.department", "sc.project.document")):
        return "document admin payroll and office operations"
    if any(
        key in ref
        for key in (
            "account.move",
            "account.move.line",
            "sc.business.fact.mixin",
            "sc.delete.guard.mixin",
            "sc.system.default.mixin",
            "sc.material.system.default.mixin",
        )
    ):
        return "compatibility bridges and native extensions"
    if "support/" in text:
        return "compatibility bridges and native extensions"
    return "unclassified"


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"models": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_family_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"families": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_ownership_specs(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ownership_specs": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_projection_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"projections": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_management_hierarchy(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"family_hierarchy": [], "missing_registry": True}
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
    family_counts = Counter(row.get("model_family") or "unclassified" for row in rows)
    unclassified_rows = [
        {
            "model": row.get("model"),
            "inherit": row.get("inherit"),
            "path": row["path"],
            "implementation_kind": row["implementation_kind"],
        }
        for row in rows
        if row.get("model_family") == "unclassified"
    ]
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
        "model_family_counts": dict(sorted(family_counts.items())),
        "unclassified_model_count": len(unclassified_rows),
        "unclassified_models": unclassified_rows,
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


def summarize_family_registry(rows: list[dict[str, Any]], family_registry: dict[str, Any]) -> dict[str, Any]:
    families = family_registry.get("families", [])
    detected_models = {row["model"] for row in rows if row.get("model")}
    detected_native_inherits: set[str] = set()
    for row in rows:
        inherit = row.get("inherit")
        if isinstance(inherit, str):
            detected_native_inherits.add(inherit)
        elif isinstance(inherit, list):
            detected_native_inherits.update(item for item in inherit if isinstance(item, str))
    detected_reference_names = detected_models | detected_native_inherits

    required_fields = [
        "family",
        "responsibility_type",
        "solution_layer",
        "business_object",
        "source_of_truth",
        "native_dependency",
        "target_problem",
        "boundary_rule",
        "status",
    ]
    shape_gaps = []
    reference_gaps = []
    layer_counts: Counter[str] = Counter()
    responsibility_counts: Counter[str] = Counter()
    business_object_counts: Counter[str] = Counter()
    for family in families:
        family_key = family.get("family")
        for field in required_fields:
            if not str(family.get(field) or "").strip():
                shape_gaps.append({"family": family_key, "field": field, "reason": "missing_required_field"})
        layer = family.get("solution_layer")
        if layer in ALLOWED_SOLUTION_LAYERS:
            layer_counts[layer] += 1
        else:
            shape_gaps.append(
                {
                    "family": family_key,
                    "field": "solution_layer",
                    "value": layer,
                    "allowed_values": sorted(ALLOWED_SOLUTION_LAYERS),
                }
            )
        responsibility = family.get("responsibility_type")
        if responsibility in ALLOWED_RESPONSIBILITY_TYPES:
            responsibility_counts[responsibility] += 1
        else:
            shape_gaps.append(
                {
                    "family": family_key,
                    "field": "responsibility_type",
                    "value": responsibility,
                    "allowed_values": sorted(ALLOWED_RESPONSIBILITY_TYPES),
                }
            )
        business_object = family.get("business_object")
        if business_object in ALLOWED_BUSINESS_OBJECTS:
            business_object_counts[business_object] += 1
        else:
            shape_gaps.append(
                {
                    "family": family_key,
                    "field": "business_object",
                    "value": business_object,
                    "allowed_values": sorted(ALLOWED_BUSINESS_OBJECTS),
                }
            )
        for model in family.get("representative_models", []):
            if model not in detected_reference_names:
                reference_gaps.append({"family": family_key, "model": model})
    return {
        "family_registry_count": len(families),
        "family_solution_layer_counts": dict(sorted(layer_counts.items())),
        "family_responsibility_counts": dict(sorted(responsibility_counts.items())),
        "family_business_object_counts": dict(sorted(business_object_counts.items())),
        "family_registry_shape_gap_count": len(shape_gaps),
        "family_registry_shape_gaps": shape_gaps,
        "family_registry_reference_gap_count": len(reference_gaps),
        "family_registry_reference_gaps": reference_gaps,
    }


def summarize_ownership_specs(rows: list[dict[str, Any]], ownership_specs: dict[str, Any]) -> dict[str, Any]:
    specs = ownership_specs.get("ownership_specs", [])
    detected_models = {row["model"] for row in rows if row.get("model")}
    detected_native_inherits: set[str] = set()
    for row in rows:
        inherit = row.get("inherit")
        if isinstance(inherit, str):
            detected_native_inherits.add(inherit)
        elif isinstance(inherit, list):
            detected_native_inherits.update(item for item in inherit if isinstance(item, str))
    detected_reference_names = detected_models | detected_native_inherits

    required_fields = [
        "spec",
        "risk_family",
        "business_object",
        "fact_source_model",
        "allowed_support_models",
        "projection_models",
        "boundary_rule",
        "forbidden_drift",
        "decision",
    ]
    shape_gaps = []
    reference_gaps = []
    for spec in specs:
        spec_key = spec.get("spec")
        for field in required_fields:
            value = spec.get(field)
            if isinstance(value, list):
                if not value:
                    shape_gaps.append({"spec": spec_key, "field": field, "reason": "missing_required_list"})
            elif not str(value or "").strip():
                shape_gaps.append({"spec": spec_key, "field": field, "reason": "missing_required_field"})
        if spec.get("business_object") not in ALLOWED_BUSINESS_OBJECTS:
            shape_gaps.append(
                {
                    "spec": spec_key,
                    "field": "business_object",
                    "value": spec.get("business_object"),
                    "allowed_values": sorted(ALLOWED_BUSINESS_OBJECTS),
                }
            )
        for key in ("fact_source_model", "allowed_support_models", "projection_models"):
            raw_models = spec.get(key, [])
            models = raw_models if isinstance(raw_models, list) else [raw_models]
            for model in models:
                if model and model not in detected_reference_names:
                    reference_gaps.append({"spec": spec_key, "field": key, "model": model})
    return {
        "ownership_spec_count": len(specs),
        "ownership_spec_shape_gap_count": len(shape_gaps),
        "ownership_spec_shape_gaps": shape_gaps,
        "ownership_spec_reference_gap_count": len(reference_gaps),
        "ownership_spec_reference_gaps": reference_gaps,
    }


def summarize_projection_registry(rows: list[dict[str, Any]], projection_registry: dict[str, Any]) -> dict[str, Any]:
    projections = projection_registry.get("projections", [])
    detected_models = {row["model"] for row in rows if row.get("model")}
    detected_projection_models = {row["model"] for row in rows if row.get("model") and "projection" in row["buckets"]}
    registry_map = {item.get("model"): item for item in projections if item.get("model")}
    required_fields = [
        "model",
        "implementation_mode",
        "write_policy",
        "source_models",
        "refresh_owner",
        "idempotency_key",
        "acceptance_probe",
    ]
    shape_gaps = []
    reference_gaps = []
    mode_counts: Counter[str] = Counter()
    for item in projections:
        model = item.get("model")
        for field in required_fields:
            value = item.get(field)
            if isinstance(value, list):
                if not value:
                    shape_gaps.append({"model": model, "field": field, "reason": "missing_required_list"})
            elif not str(value or "").strip():
                shape_gaps.append({"model": model, "field": field, "reason": "missing_required_field"})
        mode = item.get("implementation_mode")
        if mode in ALLOWED_PROJECTION_MODES:
            mode_counts[mode] += 1
        else:
            shape_gaps.append(
                {
                    "model": model,
                    "field": "implementation_mode",
                    "value": mode,
                    "allowed_values": sorted(ALLOWED_PROJECTION_MODES),
                }
            )
        if model and model not in detected_models:
            reference_gaps.append({"model": model, "field": "model", "reason": "model_not_detected"})
    return {
        "projection_registry_count": len(projections),
        "projection_mode_counts": dict(sorted(mode_counts.items())),
        "unregistered_projection_models": sorted(detected_projection_models - set(registry_map)),
        "registered_projection_models_not_detected": sorted(set(registry_map) - detected_models),
        "projection_registry_shape_gap_count": len(shape_gaps),
        "projection_registry_shape_gaps": shape_gaps,
        "projection_registry_reference_gap_count": len(reference_gaps),
        "projection_registry_reference_gaps": reference_gaps,
    }


def summarize_management_hierarchy(
    family_registry: dict[str, Any], management_hierarchy: dict[str, Any]
) -> dict[str, Any]:
    family_names = {item.get("family") for item in family_registry.get("families", []) if item.get("family")}
    hierarchy_rows = management_hierarchy.get("family_hierarchy", [])
    hierarchy_map = {item.get("family"): item for item in hierarchy_rows if item.get("family")}
    required_fields = [
        "family",
        "management_subject",
        "managed_object",
        "project_carrier_role",
        "hierarchy_statement",
    ]
    shape_gaps = []
    subject_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    carrier_counts: Counter[str] = Counter()
    for item in hierarchy_rows:
        family = item.get("family")
        for field in required_fields:
            if not str(item.get(field) or "").strip():
                shape_gaps.append({"family": family, "field": field, "reason": "missing_required_field"})
        subject = item.get("management_subject")
        if subject in ALLOWED_MANAGEMENT_SUBJECTS:
            subject_counts[subject] += 1
        else:
            shape_gaps.append(
                {
                    "family": family,
                    "field": "management_subject",
                    "value": subject,
                    "allowed_values": sorted(ALLOWED_MANAGEMENT_SUBJECTS),
                }
            )
        managed_object = item.get("managed_object")
        if managed_object in ALLOWED_MANAGED_OBJECTS:
            object_counts[managed_object] += 1
        else:
            shape_gaps.append(
                {
                    "family": family,
                    "field": "managed_object",
                    "value": managed_object,
                    "allowed_values": sorted(ALLOWED_MANAGED_OBJECTS),
                }
            )
        carrier_role = item.get("project_carrier_role")
        if carrier_role in ALLOWED_PROJECT_CARRIER_ROLES:
            carrier_counts[carrier_role] += 1
        else:
            shape_gaps.append(
                {
                    "family": family,
                    "field": "project_carrier_role",
                    "value": carrier_role,
                    "allowed_values": sorted(ALLOWED_PROJECT_CARRIER_ROLES),
                }
            )
    return {
        "management_hierarchy_count": len(hierarchy_rows),
        "management_subject_counts": dict(sorted(subject_counts.items())),
        "managed_object_counts": dict(sorted(object_counts.items())),
        "project_carrier_role_counts": dict(sorted(carrier_counts.items())),
        "hierarchy_families_missing": sorted(family_names - set(hierarchy_map)),
        "hierarchy_unknown_families": sorted(set(hierarchy_map) - family_names),
        "management_hierarchy_shape_gap_count": len(shape_gaps),
        "management_hierarchy_shape_gaps": shape_gaps,
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
        f"- unclassified_model_count: {summary['unclassified_model_count']}",
        "",
        "## Bucket Counts",
        "",
    ]
    for key, value in summary["bucket_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Implementation Counts", ""])
    for key, value in summary["implementation_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Model Family Counts", ""])
    for key, value in summary["model_family_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Unclassified Models", ""])
    if summary["unclassified_models"]:
        lines.append("| model | inherit | implementation | path |")
        lines.append("| --- | --- | --- | --- |")
        for row in summary["unclassified_models"]:
            lines.append(
                f"| {row.get('model') or ''} | {row.get('inherit') or ''} | {row['implementation_kind']} | {row['path']} |"
            )
    else:
        lines.append("- none")
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
    family_summary = report.get("family_summary") or {}
    family_registry = report.get("family_registry") or {}
    lines.extend(["", "## Family Registry", ""])
    lines.append(f"- family_registry_count: {family_summary.get('family_registry_count', 0)}")
    lines.append(
        "- family_solution_layer_counts: "
        + json.dumps(family_summary.get("family_solution_layer_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(
        "- family_responsibility_counts: "
        + json.dumps(family_summary.get("family_responsibility_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(
        "- family_business_object_counts: "
        + json.dumps(family_summary.get("family_business_object_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(f"- family_registry_shape_gap_count: {family_summary.get('family_registry_shape_gap_count', 0)}")
    lines.append(f"- family_registry_reference_gap_count: {family_summary.get('family_registry_reference_gap_count', 0)}")
    if family_registry.get("families"):
        lines.extend(["", "| family | business object | responsibility | solution layer | target problem |"])
        lines.append("| --- | --- | --- | --- | --- |")
        for family in family_registry["families"]:
            lines.append(
                "| {family} | {business_object} | {responsibility_type} | {solution_layer} | {target_problem} |".format(
                    family=family.get("family", ""),
                    business_object=family.get("business_object", ""),
                    responsibility_type=family.get("responsibility_type", ""),
                    solution_layer=family.get("solution_layer", ""),
                    target_problem=family.get("target_problem", ""),
                )
            )
    ownership_summary = report.get("ownership_summary") or {}
    ownership_specs = report.get("ownership_specs") or {}
    lines.extend(["", "## Ownership Specs", ""])
    lines.append(f"- ownership_spec_count: {ownership_summary.get('ownership_spec_count', 0)}")
    lines.append(f"- ownership_spec_shape_gap_count: {ownership_summary.get('ownership_spec_shape_gap_count', 0)}")
    lines.append(f"- ownership_spec_reference_gap_count: {ownership_summary.get('ownership_spec_reference_gap_count', 0)}")
    if ownership_specs.get("ownership_specs"):
        lines.extend(["", "| spec | risk family | business object | decision |"])
        lines.append("| --- | --- | --- | --- |")
        for spec in ownership_specs["ownership_specs"]:
            lines.append(
                "| {spec} | {risk_family} | {business_object} | {decision} |".format(
                    spec=spec.get("spec", ""),
                    risk_family=spec.get("risk_family", ""),
                    business_object=spec.get("business_object", ""),
                    decision=spec.get("decision", ""),
                )
            )
    projection_summary = report.get("projection_summary") or {}
    projection_registry = report.get("projection_registry") or {}
    lines.extend(["", "## Projection Registry", ""])
    lines.append(f"- projection_registry_count: {projection_summary.get('projection_registry_count', 0)}")
    lines.append(
        "- projection_mode_counts: "
        + json.dumps(projection_summary.get("projection_mode_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(
        "- unregistered_projection_models: "
        + (", ".join(projection_summary.get("unregistered_projection_models", [])) or "none")
    )
    lines.append(
        "- registered_projection_models_not_detected: "
        + (", ".join(projection_summary.get("registered_projection_models_not_detected", [])) or "none")
    )
    if projection_registry.get("projections"):
        lines.extend(["", "| model | mode | write policy | refresh owner |"])
        lines.append("| --- | --- | --- | --- |")
        for item in projection_registry["projections"]:
            lines.append(
                "| {model} | {implementation_mode} | {write_policy} | {refresh_owner} |".format(
                    model=item.get("model", ""),
                    implementation_mode=item.get("implementation_mode", ""),
                    write_policy=item.get("write_policy", ""),
                    refresh_owner=item.get("refresh_owner", ""),
                )
            )
    hierarchy_summary = report.get("management_hierarchy_summary") or {}
    management_hierarchy = report.get("management_hierarchy") or {}
    lines.extend(["", "## Management Hierarchy", ""])
    lines.append(f"- management_hierarchy_count: {hierarchy_summary.get('management_hierarchy_count', 0)}")
    lines.append(
        "- management_subject_counts: "
        + json.dumps(hierarchy_summary.get("management_subject_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(
        "- project_carrier_role_counts: "
        + json.dumps(hierarchy_summary.get("project_carrier_role_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(
        "- hierarchy_families_missing: "
        + (", ".join(hierarchy_summary.get("hierarchy_families_missing", [])) or "none")
    )
    if management_hierarchy.get("family_hierarchy"):
        lines.extend(["", "| family | subject | object | project carrier |"])
        lines.append("| --- | --- | --- | --- |")
        for item in management_hierarchy["family_hierarchy"]:
            lines.append(
                "| {family} | {management_subject} | {managed_object} | {project_carrier_role} |".format(
                    family=item.get("family", ""),
                    management_subject=item.get("management_subject", ""),
                    managed_object=item.get("managed_object", ""),
                    project_carrier_role=item.get("project_carrier_role", ""),
                )
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="artifacts/backend/backend_business_fact_model_audit.json")
    parser.add_argument("--markdown", default="artifacts/backend/backend_business_fact_model_audit.md")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY.relative_to(ROOT)))
    parser.add_argument("--problem-map", default=str(DEFAULT_PROBLEM_MAP.relative_to(ROOT)))
    parser.add_argument("--responsibility-matrix", default=str(DEFAULT_RESPONSIBILITY_MATRIX.relative_to(ROOT)))
    parser.add_argument("--object-hierarchy", default=str(DEFAULT_OBJECT_HIERARCHY.relative_to(ROOT)))
    parser.add_argument("--family-registry", default=str(DEFAULT_FAMILY_REGISTRY.relative_to(ROOT)))
    parser.add_argument("--ownership-specs", default=str(DEFAULT_OWNERSHIP_SPECS.relative_to(ROOT)))
    parser.add_argument("--audit-findings", default=str(DEFAULT_AUDIT_FINDINGS.relative_to(ROOT)))
    parser.add_argument("--overlap-analysis", default=str(DEFAULT_OVERLAP_ANALYSIS.relative_to(ROOT)))
    parser.add_argument("--projection-registry", default=str(DEFAULT_PROJECTION_REGISTRY.relative_to(ROOT)))
    parser.add_argument("--management-hierarchy", default=str(DEFAULT_MANAGEMENT_HIERARCHY.relative_to(ROOT)))
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Fail when formal models are unregistered, registered paths are missing, or standard gaps are undeclared.",
    )
    args = parser.parse_args()

    rows = extract_models()
    registry = load_registry(ROOT / args.registry)
    family_registry = load_family_registry(ROOT / args.family_registry)
    ownership_specs = load_ownership_specs(ROOT / args.ownership_specs)
    projection_registry = load_projection_registry(ROOT / args.projection_registry)
    management_hierarchy = load_management_hierarchy(ROOT / args.management_hierarchy)
    report = {
        "summary": summarize(rows, registry),
        "family_summary": summarize_family_registry(rows, family_registry),
        "ownership_summary": summarize_ownership_specs(rows, ownership_specs),
        "projection_summary": summarize_projection_registry(rows, projection_registry),
        "management_hierarchy_summary": summarize_management_hierarchy(family_registry, management_hierarchy),
        "registry": registry,
        "family_registry": family_registry,
        "ownership_specs": ownership_specs,
        "projection_registry": projection_registry,
        "management_hierarchy": management_hierarchy,
        "models": rows,
    }
    report_path = ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, ROOT / args.markdown)
    summary = report["summary"]
    print("BACKEND_BUSINESS_FACT_MODEL_AUDIT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
    print(
        "BACKEND_BUSINESS_MODEL_FAMILY_REGISTRY="
        + json.dumps(report["family_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "BACKEND_BUSINESS_MODEL_OWNERSHIP_SPECS="
        + json.dumps(report["ownership_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "BACKEND_BUSINESS_PROJECTION_REGISTRY="
        + json.dumps(report["projection_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "BACKEND_BUSINESS_MANAGEMENT_HIERARCHY="
        + json.dumps(report["management_hierarchy_summary"], ensure_ascii=False, sort_keys=True)
    )
    if args.enforce:
        problem_map_path = ROOT / args.problem_map
        problem_map_text = problem_map_path.read_text(encoding="utf-8") if problem_map_path.exists() else ""
        responsibility_path = ROOT / args.responsibility_matrix
        responsibility_text = responsibility_path.read_text(encoding="utf-8") if responsibility_path.exists() else ""
        hierarchy_path = ROOT / args.object_hierarchy
        hierarchy_text = hierarchy_path.read_text(encoding="utf-8") if hierarchy_path.exists() else ""
        family_registry_path = ROOT / args.family_registry
        ownership_specs_path = ROOT / args.ownership_specs
        audit_findings_path = ROOT / args.audit_findings
        audit_findings_text = audit_findings_path.read_text(encoding="utf-8") if audit_findings_path.exists() else ""
        overlap_analysis_path = ROOT / args.overlap_analysis
        overlap_analysis_text = overlap_analysis_path.read_text(encoding="utf-8") if overlap_analysis_path.exists() else ""
        projection_registry_path = ROOT / args.projection_registry
        management_hierarchy_path = ROOT / args.management_hierarchy
        blockers = {
            "unregistered_formal_models": summary["unregistered_formal_models"],
            "unclassified_models": summary["unclassified_models"],
            "registered_models_not_detected": summary["registered_models_not_detected"],
            "undeclared_standard_gaps": summary["undeclared_standard_gaps"],
            "registry_path_gaps": summary["registry_path_gaps"],
            "registry_shape_gaps": summary["registry_shape_gaps"],
            "problem_map_gaps": []
            if problem_map_path.exists() and "## Boundary Conclusions" in problem_map_text
            else [{"path": str(problem_map_path.relative_to(ROOT)), "reason": "missing_problem_map_or_boundary_conclusions"}],
            "responsibility_matrix_gaps": []
            if responsibility_path.exists() and "## Fact Flow Matrix" in responsibility_text and "## Boundary Risks" in responsibility_text
            else [
                {
                    "path": str(responsibility_path.relative_to(ROOT)),
                    "reason": "missing_responsibility_matrix_fact_flow_or_boundary_risks",
                }
            ],
            "object_hierarchy_gaps": []
            if hierarchy_path.exists()
            and "company" in hierarchy_text
            and "income business" in hierarchy_text
            and "expense business" in hierarchy_text
            and "project" in hierarchy_text
            else [{"path": str(hierarchy_path.relative_to(ROOT)), "reason": "missing_company_business_income_expense_project_hierarchy"}],
            "family_registry_gaps": []
            if family_registry_path.exists()
            and not report["family_summary"]["family_registry_shape_gaps"]
            and not report["family_summary"]["family_registry_reference_gaps"]
            else [
                {
                    "path": str(family_registry_path.relative_to(ROOT)),
                    "shape_gaps": report["family_summary"]["family_registry_shape_gaps"],
                    "reference_gaps": report["family_summary"]["family_registry_reference_gaps"],
                }
            ],
            "ownership_spec_gaps": []
            if ownership_specs_path.exists()
            and not report["ownership_summary"]["ownership_spec_shape_gaps"]
            and not report["ownership_summary"]["ownership_spec_reference_gaps"]
            else [
                {
                    "path": str(ownership_specs_path.relative_to(ROOT)),
                    "shape_gaps": report["ownership_summary"]["ownership_spec_shape_gaps"],
                    "reference_gaps": report["ownership_summary"]["ownership_spec_reference_gaps"],
                }
            ],
            "audit_findings_gaps": []
            if audit_findings_path.exists()
            and "## Core Answer" in audit_findings_text
            and "## Final Verdict" in audit_findings_text
            and "company manages business" in audit_findings_text
            and "unclassified models: 0" in audit_findings_text
            else [{"path": str(audit_findings_path.relative_to(ROOT)), "reason": "missing_audit_findings_core_answer_or_final_verdict"}],
            "overlap_analysis_gaps": []
            if overlap_analysis_path.exists()
            and "## Contract Ownership" in overlap_analysis_text
            and "## Treasury Account Reconciliation Ledger" in overlap_analysis_text
            and "## Product Material Catalog" in overlap_analysis_text
            and "## Payment Request Execution" in overlap_analysis_text
            and "## Projection Refresh" in overlap_analysis_text
            and "controlled generated ledger" in overlap_analysis_text
            else [{"path": str(overlap_analysis_path.relative_to(ROOT)), "reason": "missing_overlap_family_analysis"}],
            "projection_registry_gaps": []
            if projection_registry_path.exists()
            and not report["projection_summary"]["unregistered_projection_models"]
            and not report["projection_summary"]["registered_projection_models_not_detected"]
            and not report["projection_summary"]["projection_registry_shape_gaps"]
            and not report["projection_summary"]["projection_registry_reference_gaps"]
            else [
                {
                    "path": str(projection_registry_path.relative_to(ROOT)),
                    "unregistered_projection_models": report["projection_summary"]["unregistered_projection_models"],
                    "registered_projection_models_not_detected": report["projection_summary"][
                        "registered_projection_models_not_detected"
                    ],
                    "shape_gaps": report["projection_summary"]["projection_registry_shape_gaps"],
                    "reference_gaps": report["projection_summary"]["projection_registry_reference_gaps"],
                }
            ],
            "management_hierarchy_gaps": []
            if management_hierarchy_path.exists()
            and not report["management_hierarchy_summary"]["hierarchy_families_missing"]
            and not report["management_hierarchy_summary"]["hierarchy_unknown_families"]
            and not report["management_hierarchy_summary"]["management_hierarchy_shape_gaps"]
            else [
                {
                    "path": str(management_hierarchy_path.relative_to(ROOT)),
                    "missing_families": report["management_hierarchy_summary"]["hierarchy_families_missing"],
                    "unknown_families": report["management_hierarchy_summary"]["hierarchy_unknown_families"],
                    "shape_gaps": report["management_hierarchy_summary"]["management_hierarchy_shape_gaps"],
                }
            ],
        }
        if any(blockers.values()):
            print("BACKEND_BUSINESS_FACT_MODEL_AUDIT_BLOCKERS=" + json.dumps(blockers, ensure_ascii=False, sort_keys=True))
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
