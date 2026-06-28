#!/usr/bin/env python3
"""Guard Unified Page Contract v2 verification targets stay complete."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"

OFFLINE_TARGETS = {
    "verify.unified_page_contract.v2.guard_inventory": (
        "scripts/verify/unified_page_contract_v2_guard_inventory.py",
    ),
    "verify.unified_page_contract.v2.schema": (
        "scripts/verify/unified_page_contract_v2_schema_guard.py",
    ),
    "verify.unified_page_contract.v2.assembler": (
        "scripts/verify/unified_page_contract_v2_assembler_guard.py",
    ),
    "verify.unified_page_contract.v2.status": (
        "scripts/verify/unified_page_contract_v2_status_guard.py",
    ),
    "verify.unified_page_contract.v2.action": (
        "scripts/verify/unified_page_contract_v2_action_guard.py",
    ),
    "verify.unified_page_contract.v2.data": (
        "scripts/verify/unified_page_contract_v2_data_guard.py",
    ),
    "verify.unified_page_contract.v2.runtime": (
        "scripts/verify/unified_page_contract_v2_runtime_guard.py",
    ),
    "verify.unified_page_contract.v2.client": (
        "scripts/verify/unified_page_contract_v2_client_guard.py",
    ),
    "verify.unified_page_contract.v2.intent": (
        "scripts/verify/unified_page_contract_v2_intent_guard.py",
    ),
    "verify.unified_page_contract.v2.web_consumer": (
        "scripts/verify/unified_page_contract_v2_web_consumer_guard.py",
        "scripts/verify/web_unified_page_contract_v2_guard.py",
    ),
    "verify.unified_page_contract.v2.web_architecture": (
        "scripts/verify/web_contract_v2_frontend_architecture_guard.py",
    ),
    "verify.unified_page_contract.v2.stable_projection": (
        "scripts/verify/ui_contract_v2_contract_boundary_guard.py",
        "scripts/verify/frontend_v2_policy_projection_guard.py",
    ),
    "verify.unified_page_contract.v2.frontend_static": (),
}

HOST_TARGETS = {
    "verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host": (
        "scripts/verify/unified_page_contract_v2_harmony_h5_compile_acceptance_guard.py",
    ),
    "verify.unified_page_contract.v2.regression_audit.host": (
        "scripts/verify/unified_page_contract_v2_regression_audit.py",
    ),
    "verify.unified_page_contract.v2.web_visual_acceptance.host": (
        "scripts/verify/unified_page_contract_v2_web_visual_acceptance.js",
    ),
    "verify.unified_page_contract.v2.web_form_shadow_browser.host": (
        "scripts/verify/web_contract_v2_form_shadow_browser_smoke.js",
    ),
}


def target_body(makefile: str, target: str) -> str:
    match = re.search(
        rf"^\.PHONY:\s+{re.escape(target)}\n"
        rf"^{re.escape(target)}:[^\n]*\n"
        rf"(?P<body>(?:\t.*\n)*)",
        makefile,
        re.MULTILINE,
    )
    return match.group("body") if match else ""


def has_target(makefile: str, target: str) -> bool:
    return bool(re.search(rf"^\.PHONY:\s+{re.escape(target)}\n^{re.escape(target)}:", makefile, re.MULTILINE))


def aggregate_dependencies(makefile: str) -> set[str]:
    match = re.search(r"^verify\.unified_page_contract\.v2:\s+(?P<deps>.*)$", makefile, re.MULTILINE)
    if not match:
        return set()
    return set(match.group("deps").split())


def main() -> int:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    errors: list[str] = []

    aggregate = aggregate_dependencies(makefile)
    expected_aggregate = set(OFFLINE_TARGETS)
    if aggregate != expected_aggregate:
        errors.append(
            "verify.unified_page_contract.v2 aggregate dependencies drifted; "
            f"extra={sorted(aggregate - expected_aggregate)} missing={sorted(expected_aggregate - aggregate)}"
        )

    for target, scripts in sorted({**OFFLINE_TARGETS, **HOST_TARGETS}.items()):
        if not has_target(makefile, target):
            errors.append(f"Makefile missing target {target}")
            continue
        body = target_body(makefile, target)
        if scripts and not body:
            errors.append(f"Makefile target {target} must have command body")
            continue
        for script in scripts:
            if script not in body:
                errors.append(f"{target} must execute or compile {script}")

    if errors:
        print("[unified_page_contract_v2_guard_inventory] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[unified_page_contract_v2_guard_inventory] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
