#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
LABELS = ROOT / "addons/smart_core/utils/contract_governance_labels.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 3830


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
    labels_text = _read(LABELS)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not labels_text:
        errors.append(f"missing labels module: {LABELS.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_labels_module()",
            "contract_governance_labels.py",
            "_labels._LEGACY_FIELD_PRESENTATION_REGISTRY = _LEGACY_FIELD_PRESENTATION_REGISTRY",
            "_labels.emit_relation_entry_semantics(data)",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing labels split token: {token}")

    if labels_text:
        for token in [
            "def business_field_label(",
            "def normalize_business_field_labels(",
            "def preserve_native_layout_labels(",
            "def emit_relation_entry_semantics(",
        ]:
            if token not in labels_text:
                errors.append(f"labels module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in labels_text:
                errors.append(f"labels module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_labels_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_labels_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_labels_split_under_guard")
        governance.register_legacy_field_presentation("guard.model", "display_name", {"label": "Guard Label"})
        data = {
            "head": {"model": "guard.model"},
            "fields": {
                "display_name": {"string": "Display Name"},
                "partner_id": {
                    "relation": "res.partner",
                    "relation_entry": {"create_mode": "inline", "can_create": True},
                },
            },
            "views": {
                "form": {
                    "layout": [
                        {"type": "page", "attributes": {"string": "description"}},
                    ],
                },
                "tree": {"columns_schema": [{"name": "display_name", "string": "Display Name"}]},
            },
        }
        governance._normalize_business_field_labels(data)
        governance._preserve_native_layout_labels(data)
        governance._emit_relation_entry_semantics(data)
        if data["fields"]["display_name"].get("string") != "Guard Label":
            errors.append("business labels must read shared legacy field presentation registry")
        page = data["views"]["form"]["layout"][0]
        if page.get("label") != "描述" or page.get("title") != "描述":
            errors.append("native layout page labels must be preserved and translated")
        entries = ((data.get("semantic_page") or {}).get("relation_entries") or [])
        if not entries or entries[0].get("field") != "partner_id" or entries[0].get("create_mode") != "inline":
            errors.append("relation entry semantics must be emitted")

    if errors:
        print("[contract_governance_labels_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_labels_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
