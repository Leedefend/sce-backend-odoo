#!/usr/bin/env python3
"""Guard product-release view orchestration contracts against full UI trees."""

from __future__ import annotations

import ast
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
XML_ROOT = ROOT / "addons/smart_construction_core"
PRODUCT_SOURCE = "smart_construction_core.product_release"
ALLOWED_COMPOSITION_MODES = {"entry_semantic_surface", "semantic_entry_surface"}


def _text(value) -> str:
    return str(value or "").strip()


def _field_value(record: ET.Element, name: str) -> str:
    for field in record.findall("field"):
        if field.get("name") == name:
            return field.get("eval") or (field.text or "")
    return ""


def _literal(value: str):
    try:
        return ast.literal_eval(value)
    except Exception:
        return None


def _is_product_release(payload: dict) -> bool:
    orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
    context = orchestration.get("context") if isinstance(orchestration.get("context"), dict) else {}
    return (
        _text(context.get("source")) == PRODUCT_SOURCE
        or _text(context.get("source_status")) == "product_release"
    )


def _iter_contract_records():
    for path in sorted(XML_ROOT.rglob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            raise AssertionError(f"cannot parse XML {path.relative_to(ROOT)}: {exc}") from exc
        for record in root.iter("record"):
            if record.get("model") == "ui.business.config.contract":
                yield path, record


def main() -> int:
    errors: list[str] = []
    checked = 0
    for path, record in _iter_contract_records():
        raw = _field_value(record, "contract_json")
        payload = _literal(raw)
        if not isinstance(payload, dict) or not _is_product_release(payload):
            continue
        checked += 1
        orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
        views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        record_id = record.get("id") or "<unknown>"
        label = f"{path.relative_to(ROOT)}:{record_id}"
        if form.get("layout"):
            errors.append(f"{label}: product_release form contracts must not declare layout; use fields/sections plus backend composition_mode")
        if form.get("fields") and _text(form.get("composition_mode")) not in ALLOWED_COMPOSITION_MODES:
            errors.append(f"{label}: product_release form fields require composition_mode=entry_semantic_surface")

    if errors:
        print("[view_orchestration_product_boundary_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print(f"[view_orchestration_product_boundary_guard] PASS checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
