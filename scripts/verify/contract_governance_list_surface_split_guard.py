#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
LIST_SURFACE = ROOT / "addons/smart_core/utils/contract_governance_list_surface.py"
CI = ROOT / "make/ci.mk"

MAX_GOVERNANCE_LINES = 2898


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
    list_surface_text = _read(LIST_SURFACE)
    ci_text = _read(CI)

    if not governance_text:
        errors.append(f"missing governance file: {GOVERNANCE.relative_to(ROOT)}")
    if not list_surface_text:
        errors.append(f"missing list surface module: {LIST_SURFACE.relative_to(ROOT)}")

    if governance_text:
        line_count = len(governance_text.splitlines())
        if line_count > MAX_GOVERNANCE_LINES:
            errors.append(f"contract_governance.py line budget exceeded: {line_count} > {MAX_GOVERNANCE_LINES}")
        for token in [
            "def _load_list_surface_module()",
            "contract_governance_list_surface.py",
            "def _apply_standard_search_toolbar_labels(data: dict) -> None:",
            "_list_surface.apply_standard_search_toolbar_labels(data)",
            "def _govern_tier_review_list_for_user(data: dict) -> None:",
            "_list_surface.govern_tier_review_list_for_user(",
            "nav_action_prefixes=_TIER_REVIEW_LIST_NAV_ACTION_PREFIXES",
        ]:
            if token not in governance_text:
                errors.append(f"contract_governance.py missing list surface split token: {token}")

    if list_surface_text:
        for token in [
            "def apply_standard_search_toolbar_labels(",
            "def govern_tier_review_list_for_user(",
            "\"row_open\": \"打开\"",
            "payload[\"view_mode\"] = payload.get(\"view_mode\") or \"form\"",
            "mark_legacy_industry_governance_profile(data, \"tier.review.list\")",
            "key.startswith(prefix) for prefix in nav_action_prefixes",
        ]:
            if token not in list_surface_text:
                errors.append(f"list surface module missing token: {token}")
        for token in (".search(", ".write(", "requests.", "env[", "registry["):
            if token in list_surface_text:
                errors.append(f"list surface module must remain projection-only; found token: {token}")

    if "python3 scripts/verify/contract_governance_list_surface_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run contract_governance_list_surface_split_guard.py")

    if not errors:
        governance = _load(GOVERNANCE, "contract_governance_list_surface_split_under_guard")
        data = {
            "search": {},
            "views": {
                "tree": {
                    "row_actions": [
                        {"name": "open_form", "payload": {}},
                    ],
                },
            },
        }
        governance._apply_standard_search_toolbar_labels(data)
        labels = ((data.get("search") or {}).get("ui_labels") or {})
        action = (((data.get("views") or {}).get("tree") or {}).get("row_actions") or [{}])[0]
        if labels.get("row_open") != "打开":
            errors.append("list surface labels must include row_open")
        if action.get("label") != "打开" or (action.get("payload") or {}).get("view_mode") != "form":
            errors.append("list surface row open action semantics were not applied")

        tier_data = {
            "model": "tier.review",
            "view_type": "tree",
            "buttons": [
                {"key": "open_record", "label": "Open"},
                {"key": "action_tier_review_open_form", "label": "Open form"},
            ],
            "toolbar": {
                "header": [
                    {"key": "action_tier_review_open_form"},
                    {"key": "bulk_approve"},
                ],
                "footer": [{"key": "action_tier_review_open_related"}],
            },
            "action_groups": [
                {
                    "name": "main",
                    "actions": [
                        {"key": "action_tier_review_open_form"},
                        {"key": "approve"},
                    ],
                },
                {
                    "name": "empty",
                    "actions": [{"key": "action_tier_review_open_related"}],
                },
            ],
        }
        governance._govern_tier_review_list_for_user(tier_data)
        if [row.get("key") for row in tier_data.get("buttons", [])] != [
            "open_record",
            "action_tier_review_open_form",
        ]:
            errors.append("tier review facade must preserve actions when no navigation prefixes are configured")
        profiles = (tier_data.get("governance_diagnostics") or {}).get("legacy_industry_profiles") or []
        if "tier.review.list" not in profiles:
            errors.append("tier review list must keep its legacy governance profile marker")

        list_surface = _load(LIST_SURFACE, "contract_governance_list_surface_direct_under_guard")
        filtered_data = {
            "buttons": [
                {"key": "open_record", "label": "Open"},
                {"key": "action_tier_review_open_form", "label": "Open form"},
            ],
            "toolbar": {
                "header": [
                    {"key": "action_tier_review_open_form"},
                    {"key": "bulk_approve"},
                ],
                "footer": [{"key": "action_tier_review_open_related"}],
            },
            "action_groups": [
                {
                    "name": "main",
                    "actions": [
                        {"key": "action_tier_review_open_form"},
                        {"key": "approve"},
                    ],
                },
                {
                    "name": "empty",
                    "actions": [{"key": "action_tier_review_open_related"}],
                },
            ],
        }
        marked: list[str] = []
        list_surface.govern_tier_review_list_for_user(
            filtered_data,
            is_model_tree_contract=lambda data, model: model == "tier.review",
            mark_legacy_industry_governance_profile=lambda data, profile: marked.append(profile),
            nav_action_prefixes=("action_tier_review_",),
        )
        if [row.get("key") for row in filtered_data.get("buttons", [])] != ["open_record"]:
            errors.append("tier review list buttons must drop navigation actions when prefixes are configured")
        if [row.get("key") for row in filtered_data.get("toolbar", {}).get("header", [])] != ["bulk_approve"]:
            errors.append("tier review list toolbar must drop navigation actions when prefixes are configured")
        if filtered_data.get("toolbar", {}).get("footer") != []:
            errors.append("tier review list footer must preserve an empty filtered slot")
        groups = filtered_data.get("action_groups") or []
        if len(groups) != 1 or [row.get("key") for row in groups[0].get("actions", [])] != ["approve"]:
            errors.append("tier review list action groups must drop empty navigation-only groups")
        if marked != ["tier.review.list"]:
            errors.append("tier review list direct module path must invoke profile marker callback")

    if errors:
        print("[contract_governance_list_surface_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_list_surface_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
