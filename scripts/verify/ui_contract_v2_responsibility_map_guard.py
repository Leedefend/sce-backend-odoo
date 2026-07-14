#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/engineering_convergence/ui_contract_v2_responsibility_map.md"
HANDLER = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"
ADAPTERS = ROOT / "addons/smart_core/handlers/ui_contract_v2_adapters.py"
CI = ROOT / "make/ci.mk"

REQUIRED_METHODS = [
    "handle",
    "_resolve_entry_contract",
    "_inject_action_window_contract",
    "_inject_business_category_form_policy",
    "_merge_user_list_preference_columns",
    "_form_structure_governance",
    "_merge_business_list_profile",
    "_action_scoped_visible_list_columns",
    "_scbs55_legacy_visible_list_override",
    "_hydrate_record_snapshot",
    "_inject_native_group_layout_columns",
    "_handle_scene_contract",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _class_method_names(source: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "UiContractV2Handler":
            return {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)
    handler = _read(HANDLER)
    adapters = _read(ADAPTERS)
    ci = _read(CI)

    if not doc:
        errors.append(f"missing responsibility map: {DOC.relative_to(ROOT)}")
    if not handler:
        errors.append(f"missing handler: {HANDLER.relative_to(ROOT)}")
    if not adapters:
        errors.append(f"missing adapters: {ADAPTERS.relative_to(ROOT)}")

    for token in [
        "UI Contract V2 Responsibility Map",
        "Current size: 3,731 lines",
        "Stage 1 request adapter split",
        "## Public Entry Points",
        "## Responsibility Bands",
        "## Current Side-Effect Boundaries",
        "## Do Not Move Yet",
        "## Stage 1 Target",
        "## Stage 2 Candidate",
        "## Verification Gaps",
        "## Invariants",
        "`UiContractV2Handler.handle`",
        "`ui_contract_v2.py` is locked at `<=3731` lines",
        "`ui_contract_v2_adapters.py` owns request/result adapters",
        "`ui_contract_v2_adapters.py` also owns pure value builders",
        "Do not move these responsibilities before behavior coverage exists",
        "UiContractHandler",
        "PageAssembler",
        "SCBS55 legacy-visible projection",
        "record snapshot hydration",
        "view XML parsing",
        "scene contract source loading",
        "projection-only",
        "must not become the source of business truth",
    ]:
        if token not in doc:
            errors.append(f"responsibility map missing token: {token}")

    if handler:
        line_count = handler.count("\n") + (0 if handler.endswith("\n") else 1)
        if line_count > 3731:
            errors.append(f"ui_contract_v2.py line budget exceeded: {line_count} > 3731")
        methods = _class_method_names(handler)
        for name in REQUIRED_METHODS:
            if name not in methods:
                errors.append(f"UiContractV2Handler missing method: {name}")
        for token in [
            "UiContractHandler(",
            "assemble_unified_page_contract_v2(",
            "trim_unified_page_contract_v2(",
            "call_extension_hook_first(",
            "load_scenes_from_db_or_fallback(",
            "class UiContractV2Handler(BaseIntentHandler):",
            "from . import ui_contract_v2_adapters as _adapters",
            "return _adapters.params_from_payload(payload, self.params)",
            "return _adapters.headers_from_request(self.request, _logger)",
            "return _adapters.trim_limit_params(params)",
            "return _adapters.ui_contract_params(params)",
            "return _adapters.envelope(result)",
            "return _adapters.error_result(",
            "return _adapters.safe_eval_action_value(value, default)",
            "return _adapters.allowed_models_from_hook(env, hook_name)",
            "return _adapters.standard_chatter_actions(",
        ]:
            if token not in handler:
                errors.append(f"ui_contract_v2.py missing orchestration token: {token}")

    if adapters:
        for token in [
            "def params_from_payload(",
            "def headers_from_request(",
            "def trim_limit_params(",
            "def ui_contract_params(",
            "def envelope(",
            "def error_result(",
            "def safe_eval_action_value(",
            "def allowed_models_from_hook(",
            "def standard_chatter_actions(",
            "def v2_policy_projection_source_authority(",
            "def v2_policy_projection(",
            "parse_positive_int(",
            "IntentExecutionResult(",
            "call_extension_hook_first(",
        ]:
            if token not in adapters:
                errors.append(f"ui_contract_v2_adapters.py missing token: {token}")

    ci_token = "python3 scripts/verify/ui_contract_v2_responsibility_map_guard.py"
    if ci_token not in ci:
        errors.append("ci.local.quick must run ui_contract_v2_responsibility_map_guard.py")

    if errors:
        print("[ui_contract_v2_responsibility_map_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[ui_contract_v2_responsibility_map_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
