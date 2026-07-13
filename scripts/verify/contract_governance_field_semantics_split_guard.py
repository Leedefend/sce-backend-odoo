#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FIELD_SEMANTICS = ROOT / "addons/smart_core/utils/contract_governance_field_semantics.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3453


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    governance_text = _read(GOVERNANCE)
    field_semantics_text = _read(FIELD_SEMANTICS)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not field_semantics_text:
        errors.append(f"missing field semantics module: {FIELD_SEMANTICS.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_field_semantics_module()",
            "contract_governance_field_semantics.py",
            "return _field_semantics.is_technical_field(name, descriptor)",
            "return _field_semantics.classify_field_semantic_type(name, descriptor)",
            "_field_semantics.annotate_field_semantics(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing field semantics split token: {token}")

    if field_semantics_text:
        for token in [
            "def is_technical_field(",
            "def classify_field_semantic_type(",
            "def annotate_field_semantics(",
            "_PROJECT_FORM_PAGE_PRESERVE_FIELDS",
            "_BUSINESS_DETAIL_RELATION_FIELDS",
            "_TECHNICAL_RELATION_FIELD_PREFIXES",
            '"semantic_type"',
            '"surface_role"',
        ]:
            if token not in field_semantics_text:
                errors.append(f"field semantics module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in field_semantics_text:
                errors.append(f"field semantics module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_field_semantics_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_field_semantics_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_field_semantics_split_under_guard")
        if not governance._is_technical_field("message_ids", {"type": "one2many"}):
            errors.append("message one2many fields must remain technical")
        if governance._is_technical_field("task_ids", {"type": "one2many"}):
            errors.append("business detail relation fields must remain preserved")
        if governance._classify_field_semantic_type("partner_id", {"type": "many2one"}) != "relation":
            errors.append("many2one fields must classify as relation")

        data = {
            "fields": {
                "name": {"type": "char"},
                "message_ids": {"type": "one2many"},
                "partner_id": {"type": "many2one"},
                "internal_score": {"type": "integer", "compute": "_compute_score"},
            },
            "views": {
                "form": {
                    "layout": [
                        {"type": "field", "name": "name"},
                        {"type": "field", "name": "partner_id"},
                    ]
                }
            },
            "field_groups": [{"name": "core", "fields": ["name"]}],
            "field_policies": {
                "partner_id": {"visible_profiles": ["create", "edit"], "group": "advanced"},
                "name": {"visible_profiles": ["create", "edit"]},
            },
        }
        governance._annotate_field_semantics(data)
        semantics = data.get("field_semantics") or {}
        if semantics.get("name", {}).get("surface_role") != "core":
            errors.append("field group must mark core field semantics")
        if semantics.get("partner_id", {}).get("semantic_type") != "relation":
            errors.append("layout relation field must remain relation")
        if semantics.get("partner_id", {}).get("surface_role") != "advanced":
            errors.append("field policy group must drive advanced surface role")
        if semantics.get("message_ids", {}).get("surface_role") != "hidden":
            errors.append("technical field without visible policy must be hidden")

    if errors:
        print("[contract_governance_field_semantics_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_field_semantics_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
