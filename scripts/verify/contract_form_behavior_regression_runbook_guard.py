#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs/engineering_convergence/contract_form_behavior_regression_runbook.md"
SIDE_EFFECT_MAP = ROOT / "docs/engineering_convergence/contract_form_side_effect_map.md"
CI = ROOT / "make/ci.mk"

SCENARIOS = [
    "CF-BHV-01",
    "CF-BHV-02",
    "CF-BHV-03",
    "CF-BHV-04",
    "CF-BHV-05",
    "CF-BHV-06",
    "CF-BHV-07",
    "CF-BHV-08",
    "CF-BHV-09",
    "CF-BHV-10",
    "CF-BHV-11",
    "CF-BHV-12",
    "CF-BHV-13",
    "CF-BHV-14",
    "CF-BHV-15",
]

REQUIRED_TOKENS = [
    "Contract Form Behavior Regression Runbook",
    "Baseline: `ContractFormPage.vue <= 6000`",
    "not authorize moving",
    "`saveRecord`",
    "`runAction`",
    "`runOnchangeRoundtrip`",
    "`make ci.local.quick`",
    "`make ci`",
    "`make test.e2e` or mapped browser acceptance target",
    "Screenshot",
    "Browser log",
    "Server/API log",
    "Request trace",
    "Result summary",
    "Browser/container",
]

REQUIRED_GUARDS = [
    "contract_form_save_payload_builder_guard.py",
    "contract_form_side_effect_regression_guard.py",
    "contract_form_runtime_state_behavior_guard.sh",
    "contract_form_action_plan_builder_guard.py",
    "contract_form_runtime_state_protocol_guard.py",
    "contract_form_onchange_normalization_guard.py",
    "frontend_page_contract_boundary_guard.py",
    "frontend_page_contract_orchestration_consumption_guard.py",
    "frontend_contract_consumer_intrusion_guard.py",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    runbook = _read(RUNBOOK)
    side_effect_map = _read(SIDE_EFFECT_MAP)
    ci = _read(CI)

    if not runbook:
        errors.append(f"missing runbook: {RUNBOOK.relative_to(ROOT)}")
    if not side_effect_map:
        errors.append(f"missing side-effect map: {SIDE_EFFECT_MAP.relative_to(ROOT)}")

    for token in REQUIRED_TOKENS:
        if token not in runbook:
            errors.append(f"runbook missing token: {token}")

    for scenario in SCENARIOS:
        marker = f"| {scenario} |"
        if marker not in runbook:
            errors.append(f"runbook missing scenario row: {scenario}")

    for guard in REQUIRED_GUARDS:
        if guard not in runbook:
            errors.append(f"runbook must cite guard: {guard}")

    if "## Behavior Regression Matrix" not in side_effect_map:
        errors.append("side-effect map must retain behavior regression matrix")
    if "Manual form regression means exercising the path in a browser or containerized" not in side_effect_map:
        errors.append("side-effect map must retain manual/browser regression warning")

    ci_tokens = [
        "python3 scripts/verify/contract_form_behavior_regression_runbook_guard.py",
        "python3 scripts/verify/contract_form_side_effect_regression_guard.py",
        "scripts/verify/contract_form_runtime_state_behavior_guard.sh",
    ]
    for token in ci_tokens:
        if token not in ci:
            errors.append(f"ci.local.quick missing token: {token}")

    if errors:
        print("[contract_form_behavior_regression_runbook_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_behavior_regression_runbook_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
