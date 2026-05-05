#!/usr/bin/env python3
"""Report and guard the Lite all-terminal coverage matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CLIENTS = ("web_pc", "wx_mini", "harmony_h5")
MOBILE_PACKAGE = ROOT / "frontend/apps/mobile/package.json"
MOBILE_MANIFEST = ROOT / "frontend/apps/mobile/src/manifest.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_tokens(label: str, text: str, tokens: tuple[str, ...], errors: list[str]) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        errors.append(f"{label} missing tokens: {missing}")


def has_target(makefile: str, target: str) -> bool:
    return target in makefile


def build_matrix(parity: dict[str, Any], makefile: str) -> list[dict[str, Any]]:
    signature_ok = parity.get("ok") is True
    reports = parity.get("contractReports") or []
    parity_count = len(reports)
    wx_compile_preflight = (
        has_target(makefile, "verify.unified_page_contract.lite.wx_mini_compile_pilot.host")
        and MOBILE_PACKAGE.exists()
        and MOBILE_MANIFEST.exists()
    )
    wx_real_compile_gate = has_target(makefile, "verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host")
    wx_runtime_acceptance_gate = has_target(makefile, "verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host")
    wx_device_probe_gate = has_target(makefile, "verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host")
    harmony_compile_gate = has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_compile_pilot.host")
    harmony_runtime_acceptance_gate = has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host")
    harmony_device_probe_gate = has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host")
    web_browser_gate = all(
        token in makefile
        for token in (
            "verify.unified_page_contract.lite.all_tree_browser.host",
            "verify.unified_page_contract.lite.all_tree_legacy_browser.host",
            "verify.unified_page_contract.lite.all_tree_matrix_browser.host",
            "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
        )
    )
    return [
        {
            "clientType": "web_pc",
            "semanticContract": "pass" if signature_ok else "fail",
            "semanticContractCases": parity_count,
            "rendererPilot": "available",
            "browserAcceptanceGate": "available" if web_browser_gate else "missing",
            "status": "covered" if signature_ok and web_browser_gate else "blocked",
        },
        {
            "clientType": "wx_mini",
            "semanticContract": "pass" if signature_ok else "fail",
            "semanticContractCases": parity_count,
            "rendererInputPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host")
                else "missing"
            ),
            "uiRendererPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host")
                else "missing"
            ),
            "pageIntegrationGate": "pending",
            "pageIntegrationPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host")
                else "missing"
            ),
            "runtimeMountGate": "pending",
            "runtimeMountPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host")
                else "missing"
            ),
            "compilePreflight": "available" if wx_compile_preflight else "missing",
            "compileGate": "available" if wx_real_compile_gate else "pending",
            "browserAcceptanceGate": "available" if wx_runtime_acceptance_gate else "pending",
            "deviceAcceptanceGate": "probe" if wx_device_probe_gate else "pending",
            "status": "device_acceptance_probe_ready_runner_pending"
            if signature_ok and has_target(makefile, "verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host")
            and has_target(makefile, "verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host")
            and has_target(makefile, "verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host")
            and has_target(makefile, "verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host")
            and wx_compile_preflight
            and wx_real_compile_gate
            and wx_runtime_acceptance_gate
            and wx_device_probe_gate
            else "blocked",
        },
        {
            "clientType": "harmony_h5",
            "semanticContract": "pass" if signature_ok else "fail",
            "semanticContractCases": parity_count,
            "rendererInputPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host")
                else "missing"
            ),
            "uiRendererPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host")
                else "missing"
            ),
            "pageIntegrationGate": "pending",
            "pageIntegrationPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host")
                else "missing"
            ),
            "runtimeMountGate": "pending",
            "runtimeMountPilot": (
                "available"
                if has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host")
                else "missing"
            ),
            "compilePreflight": "available" if harmony_compile_gate else "pending",
            "compileGate": "available" if harmony_compile_gate else "pending",
            "browserAcceptanceGate": "available" if harmony_runtime_acceptance_gate else "pending",
            "deviceAcceptanceGate": "probe" if harmony_device_probe_gate else "pending",
            "status": "device_acceptance_probe_ready_runner_pending"
            if signature_ok and has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host")
            and has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host")
            and has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host")
            and has_target(makefile, "verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host")
            and harmony_compile_gate
            and harmony_runtime_acceptance_gate
            and harmony_device_probe_gate
            else "blocked",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parity-report", required=True, type=Path)
    parser.add_argument("--plan-doc", required=True, type=Path)
    parser.add_argument("--parity-doc", required=True, type=Path)
    parser.add_argument("--matrix-doc", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (args.parity_report, args.plan_doc, args.parity_doc, args.matrix_doc, args.makefile):
        if not path.exists():
            errors.append(f"missing file: {path}")

    parity = read_json(args.parity_report) if args.parity_report.exists() else {}
    plan_doc = read_text(args.plan_doc) if args.plan_doc.exists() else ""
    parity_doc = read_text(args.parity_doc) if args.parity_doc.exists() else ""
    matrix_doc = read_text(args.matrix_doc) if args.matrix_doc.exists() else ""
    makefile = read_text(args.makefile) if args.makefile.exists() else ""

    if parity.get("ok") is not True:
        errors.append("terminal client parity report is not ok")
    if tuple(parity.get("clients") or []) != CLIENTS:
        errors.append(f"terminal clients must be {CLIENTS}, got {parity.get('clients')!r}")

    require_tokens(
        "plan_doc",
        plan_doc,
        (
            "All-Terminal Coverage Plan",
            "Step 3 - Web PC Regression as Coverage Anchor",
            "Step 4 - Mini Program Tree/List Pilot",
            "Step 5 - Harmony H5 Reuse Check",
            "Step 6 - All-Terminal Coverage Matrix",
            "unsupported fallback cannot change business semantics",
        ),
        errors,
    )
    require_tokens(
        "parity_doc",
        parity_doc,
        (
            "Terminal Client Parity",
            "semantic signature comparison for `web_pc`, `wx_mini`, and `harmony_h5`",
            "This batch does not",
        ),
        errors,
    )
    require_tokens(
        "matrix_doc",
        matrix_doc,
        (
            "Terminal Coverage Matrix",
            "`web_pc` is the current browser acceptance anchor",
            "`wx_mini` has a device acceptance probe but device runner is pending",
            "`harmony_h5` has a device acceptance probe but device runner is pending",
            "must not be reported as fully covered",
        ),
        errors,
    )
    require_tokens(
        "makefile",
        makefile,
        (
            "verify.unified_page_contract.lite.terminal_client_parity",
            "verify.unified_page_contract.lite.terminal_coverage_matrix",
            "verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_renderer_input_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_compile_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host",
            "verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_compile_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host",
            "verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host",
            "verify.unified_page_contract.lite.all_tree_acceptance_browser.host",
            "unified_page_contract_lite_terminal_coverage_matrix_guard.py",
        ),
        errors,
    )

    matrix = build_matrix(parity, makefile)
    if not any(item["clientType"] == "web_pc" and item["status"] == "covered" for item in matrix):
        errors.append("web_pc must remain the covered browser anchor")
    wx_item = next((row for row in matrix if row["clientType"] == "wx_mini"), None)
    if not wx_item or wx_item["status"] != "device_acceptance_probe_ready_runner_pending":
        errors.append("wx_mini must be explicitly device-acceptance-probe-ready and runner-pending")
    harmony_item = next((row for row in matrix if row["clientType"] == "harmony_h5"), None)
    if not harmony_item or harmony_item["status"] != "device_acceptance_probe_ready_runner_pending":
        errors.append("harmony_h5 must be explicitly device-acceptance-probe-ready and runner-pending")

    report = {
        "ok": not errors,
        "decision": "terminal_matrix_device_probes_ready_runners_pending" if not errors else "blocked",
        "clients": list(CLIENTS),
        "matrix": matrix,
        "nextRequiredGates": [
            "verify.unified_page_contract.lite.wx_mini_device_runner_acceptance.host",
            "verify.unified_page_contract.lite.harmony_h5_device_runner_acceptance.host",
        ],
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite terminal coverage matrix guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite terminal coverage matrix guard passed")
    print("- web_pc: covered browser anchor")
    print("- wx_mini: device acceptance probe ready, device runner pending")
    print("- harmony_h5: device acceptance probe ready, device runner pending")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
