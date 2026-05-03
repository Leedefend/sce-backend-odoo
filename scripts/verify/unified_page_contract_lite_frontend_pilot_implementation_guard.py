#!/usr/bin/env python3
"""Guard the default-off Lite frontend pilot implementation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts",
    "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts",
    "frontend/apps/web/src/api/contract.ts",
    "frontend/apps/web/src/app/resolvers/actionResolver.ts",
    "scripts/verify/unified_page_contract_lite_frontend_pilot_browser_smoke.js",
    "docs/architecture/unified_page_contract_lite/frontend_pilot_implementation_batch_45.md",
    "docs/architecture/unified_page_contract_lite/frontend_pilot_browser_smoke_batch_46.md",
)

REQUIRED_TOKENS = {
    "frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts": (
        "contractVersion: '2.0.0'",
        "isUnifiedPageContractLite",
        "extractLitePreviewEnvelope",
        "lite_preview",
        "lite_contract",
    ),
    "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts": (
        "LITE_CONTRACT_PILOT_MODEL = 'project.project'",
        "LITE_CONTRACT_PILOT_VIEW = 'tree'",
        "VITE_LITE_CONTRACT_PILOT",
        "=== '1'",
        "adaptLiteContractToActionViewContract",
        "extractLiteContractFromIntentBody",
    ),
    "frontend/apps/web/src/api/contract.ts": (
        "loadModelLitePreviewContract",
        "intent: 'load_contract'",
        "contractMode: 'lite_preview'",
        "contractVersion: '2.0.0'",
        "entryPoint: 'load_contract'",
        "fallbackMode: 'legacy_default'",
    ),
    "frontend/apps/web/src/app/resolvers/actionResolver.ts": (
        "needsLiteContractAllTreeViewPreflight(seedMeta)",
        "isLiteContractPilotCandidate(candidateMeta)",
        "loadModelLitePreviewContract",
        "adaptLiteContractToActionViewContract",
        "loadActionContract(actionId)",
    ),
    "docs/architecture/unified_page_contract_lite/frontend_pilot_implementation_batch_45.md": (
        "implemented behind default-off feature flag",
        "project.project:tree",
        "load_contract opt-in preview",
        "VITE_LITE_CONTRACT_PILOT=0",
        "legacy `ui.contract`",
        "set VITE_LITE_CONTRACT_PILOT=0 and redeploy frontend",
    ),
    "scripts/verify/unified_page_contract_lite_frontend_pilot_browser_smoke.js": (
        "VITE_LITE_CONTRACT_PILOT",
        "load_contract",
        "lite_preview",
        "payloadType === 'lite_contract'",
        "ui.contract",
        "project tree did not render rows",
    ),
    "docs/architecture/unified_page_contract_lite/frontend_pilot_browser_smoke_batch_46.md": (
        "VITE_LITE_CONTRACT_PILOT=1",
        "load_contract Lite preview",
        "no `ui.contract` fallback",
        "project.project:tree",
        "verify.unified_page_contract.lite.frontend_pilot_browser.host",
    ),
}

FORBIDDEN_TOKENS = (
    "VITE_LITE_CONTRACT_PILOT=1 by default",
    "system.init Lite",
    "login Lite",
    "runtimeContract enabled",
    "dependencyGraph enabled",
    "selectorStatus enabled",
)


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--runtime-negative-report", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    missing_files = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing_files:
        errors.append(f"missing pilot files: {missing_files}")

    for path, tokens in REQUIRED_TOKENS.items():
        full = ROOT / path
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8")
        missing = [token for token in tokens if token not in text]
        if missing:
            errors.append(f"{path} missing required tokens: {missing}")
        forbidden = [token for token in FORBIDDEN_TOKENS if token in text]
        if forbidden:
            errors.append(f"{path} contains forbidden tokens: {forbidden}")

    makefile_text = args.makefile.read_text(encoding="utf-8")
    if "verify.unified_page_contract.lite.frontend_pilot_implementation" not in makefile_text:
        errors.append("Makefile missing frontend pilot implementation target")
    if "verify.unified_page_contract.lite.frontend_pilot_browser.host" not in makefile_text:
        errors.append("Makefile missing frontend pilot browser smoke target")

    runtime_report: dict[str, Any] = {}
    if args.runtime_negative_report.exists():
        runtime_report = json.loads(args.runtime_negative_report.read_text(encoding="utf-8"))
        if runtime_report.get("ok") is not True:
            errors.append("frontend runtime negative guard report is not ok")
    else:
        errors.append(f"missing runtime negative report: {args.runtime_negative_report}")

    report = {
        "ok": not errors,
        "decision": "frontend_lite_pilot_implemented_default_off" if not errors else "blocked",
        "feature_flag": "VITE_LITE_CONTRACT_PILOT=0",
        "pilot": "project.project:tree",
        "source_entry": "load_contract opt-in preview",
        "missing_files": missing_files,
        "runtime_negative_policy": runtime_report.get("policy"),
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite frontend pilot implementation guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite frontend pilot implementation guard passed")
    print("- decision: frontend_lite_pilot_implemented_default_off")
    print("- pilot: project.project:tree")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
