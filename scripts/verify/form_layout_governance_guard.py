#!/usr/bin/env python3
"""Guard form layout governance against post-processor drift."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"


def section(source: str, start: str, end: str) -> str:
    start_index = source.find(start)
    if start_index < 0:
        raise AssertionError(f"missing section start: {start}")
    end_index = source.find(end, start_index + len(start))
    if end_index < 0:
        raise AssertionError(f"missing section end after {start}: {end}")
    return source[start_index:end_index]


def assert_contains(value: str, needle: str, label: str) -> None:
    if needle not in value:
        raise AssertionError(f"{label} must contain {needle!r}")


def assert_not_contains(value: str, needle: str, label: str) -> None:
    if needle in value:
        raise AssertionError(f"{label} must not contain duplicated local logic {needle!r}")


def main() -> int:
    source = HANDLER.read_text(encoding="utf-8")
    helper = "def _apply_form_layout_governance_to_group("
    assert_contains(source, "def _form_layout_governance(", "ui_contract_v2.py")
    assert_contains(source, "def _form_layout_governance_columns(", "ui_contract_v2.py")
    assert_contains(source, "def _form_layout_columns_from_governance(", "ui_contract_v2.py")
    assert_contains(source, helper, "ui_contract_v2.py")

    business_groups = section(
        source,
        "def _apply_business_config_form_groups_to_v2(",
        "def _normalize_general_contract_company_form(",
    )
    general_contract = section(
        source,
        "def _normalize_general_contract_company_form(",
        "def _form_layout_governance(",
    )
    construction_diary = section(
        source,
        "def _normalize_construction_diary_form(",
        "def _apply_legacy_visible_list_layout(",
    )
    structure_contract = section(
        source,
        "def _build_form_structure_contract(",
        "def _merge_business_list_profile(",
    )

    for label, body in (
        ("business config form groups", business_groups),
        ("general contract form", general_contract),
        ("construction diary form", construction_diary),
    ):
        assert_contains(body, "_apply_form_layout_governance_to_group(", label)

    for label, body in (
        ("business config form groups", business_groups),
        ("general contract form", general_contract),
        ("construction diary form", construction_diary),
    ):
        assert_not_contains(body, "def apply_group_columns(", label)
        assert_not_contains(body, "def group_layout_columns(", label)
        assert_not_contains(body, "group_columns = governance.get(\"group_columns\")", label)
        assert_not_contains(body, "form_columns = int(governance.get(\"form_columns\")", label)
    assert_contains(
        structure_contract,
        "_form_layout_columns_from_governance(governance",
        "form structure contract",
    )
    assert_not_contains(
        structure_contract,
        "configured_group_columns =",
        "form structure contract",
    )
    assert_not_contains(
        structure_contract,
        "def configured_columns(",
        "form structure contract",
    )
    assert_not_contains(
        structure_contract,
        "form_columns = int(governance.get(\"form_columns\")",
        "form structure contract",
    )

    native_columns = section(
        source,
        "def _inject_native_group_layout_columns(",
        "def _handle_scene_contract(",
    )
    assert_contains(native_columns, 'node["cols"] = columns', "native group layout projection")
    assert_contains(native_columns, 'node["columns"] = columns', "native group layout projection")
    assert_contains(native_columns, 'attrs["col"] = str(columns)', "native group layout projection")

    print("form layout governance guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
