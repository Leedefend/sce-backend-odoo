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
SMART_CORE_MODEL_ROOT = ROOT / "addons" / "smart_core" / "models"

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
DEFAULT_UNIVERSAL_ABSTRACTION = ROOT / "docs" / "architecture" / "platform_universal_business_abstraction_v1.md"
DEFAULT_UNIVERSAL_REGISTRY = ROOT / "docs" / "architecture" / "platform_universal_business_abstraction_registry_v1.json"
DEFAULT_UNIVERSAL_ROLLOUT = ROOT / "docs" / "architecture" / "platform_universal_abstraction_rollout_v1.md"
DEFAULT_CARRIER_FIT_AUDIT = ROOT / "docs" / "architecture" / "platform_universal_carrier_fit_audit_v1.md"
DEFAULT_CARRIER_FIT_REGISTRY = ROOT / "docs" / "architecture" / "platform_universal_carrier_fit_registry_v1.json"
DEFAULT_SCOPE_DECISION_GATE = ROOT / "docs" / "architecture" / "platform_universal_scope_decision_gate_v1.json"
DEFAULT_OPTIONAL_SCOPE_METADATA = ROOT / "docs" / "architecture" / "platform_universal_optional_scope_metadata_v1.json"
DEFAULT_PLATFORM_CORE_KERNEL_GAP = ROOT / "docs" / "architecture" / "platform_core_business_kernel_gap_v1.json"
PLATFORM_SCOPE_FIELD_NAMES = [
    "business_scope_key",
    "business_direction",
    "carrier_type",
    "carrier_model",
    "carrier_res_id",
]
PLATFORM_COMPANY_ACCESS_MODELS = {
    "sc.subscription.plan": ["code", "active", "feature_flags_json", "limits_json"],
    "sc.subscription": ["company_id", "plan_id", "state", "start_date", "end_date"],
    "sc.entitlement": ["company_id", "plan_id", "effective_flags_json", "effective_limits_json"],
    "sc.usage.counter": ["company_id", "key", "value"],
    "sc.ops.job": ["name", "job_type", "status"],
}
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
REQUIRED_UNIVERSAL_CONCEPTS = {"platform", "company", "business", "carrier", "fact", "projection"}
ALLOWED_UNIVERSAL_LAYERS = {"platform_kernel", "industry_binding", "customer_binding"}
ALLOWED_UNIVERSAL_CONCEPT_TYPES = {
    "management_subject",
    "managed_object",
    "extension_point",
    "event_or_state",
    "derived_visibility",
    "policy",
}
ALLOWED_UNIVERSAL_CARRIER_FITS = {
    "platform_company_level",
    "company_identity",
    "business_level_no_carrier",
    "pre_carrier_pre_project",
    "carrier_primary_project",
    "carrier_optional_project",
    "derived_projection",
    "legacy_evidence",
    "technical_bridge",
    "review_required",
}
ALLOWED_SCOPE_DECISIONS = {
    "registry_metadata_only",
    "optional_scope_fields",
    "projection_extension",
    "policy_scope_extension",
    "concrete_business_model",
    "concrete_carrier_model",
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


def call_kwargs(node: ast.AST) -> dict[str, Any]:
    if not isinstance(node, ast.Call):
        return {}
    return {kw.arg: literal(kw.value) for kw in node.keywords if kw.arg}


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
            fields: list[dict[str, Any]] = []
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
                    kwargs = call_kwargs(stmt.value)
                    fields.append(
                        {
                            "name": target.id,
                            "type": field_call.split(".", 1)[1],
                            "comodel": comodel,
                            "required": bool(kwargs.get("required")),
                            "readonly": bool(kwargs.get("readonly")),
                            "related": kwargs.get("related") or "",
                            "store": bool(kwargs.get("store")),
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
            carrier_fit = classify_universal_carrier_fit(path_text, model_name, inherit, fields, buckets, model_family)
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
                    "universal_carrier_fit": carrier_fit,
                    "standard_fields": {field: field in field_names for field in STANDARD_FIELDS},
                    "has_legacy_unique_constraint": "legacy_source_unique" in constraint_text
                    or "unique(legacy_source_model, legacy_record_id)" in constraint_text,
                    "has_legacy_confirmed_write_guard": "legacy_confirmed" in source
                    and "source_origin" in source
                    and "def write" in source,
                }
            )
    return rows


def extract_named_model(path: Path, target_model: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        model_name = None
        inherit = None
        description = None
        fields: list[dict[str, Any]] = []
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
                kwargs = call_kwargs(stmt.value)
                fields.append(
                    {
                        "name": target.id,
                        "type": field_call.split(".", 1)[1],
                        "comodel": comodel,
                        "required": bool(kwargs.get("required")),
                        "readonly": bool(kwargs.get("readonly")),
                        "related": kwargs.get("related") or "",
                        "store": bool(kwargs.get("store")),
                    }
                )
        if model_name == target_model:
            return {
                "path": str(path.relative_to(ROOT)),
                "class": node.name,
                "model": model_name,
                "inherit": inherit,
                "description": description,
                "fields": fields,
            }
    return None


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


def field_by_name(fields: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next((field for field in fields if field.get("name") == name), None)


def inherits_model(inherit: Any, model_name: str) -> bool:
    if isinstance(inherit, str):
        return inherit == model_name
    if isinstance(inherit, (list, tuple, set)):
        return model_name in inherit
    return False


def classify_universal_carrier_fit(
    path: str,
    model_name: str | None,
    inherit: Any,
    fields: list[dict[str, Any]],
    buckets: list[str],
    model_family: str,
) -> str:
    ref = model_ref(model_name, inherit)
    project_field = field_by_name(fields, "project_id") or {}
    has_project = bool(project_field)
    project_required = bool(project_field.get("required"))
    project_related = bool(project_field.get("related"))

    if "projection" in buckets:
        return "derived_projection"
    if "legacy_fact" in buckets or ref.startswith("sc.legacy") or ref == "sc.history.todo":
        return "legacy_evidence"
    if model_family == "compatibility bridges and native extensions":
        return "technical_bridge"
    if model_family in {
        "company and business governance",
        "workflow approval dictionary audit and validation",
        "scene capability subscription and frontend contract runtime",
    }:
        return "platform_company_level"
    if model_family in {"partner and counterparty identity", "product and material identity"}:
        return "company_identity"
    if model_family == "income contract and tender business" and ref.startswith("tender."):
        return "pre_carrier_pre_project" if not project_required or project_related else "business_level_no_carrier"
    if model_family == "treasury account reconciliation and ledger" and ref == "sc.fund.account":
        return "carrier_optional_project"
    if model_family == "document admin payroll and office operations" and (not has_project or not project_required):
        return "carrier_optional_project"
    if has_project and project_required:
        return "carrier_primary_project"
    if has_project:
        return "carrier_optional_project"
    if model_family in {
        "income contract and tender business",
        "expense contract and procurement commitment",
        "payment request and payment execution",
        "receipt income invoice and tax realization",
        "project budget BOQ and cost control",
        "material lifecycle",
        "labor equipment and subcontract lifecycle",
        "progress quality safety risk and diary",
    }:
        return "carrier_primary_project"
    if model_family == "project identity and execution carrier":
        return "carrier_primary_project"
    return "review_required"


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


def load_universal_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"concepts": [], "carrier_bindings": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_carrier_fit_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"family_carrier_fits": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_scope_decision_gate(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"decision_gates": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_scope_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"model_scope_metadata": [], "missing_registry": True}
    return json.loads(path.read_text(encoding="utf-8"))


def load_platform_core_kernel_gap(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"minimum_kernel_artifacts": [], "missing_registry": True}
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
    carrier_fit_counts = Counter(row.get("universal_carrier_fit") or "review_required" for row in rows)
    carrier_fit_unclassified = [
        {"model": row.get("model"), "inherit": row.get("inherit"), "path": row["path"]}
        for row in rows
        if row.get("universal_carrier_fit") not in ALLOWED_UNIVERSAL_CARRIER_FITS
    ]
    project_required_rows = []
    project_optional_rows = []
    carrier_fit_review_rows = []
    for row in rows:
        project_field = field_by_name(row.get("fields", []), "project_id")
        if project_field and project_field.get("required"):
            project_required_rows.append({"model": row.get("model"), "inherit": row.get("inherit"), "path": row["path"]})
        elif project_field:
            project_optional_rows.append({"model": row.get("model"), "inherit": row.get("inherit"), "path": row["path"]})
        if row.get("universal_carrier_fit") == "review_required":
            carrier_fit_review_rows.append(
                {
                    "model": row.get("model"),
                    "inherit": row.get("inherit"),
                    "model_family": row.get("model_family"),
                    "path": row["path"],
                }
            )
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
        "universal_carrier_fit_counts": dict(sorted(carrier_fit_counts.items())),
        "universal_carrier_fit_unclassified_count": len(carrier_fit_unclassified),
        "universal_carrier_fit_unclassified": carrier_fit_unclassified,
        "project_required_model_count": len(project_required_rows),
        "project_optional_model_count": len(project_optional_rows),
        "universal_carrier_fit_review_count": len(carrier_fit_review_rows),
        "universal_carrier_fit_review_models": carrier_fit_review_rows,
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


def summarize_universal_registry(universal_registry: dict[str, Any]) -> dict[str, Any]:
    concepts = universal_registry.get("concepts", [])
    bindings = universal_registry.get("carrier_bindings", [])
    concept_map = {item.get("key"): item for item in concepts if item.get("key")}
    required_fields = ["key", "name", "concept_type", "layer", "definition", "platform_contract", "current_construction_binding"]
    concept_shape_gaps = []
    layer_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    for item in concepts:
        key = item.get("key")
        for field in required_fields:
            if not str(item.get(field) or "").strip():
                concept_shape_gaps.append({"key": key, "field": field, "reason": "missing_required_field"})
        layer = item.get("layer")
        if layer in ALLOWED_UNIVERSAL_LAYERS:
            layer_counts[layer] += 1
        else:
            concept_shape_gaps.append(
                {
                    "key": key,
                    "field": "layer",
                    "value": layer,
                    "allowed_values": sorted(ALLOWED_UNIVERSAL_LAYERS),
                }
            )
        concept_type = item.get("concept_type")
        if concept_type in ALLOWED_UNIVERSAL_CONCEPT_TYPES:
            type_counts[concept_type] += 1
        else:
            concept_shape_gaps.append(
                {
                    "key": key,
                    "field": "concept_type",
                    "value": concept_type,
                    "allowed_values": sorted(ALLOWED_UNIVERSAL_CONCEPT_TYPES),
                }
            )
    binding_shape_gaps = []
    for item in bindings:
        key = item.get("key")
        for field in ("key", "industry", "carrier_type", "model", "business_binding", "platform_boundary"):
            if not str(item.get(field) or "").strip():
                binding_shape_gaps.append({"key": key, "field": field, "reason": "missing_required_field"})
    return {
        "universal_concept_count": len(concepts),
        "universal_concept_layer_counts": dict(sorted(layer_counts.items())),
        "universal_concept_type_counts": dict(sorted(type_counts.items())),
        "missing_required_universal_concepts": sorted(REQUIRED_UNIVERSAL_CONCEPTS - set(concept_map)),
        "universal_concept_shape_gap_count": len(concept_shape_gaps),
        "universal_concept_shape_gaps": concept_shape_gaps,
        "carrier_binding_count": len(bindings),
        "carrier_binding_shape_gap_count": len(binding_shape_gaps),
        "carrier_binding_shape_gaps": binding_shape_gaps,
        "has_construction_project_binding": any(
            item.get("industry") == "construction"
            and item.get("carrier_type") == "project"
            and item.get("model") == "project.project"
            for item in bindings
        ),
    }


def summarize_carrier_fit_registry(
    family_registry: dict[str, Any], carrier_fit_registry: dict[str, Any]
) -> dict[str, Any]:
    family_names = {item.get("family") for item in family_registry.get("families", []) if item.get("family")}
    fit_rows = carrier_fit_registry.get("family_carrier_fits", [])
    fit_map = {item.get("family"): item for item in fit_rows if item.get("family")}
    required_fields = [
        "family",
        "carrier_fit",
        "current_binding",
        "future_platform_pressure",
        "decision",
        "next_action",
    ]
    shape_gaps = []
    fit_counts: Counter[str] = Counter()
    pressure_counts: Counter[str] = Counter()
    for item in fit_rows:
        family = item.get("family")
        for field in required_fields:
            if not str(item.get(field) or "").strip():
                shape_gaps.append({"family": family, "field": field, "reason": "missing_required_field"})
        carrier_fit = item.get("carrier_fit")
        if carrier_fit in ALLOWED_UNIVERSAL_CARRIER_FITS:
            fit_counts[carrier_fit] += 1
        else:
            shape_gaps.append(
                {
                    "family": family,
                    "field": "carrier_fit",
                    "value": carrier_fit,
                    "allowed_values": sorted(ALLOWED_UNIVERSAL_CARRIER_FITS),
                }
            )
        pressure_counts[str(item.get("future_platform_pressure") or "missing")] += 1
        pressure_models = item.get("representative_pressure_models", [])
        if not isinstance(pressure_models, list):
            shape_gaps.append({"family": family, "field": "representative_pressure_models", "reason": "must_be_list"})
    return {
        "carrier_fit_registry_count": len(fit_rows),
        "carrier_fit_family_counts": dict(sorted(fit_counts.items())),
        "future_platform_pressure_counts": dict(sorted(pressure_counts.items())),
        "carrier_fit_registry_families_missing": sorted(family_names - set(fit_map)),
        "carrier_fit_registry_unknown_families": sorted(set(fit_map) - family_names),
        "carrier_fit_registry_shape_gap_count": len(shape_gaps),
        "carrier_fit_registry_shape_gaps": shape_gaps,
    }


def summarize_scope_decision_gate(scope_decision_gate: dict[str, Any]) -> dict[str, Any]:
    gate_rows = scope_decision_gate.get("decision_gates", [])
    required_fields = [
        "decision",
        "when_to_use",
        "allowed_changes",
        "forbidden_changes",
        "required_evidence",
        "verification_gate",
    ]
    shape_gaps = []
    decision_counts: Counter[str] = Counter()
    for item in gate_rows:
        decision = item.get("decision")
        if decision in ALLOWED_SCOPE_DECISIONS:
            decision_counts[decision] += 1
        else:
            shape_gaps.append(
                {
                    "decision": decision,
                    "field": "decision",
                    "value": decision,
                    "allowed_values": sorted(ALLOWED_SCOPE_DECISIONS),
                }
            )
        for field in required_fields:
            value = item.get(field)
            if isinstance(value, list):
                if not value:
                    shape_gaps.append({"decision": decision, "field": field, "reason": "missing_required_list"})
            elif not str(value or "").strip():
                shape_gaps.append({"decision": decision, "field": field, "reason": "missing_required_field"})
    return {
        "scope_decision_gate_count": len(gate_rows),
        "scope_decision_counts": dict(sorted(decision_counts.items())),
        "missing_scope_decisions": sorted(ALLOWED_SCOPE_DECISIONS - set(decision_counts)),
        "scope_decision_gate_shape_gap_count": len(shape_gaps),
        "scope_decision_gate_shape_gaps": shape_gaps,
    }


def summarize_platform_core_kernel_gap(platform_core_kernel_gap: dict[str, Any]) -> dict[str, Any]:
    mixin_row = extract_named_model(SMART_CORE_MODEL_ROOT / "business_scope.py", "sc.business.scope.mixin")
    company_access_rows = {
        model: extract_named_model(SMART_CORE_MODEL_ROOT / "subscription.py", model)
        for model in PLATFORM_COMPANY_ACCESS_MODELS
    }
    artifact_rows = platform_core_kernel_gap.get("minimum_kernel_artifacts", [])
    required_artifact_keys = {"platform_business_scope_mixin", "platform_company_access_models"}
    artifact_keys = {item.get("artifact_key") for item in artifact_rows}
    shape_gaps = []
    if "platform_business_scope_mixin" not in artifact_keys:
        shape_gaps.append(
            {
                "artifact_key": "platform_business_scope_mixin",
                "reason": "missing_minimum_kernel_artifact_registry",
            }
        )
    if "platform_company_access_models" not in artifact_keys:
        shape_gaps.append(
            {
                "artifact_key": "platform_company_access_models",
                "reason": "missing_minimum_kernel_artifact_registry",
            }
        )
    if not mixin_row:
        shape_gaps.append(
            {
                "artifact_key": "platform_business_scope_mixin",
                "model": "sc.business.scope.mixin",
                "reason": "mixin_model_not_detected",
            }
        )
        mixin_fields = []
    else:
        mixin_fields = mixin_row.get("fields", [])
    for field_name in PLATFORM_SCOPE_FIELD_NAMES:
        field = field_by_name(mixin_fields, field_name)
        if not field:
            shape_gaps.append(
                {
                    "artifact_key": "platform_business_scope_mixin",
                    "field": field_name,
                    "reason": "required_platform_scope_field_missing",
                }
            )
            continue
        if field.get("required"):
            shape_gaps.append(
                {
                    "artifact_key": "platform_business_scope_mixin",
                    "field": field_name,
                    "reason": "platform_scope_field_must_remain_optional",
                }
            )
    for model_name, required_fields in PLATFORM_COMPANY_ACCESS_MODELS.items():
        model_row = company_access_rows.get(model_name)
        if not model_row:
            shape_gaps.append(
                {
                    "artifact_key": "platform_company_access_models",
                    "model": model_name,
                    "reason": "company_access_model_not_detected_in_smart_core",
                }
            )
            continue
        for field_name in required_fields:
            if not field_by_name(model_row.get("fields", []), field_name):
                shape_gaps.append(
                    {
                        "artifact_key": "platform_company_access_models",
                        "model": model_name,
                        "field": field_name,
                        "reason": "required_company_access_field_missing",
                    }
                )
    return {
        "minimum_kernel_artifact_count": len(artifact_rows),
        "has_platform_business_scope_mixin": bool(mixin_row),
        "platform_scope_field_count": len([field for field in mixin_fields if field.get("name") in PLATFORM_SCOPE_FIELD_NAMES]),
        "platform_scope_fields": [field.get("name") for field in mixin_fields if field.get("name") in PLATFORM_SCOPE_FIELD_NAMES],
        "company_access_model_count": len([row for row in company_access_rows.values() if row]),
        "company_access_models": sorted(model for model, row in company_access_rows.items() if row),
        "missing_required_artifact_keys": sorted(required_artifact_keys - artifact_keys),
        "platform_core_kernel_shape_gap_count": len(shape_gaps),
        "platform_core_kernel_shape_gaps": shape_gaps,
        "scope_mixin_fields": mixin_fields,
    }


def inherited_optional_scope_field(
    model_row: dict[str, Any] | None, field_name: str, platform_core_summary: dict[str, Any]
) -> dict[str, Any] | None:
    if not model_row:
        return None
    direct_field = field_by_name(model_row.get("fields", []), field_name)
    if direct_field:
        return direct_field
    if not inherits_model(model_row.get("inherit"), "sc.business.scope.mixin"):
        return None
    return field_by_name(platform_core_summary.get("scope_mixin_fields", []), field_name)


def summarize_optional_scope_metadata(
    rows: list[dict[str, Any]],
    family_registry: dict[str, Any],
    optional_scope_metadata: dict[str, Any],
    platform_core_summary: dict[str, Any],
) -> dict[str, Any]:
    detected_models = {row["model"] for row in rows if row.get("model")}
    family_names = {item.get("family") for item in family_registry.get("families", []) if item.get("family")}
    metadata_rows = optional_scope_metadata.get("model_scope_metadata", [])
    required_fields = [
        "target_model",
        "family",
        "decision",
        "current_required_binding",
        "proposed_optional_fields",
        "compatibility_rule",
        "migration_policy",
        "acceptance_probe",
    ]
    required_optional_field_keys = {"name", "type", "required", "purpose"}
    shape_gaps = []
    reference_gaps = []
    decision_counts: Counter[str] = Counter()
    for item in metadata_rows:
        target_model = item.get("target_model")
        family = item.get("family")
        model_row = next((row for row in rows if row.get("model") == target_model), None)
        for field in required_fields:
            value = item.get(field)
            if isinstance(value, list):
                if not value:
                    shape_gaps.append({"target_model": target_model, "field": field, "reason": "missing_required_list"})
            elif not str(value or "").strip():
                shape_gaps.append({"target_model": target_model, "field": field, "reason": "missing_required_field"})
        if target_model not in detected_models:
            reference_gaps.append({"target_model": target_model, "field": "target_model", "reason": "model_not_detected"})
        if family not in family_names:
            reference_gaps.append({"target_model": target_model, "field": "family", "family": family})
        decision = item.get("decision")
        if decision == "optional_scope_fields":
            decision_counts[decision] += 1
        else:
            shape_gaps.append(
                {
                    "target_model": target_model,
                    "field": "decision",
                    "value": decision,
                    "allowed_values": ["optional_scope_fields"],
                }
            )
        for proposed_field in item.get("proposed_optional_fields", []):
            missing_keys = sorted(required_optional_field_keys - set(proposed_field))
            if missing_keys:
                shape_gaps.append(
                    {
                        "target_model": target_model,
                        "field": "proposed_optional_fields",
                        "reason": "missing_field_keys",
                        "missing_keys": missing_keys,
                    }
                )
            if proposed_field.get("required") is not False:
                shape_gaps.append(
                    {
                        "target_model": target_model,
                        "field": proposed_field.get("name"),
                        "reason": "optional_scope_field_must_be_required_false",
                    }
                )
            actual_field = inherited_optional_scope_field(model_row, proposed_field.get("name"), platform_core_summary)
            if not actual_field:
                shape_gaps.append(
                    {
                        "target_model": target_model,
                        "field": proposed_field.get("name"),
                        "reason": "proposed_optional_scope_field_not_implemented",
                    }
                )
                continue
            if actual_field.get("type") != proposed_field.get("type"):
                shape_gaps.append(
                    {
                        "target_model": target_model,
                        "field": proposed_field.get("name"),
                        "reason": "implemented_field_type_mismatch",
                        "expected": proposed_field.get("type"),
                        "actual": actual_field.get("type"),
                    }
                )
            if actual_field.get("required"):
                shape_gaps.append(
                    {
                        "target_model": target_model,
                        "field": proposed_field.get("name"),
                        "reason": "implemented_optional_scope_field_is_required",
                    }
                )
    return {
        "optional_scope_metadata_count": len(metadata_rows),
        "optional_scope_decision_counts": dict(sorted(decision_counts.items())),
        "optional_scope_metadata_shape_gap_count": len(shape_gaps),
        "optional_scope_metadata_shape_gaps": shape_gaps,
        "optional_scope_metadata_reference_gap_count": len(reference_gaps),
        "optional_scope_metadata_reference_gaps": reference_gaps,
        "has_tender_bid_optional_scope_metadata": any(
            item.get("target_model") == "tender.bid" and item.get("decision") == "optional_scope_fields"
            for item in metadata_rows
        ),
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
        f"- universal_carrier_fit_unclassified_count: {summary['universal_carrier_fit_unclassified_count']}",
        f"- universal_carrier_fit_review_count: {summary['universal_carrier_fit_review_count']}",
        f"- project_required_model_count: {summary['project_required_model_count']}",
        f"- project_optional_model_count: {summary['project_optional_model_count']}",
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
    lines.extend(["", "## Universal Carrier Fit", ""])
    for key, value in summary["universal_carrier_fit_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Universal Carrier Fit Review Models", ""])
    if summary["universal_carrier_fit_review_models"]:
        lines.append("| model | inherit | family | path |")
        lines.append("| --- | --- | --- | --- |")
        for row in summary["universal_carrier_fit_review_models"]:
            lines.append(
                f"| {row.get('model') or ''} | {row.get('inherit') or ''} | {row.get('model_family') or ''} | {row['path']} |"
            )
    else:
        lines.append("- none")
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
    universal_summary = report.get("universal_summary") or {}
    universal_registry = report.get("universal_registry") or {}
    lines.extend(["", "## Universal Abstraction Registry", ""])
    lines.append(f"- universal_concept_count: {universal_summary.get('universal_concept_count', 0)}")
    lines.append(
        "- universal_concept_layer_counts: "
        + json.dumps(universal_summary.get("universal_concept_layer_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(f"- carrier_binding_count: {universal_summary.get('carrier_binding_count', 0)}")
    lines.append(f"- has_construction_project_binding: {universal_summary.get('has_construction_project_binding', False)}")
    if universal_registry.get("concepts"):
        lines.extend(["", "| concept | type | layer | construction binding |"])
        lines.append("| --- | --- | --- | --- |")
        for item in universal_registry["concepts"]:
            lines.append(
                "| {key} | {concept_type} | {layer} | {current_construction_binding} |".format(
                    key=item.get("key", ""),
                    concept_type=item.get("concept_type", ""),
                    layer=item.get("layer", ""),
                    current_construction_binding=item.get("current_construction_binding", ""),
                )
            )
    platform_core_summary = report.get("platform_core_summary") or {}
    lines.extend(["", "## Platform Core Kernel Gap", ""])
    lines.append(
        f"- minimum_kernel_artifact_count: {platform_core_summary.get('minimum_kernel_artifact_count', 0)}"
    )
    lines.append(
        f"- has_platform_business_scope_mixin: {platform_core_summary.get('has_platform_business_scope_mixin', False)}"
    )
    lines.append(f"- platform_scope_field_count: {platform_core_summary.get('platform_scope_field_count', 0)}")
    lines.append(
        "- platform_scope_fields: "
        + (", ".join(platform_core_summary.get("platform_scope_fields", [])) or "none")
    )
    lines.append(f"- company_access_model_count: {platform_core_summary.get('company_access_model_count', 0)}")
    lines.append(
        "- company_access_models: "
        + (", ".join(platform_core_summary.get("company_access_models", [])) or "none")
    )
    lines.append(
        "- missing_required_artifact_keys: "
        + (", ".join(platform_core_summary.get("missing_required_artifact_keys", [])) or "none")
    )
    carrier_fit_registry_summary = report.get("carrier_fit_registry_summary") or {}
    carrier_fit_registry = report.get("carrier_fit_registry") or {}
    lines.extend(["", "## Carrier Fit Registry", ""])
    lines.append(
        f"- carrier_fit_registry_count: {carrier_fit_registry_summary.get('carrier_fit_registry_count', 0)}"
    )
    lines.append(
        "- carrier_fit_family_counts: "
        + json.dumps(
            carrier_fit_registry_summary.get("carrier_fit_family_counts", {}),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    lines.append(
        "- future_platform_pressure_counts: "
        + json.dumps(
            carrier_fit_registry_summary.get("future_platform_pressure_counts", {}),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if carrier_fit_registry.get("family_carrier_fits"):
        lines.extend(["", "| family | carrier fit | pressure | decision |"])
        lines.append("| --- | --- | --- | --- |")
        for item in carrier_fit_registry["family_carrier_fits"]:
            lines.append(
                "| {family} | {carrier_fit} | {future_platform_pressure} | {decision} |".format(
                    family=item.get("family", ""),
                    carrier_fit=item.get("carrier_fit", ""),
                    future_platform_pressure=item.get("future_platform_pressure", ""),
                    decision=item.get("decision", ""),
                )
            )
    scope_decision_summary = report.get("scope_decision_summary") or {}
    scope_decision_gate = report.get("scope_decision_gate") or {}
    lines.extend(["", "## Scope Decision Gate", ""])
    lines.append(f"- scope_decision_gate_count: {scope_decision_summary.get('scope_decision_gate_count', 0)}")
    lines.append(
        "- scope_decision_counts: "
        + json.dumps(scope_decision_summary.get("scope_decision_counts", {}), ensure_ascii=False, sort_keys=True)
    )
    lines.append(
        "- missing_scope_decisions: "
        + (", ".join(scope_decision_summary.get("missing_scope_decisions", [])) or "none")
    )
    if scope_decision_gate.get("decision_gates"):
        lines.extend(["", "| decision | when to use | verification |"])
        lines.append("| --- | --- | --- |")
        for item in scope_decision_gate["decision_gates"]:
            lines.append(
                "| {decision} | {when_to_use} | {verification_gate} |".format(
                    decision=item.get("decision", ""),
                    when_to_use=item.get("when_to_use", ""),
                    verification_gate=item.get("verification_gate", ""),
                )
            )
    optional_scope_summary = report.get("optional_scope_summary") or {}
    optional_scope_metadata = report.get("optional_scope_metadata") or {}
    lines.extend(["", "## Optional Scope Metadata", ""])
    lines.append(
        f"- optional_scope_metadata_count: {optional_scope_summary.get('optional_scope_metadata_count', 0)}"
    )
    lines.append(
        f"- has_tender_bid_optional_scope_metadata: {optional_scope_summary.get('has_tender_bid_optional_scope_metadata', False)}"
    )
    if optional_scope_metadata.get("model_scope_metadata"):
        lines.extend(["", "| target model | family | decision | acceptance |"])
        lines.append("| --- | --- | --- | --- |")
        for item in optional_scope_metadata["model_scope_metadata"]:
            lines.append(
                "| {target_model} | {family} | {decision} | {acceptance_probe} |".format(
                    target_model=item.get("target_model", ""),
                    family=item.get("family", ""),
                    decision=item.get("decision", ""),
                    acceptance_probe=item.get("acceptance_probe", ""),
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
    parser.add_argument("--universal-abstraction", default=str(DEFAULT_UNIVERSAL_ABSTRACTION.relative_to(ROOT)))
    parser.add_argument("--universal-registry", default=str(DEFAULT_UNIVERSAL_REGISTRY.relative_to(ROOT)))
    parser.add_argument("--universal-rollout", default=str(DEFAULT_UNIVERSAL_ROLLOUT.relative_to(ROOT)))
    parser.add_argument("--carrier-fit-audit", default=str(DEFAULT_CARRIER_FIT_AUDIT.relative_to(ROOT)))
    parser.add_argument("--carrier-fit-registry", default=str(DEFAULT_CARRIER_FIT_REGISTRY.relative_to(ROOT)))
    parser.add_argument("--scope-decision-gate", default=str(DEFAULT_SCOPE_DECISION_GATE.relative_to(ROOT)))
    parser.add_argument("--optional-scope-metadata", default=str(DEFAULT_OPTIONAL_SCOPE_METADATA.relative_to(ROOT)))
    parser.add_argument("--platform-core-kernel-gap", default=str(DEFAULT_PLATFORM_CORE_KERNEL_GAP.relative_to(ROOT)))
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
    universal_registry = load_universal_registry(ROOT / args.universal_registry)
    carrier_fit_registry = load_carrier_fit_registry(ROOT / args.carrier_fit_registry)
    scope_decision_gate = load_scope_decision_gate(ROOT / args.scope_decision_gate)
    optional_scope_metadata = load_optional_scope_metadata(ROOT / args.optional_scope_metadata)
    platform_core_kernel_gap = load_platform_core_kernel_gap(ROOT / args.platform_core_kernel_gap)
    platform_core_summary = summarize_platform_core_kernel_gap(platform_core_kernel_gap)
    report = {
        "summary": summarize(rows, registry),
        "family_summary": summarize_family_registry(rows, family_registry),
        "ownership_summary": summarize_ownership_specs(rows, ownership_specs),
        "projection_summary": summarize_projection_registry(rows, projection_registry),
        "management_hierarchy_summary": summarize_management_hierarchy(family_registry, management_hierarchy),
        "universal_summary": summarize_universal_registry(universal_registry),
        "platform_core_summary": platform_core_summary,
        "carrier_fit_registry_summary": summarize_carrier_fit_registry(family_registry, carrier_fit_registry),
        "scope_decision_summary": summarize_scope_decision_gate(scope_decision_gate),
        "optional_scope_summary": summarize_optional_scope_metadata(
            rows, family_registry, optional_scope_metadata, platform_core_summary
        ),
        "registry": registry,
        "family_registry": family_registry,
        "ownership_specs": ownership_specs,
        "projection_registry": projection_registry,
        "management_hierarchy": management_hierarchy,
        "universal_registry": universal_registry,
        "platform_core_kernel_gap": platform_core_kernel_gap,
        "carrier_fit_registry": carrier_fit_registry,
        "scope_decision_gate": scope_decision_gate,
        "optional_scope_metadata": optional_scope_metadata,
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
    print(
        "PLATFORM_UNIVERSAL_BUSINESS_ABSTRACTION="
        + json.dumps(report["universal_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "PLATFORM_CORE_BUSINESS_KERNEL_GAP="
        + json.dumps(report["platform_core_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "PLATFORM_UNIVERSAL_CARRIER_FIT_REGISTRY="
        + json.dumps(report["carrier_fit_registry_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "PLATFORM_UNIVERSAL_SCOPE_DECISION_GATE="
        + json.dumps(report["scope_decision_summary"], ensure_ascii=False, sort_keys=True)
    )
    print(
        "PLATFORM_UNIVERSAL_OPTIONAL_SCOPE_METADATA="
        + json.dumps(report["optional_scope_summary"], ensure_ascii=False, sort_keys=True)
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
        universal_abstraction_path = ROOT / args.universal_abstraction
        universal_abstraction_text = (
            universal_abstraction_path.read_text(encoding="utf-8") if universal_abstraction_path.exists() else ""
        )
        universal_registry_path = ROOT / args.universal_registry
        universal_rollout_path = ROOT / args.universal_rollout
        universal_rollout_text = universal_rollout_path.read_text(encoding="utf-8") if universal_rollout_path.exists() else ""
        carrier_fit_audit_path = ROOT / args.carrier_fit_audit
        carrier_fit_audit_text = carrier_fit_audit_path.read_text(encoding="utf-8") if carrier_fit_audit_path.exists() else ""
        carrier_fit_registry_path = ROOT / args.carrier_fit_registry
        scope_decision_gate_path = ROOT / args.scope_decision_gate
        optional_scope_metadata_path = ROOT / args.optional_scope_metadata
        platform_core_kernel_gap_path = ROOT / args.platform_core_kernel_gap
        blockers = {
            "unregistered_formal_models": summary["unregistered_formal_models"],
            "unclassified_models": summary["unclassified_models"],
            "universal_carrier_fit_unclassified": summary["universal_carrier_fit_unclassified"],
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
            "universal_abstraction_gaps": []
            if universal_abstraction_path.exists()
            and "platform -> company -> business -> carrier -> fact -> projection" in universal_abstraction_text
            and "Project Is Not Platform Kernel" in universal_abstraction_text
            and "Industry Carrier" in universal_abstraction_text
            and "Construction Binding" in universal_abstraction_text
            else [
                {
                    "path": str(universal_abstraction_path.relative_to(ROOT)),
                    "reason": "missing_platform_universal_abstraction_or_project_boundary",
                }
            ],
            "universal_registry_gaps": []
            if universal_registry_path.exists()
            and not report["universal_summary"]["missing_required_universal_concepts"]
            and not report["universal_summary"]["universal_concept_shape_gaps"]
            and not report["universal_summary"]["carrier_binding_shape_gaps"]
            and report["universal_summary"]["has_construction_project_binding"]
            else [
                {
                    "path": str(universal_registry_path.relative_to(ROOT)),
                    "missing_required_universal_concepts": report["universal_summary"][
                        "missing_required_universal_concepts"
                    ],
                    "concept_shape_gaps": report["universal_summary"]["universal_concept_shape_gaps"],
                    "carrier_binding_shape_gaps": report["universal_summary"]["carrier_binding_shape_gaps"],
                    "has_construction_project_binding": report["universal_summary"]["has_construction_project_binding"],
                }
            ],
            "platform_core_kernel_gaps": []
            if platform_core_kernel_gap_path.exists()
            and report["platform_core_summary"]["has_platform_business_scope_mixin"]
            and report["platform_core_summary"]["platform_scope_field_count"] == len(PLATFORM_SCOPE_FIELD_NAMES)
            and report["platform_core_summary"]["company_access_model_count"] == len(PLATFORM_COMPANY_ACCESS_MODELS)
            and not report["platform_core_summary"]["missing_required_artifact_keys"]
            and not report["platform_core_summary"]["platform_core_kernel_shape_gaps"]
            else [
                {
                    "path": str(platform_core_kernel_gap_path.relative_to(ROOT)),
                    "has_platform_business_scope_mixin": report["platform_core_summary"][
                        "has_platform_business_scope_mixin"
                    ],
                    "platform_scope_fields": report["platform_core_summary"]["platform_scope_fields"],
                    "company_access_models": report["platform_core_summary"]["company_access_models"],
                    "missing_required_artifact_keys": report["platform_core_summary"][
                        "missing_required_artifact_keys"
                    ],
                    "shape_gaps": report["platform_core_summary"]["platform_core_kernel_shape_gaps"],
                }
            ],
            "universal_rollout_gaps": []
            if universal_rollout_path.exists()
            and "Do not add `sc.business` or `sc.business.carrier` immediately." in universal_rollout_text
            and "classify current backend models by universal carrier fit" in universal_rollout_text
            and "Decision Gate" in universal_rollout_text
            else [
                {
                    "path": str(universal_rollout_path.relative_to(ROOT)),
                    "reason": "missing_universal_rollout_or_decision_gate",
                }
            ],
            "carrier_fit_audit_gaps": []
            if carrier_fit_audit_path.exists()
            and "## Carrier Fit Counts" in carrier_fit_audit_text
            and "## Decision" in carrier_fit_audit_text
            and "Do not introduce `sc.business` or `sc.business.carrier` as tables yet." in carrier_fit_audit_text
            and "project_required_model_count" in carrier_fit_audit_text
            else [
                {
                    "path": str(carrier_fit_audit_path.relative_to(ROOT)),
                    "reason": "missing_carrier_fit_audit_or_decision",
                }
            ],
            "carrier_fit_registry_gaps": []
            if carrier_fit_registry_path.exists()
            and not report["carrier_fit_registry_summary"]["carrier_fit_registry_families_missing"]
            and not report["carrier_fit_registry_summary"]["carrier_fit_registry_unknown_families"]
            and not report["carrier_fit_registry_summary"]["carrier_fit_registry_shape_gaps"]
            and report["carrier_fit_registry_summary"]["future_platform_pressure_counts"].get("high", 0) >= 1
            else [
                {
                    "path": str(carrier_fit_registry_path.relative_to(ROOT)),
                    "missing_families": report["carrier_fit_registry_summary"][
                        "carrier_fit_registry_families_missing"
                    ],
                    "unknown_families": report["carrier_fit_registry_summary"][
                        "carrier_fit_registry_unknown_families"
                    ],
                    "shape_gaps": report["carrier_fit_registry_summary"]["carrier_fit_registry_shape_gaps"],
                    "future_platform_pressure_counts": report["carrier_fit_registry_summary"][
                        "future_platform_pressure_counts"
                    ],
                }
            ],
            "scope_decision_gate_gaps": []
            if scope_decision_gate_path.exists()
            and not report["scope_decision_summary"]["missing_scope_decisions"]
            and not report["scope_decision_summary"]["scope_decision_gate_shape_gaps"]
            else [
                {
                    "path": str(scope_decision_gate_path.relative_to(ROOT)),
                    "missing_scope_decisions": report["scope_decision_summary"]["missing_scope_decisions"],
                    "shape_gaps": report["scope_decision_summary"]["scope_decision_gate_shape_gaps"],
                }
            ],
            "optional_scope_metadata_gaps": []
            if optional_scope_metadata_path.exists()
            and not report["optional_scope_summary"]["optional_scope_metadata_shape_gaps"]
            and not report["optional_scope_summary"]["optional_scope_metadata_reference_gaps"]
            and report["optional_scope_summary"]["has_tender_bid_optional_scope_metadata"]
            else [
                {
                    "path": str(optional_scope_metadata_path.relative_to(ROOT)),
                    "shape_gaps": report["optional_scope_summary"]["optional_scope_metadata_shape_gaps"],
                    "reference_gaps": report["optional_scope_summary"]["optional_scope_metadata_reference_gaps"],
                    "has_tender_bid_optional_scope_metadata": report["optional_scope_summary"][
                        "has_tender_bid_optional_scope_metadata"
                    ],
                }
            ],
        }
        if any(blockers.values()):
            print("BACKEND_BUSINESS_FACT_MODEL_AUDIT_BLOCKERS=" + json.dumps(blockers, ensure_ascii=False, sort_keys=True))
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
