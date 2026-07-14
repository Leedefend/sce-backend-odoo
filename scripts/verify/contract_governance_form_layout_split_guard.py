#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
FORM_LAYOUT = ROOT / "addons/smart_core/utils/contract_governance_form_layout.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3361


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
    form_layout_text = _read(FORM_LAYOUT)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not form_layout_text:
        errors.append(f"missing form layout module: {FORM_LAYOUT.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_form_layout_module()",
            "contract_governance_form_layout.py",
            "return _form_layout.collect_layout_field_names(nodes)",
            "return _form_layout.find_layout_sheet_node(nodes)",
            "_form_layout.backfill_form_layout_from_visible_fields(",
            "return _form_layout.make_labeled_field_node(name, fields_map, preferred_labels)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing form layout split token: {token}")

    if form_layout_text:
        for token in [
            "def collect_layout_field_names(",
            "def find_layout_sheet_node(",
            "def make_labeled_field_node(",
            "def backfill_form_layout_from_visible_fields(",
            "visible_fields_backfill_group",
            '"one2many": "one2many_list"',
            "_ENTERPRISE_COMPANY_FIELD_LABELS",
            "_ENTERPRISE_USER_FIELD_LABELS",
        ]:
            if token not in form_layout_text:
                errors.append(f"form layout module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in form_layout_text:
                errors.append(f"form layout module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_form_layout_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_form_layout_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_form_layout_split_under_guard")
        layout = [
            {
                "type": "sheet",
                "children": [
                    {"type": "group", "children": [{"type": "field", "name": "name"}]},
                    {"type": "notebook", "pages": [{"type": "page", "children": [{"type": "field", "name": "state"}]}]},
                ],
            }
        ]
        if governance._collect_layout_field_names(layout) != ["name", "state"]:
            errors.append("layout field collection must preserve nested field order")
        if governance._find_layout_sheet_node(layout) is not layout[0]:
            errors.append("sheet lookup must return the nested sheet node")

        node = governance._make_labeled_field_node(
            "partner_ids",
            {"partner_ids": {"type": "many2many", "string": "Partners"}},
        )
        if node.get("fieldInfo", {}).get("widget") != "many2many_tags":
            errors.append("many2many field node must infer many2many_tags widget")

        data = {
            "head": {"view_type": "form"},
            "visible_fields": ["name", "partner_id", "message_ids"],
            "fields": {
                "name": {"type": "char", "string": "Name"},
                "partner_id": {"type": "many2one", "string": "Partner"},
                "message_ids": {"type": "one2many", "string": "Messages"},
            },
            "views": {"form": {"layout": layout}},
        }
        governance._backfill_form_layout_from_visible_fields(data)
        sheet = data["views"]["form"]["layout"][0]
        children = sheet.get("children") or []
        backfill = children[-1] if children else {}
        backfill_names = [
            row.get("name")
            for row in backfill.get("children", [])
            if isinstance(row, dict)
        ]
        if backfill.get("name") != "visible_fields_backfill_group":
            errors.append("missing visible fields must be appended as a backfill group")
        if "partner_id" not in backfill_names:
            errors.append("non-technical missing visible field must be backfilled")
        if "message_ids" in backfill_names:
            errors.append("technical missing visible field must not be backfilled")

    if errors:
        print("[contract_governance_form_layout_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_form_layout_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
