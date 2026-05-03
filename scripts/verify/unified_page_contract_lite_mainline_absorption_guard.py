#!/usr/bin/env python3
"""Guard the Lite contract governance baseline after mainline absorption."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def lite_core_file(suffix: str) -> str:
    return "addons/smart_core/core/" + "unified_page_contract_lite_" + suffix


REQUIRED_FILES = (
    lite_core_file("adapter.py"),
    lite_core_file("source_normalizer.py"),
    lite_core_file("patch_normalizer.py"),
    lite_core_file("preview.py"),
    "docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json",
    "docs/architecture/unified_page_contract_lite/frontend_consumption_contract_freeze_v2_0_batch_44.md",
    "docs/architecture/unified_page_contract_lite/frontend_pilot_implementation_batch_45.md",
    "docs/architecture/unified_page_contract_lite/frontend_pilot_browser_smoke_batch_46.md",
    "frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts",
    "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts",
    "frontend/apps/web/src/api/contract.ts",
    "frontend/apps/web/src/app/resolvers/actionResolver.ts",
)

CHECKPOINT_TOKENS = (
    "Status: mainline absorbed",
    "contractVersion: 2.0.0",
    "default-off",
    "project.project:tree",
    "load_contract opt-in preview",
    "legacy `ui.contract` remains the default path",
    "VITE_LITE_CONTRACT_PILOT=1",
    "No mobile contract fields are introduced by this checkpoint.",
)

MAKEFILE_TARGETS = (
    "verify.unified_page_contract.lite",
    "verify.unified_page_contract.lite.contract_freeze_v2_0",
    "verify.unified_page_contract.lite.frontend_pilot_implementation",
    "verify.unified_page_contract.lite.frontend_pilot_browser.host",
    "verify.unified_page_contract.lite.mainline_absorption",
)

FRONTEND_TOKENS = {
    "frontend/apps/web/src/app/runtime/unifiedPageContractLitePilot.ts": (
        "LITE_CONTRACT_PILOT_MODEL = 'project.project'",
        "LITE_CONTRACT_PILOT_VIEW = 'tree'",
        "VITE_LITE_CONTRACT_PILOT",
        "=== '1'",
    ),
    "frontend/apps/web/src/api/contract.ts": (
        "loadModelLitePreviewContract",
        "contractMode: 'lite_preview'",
        "contractVersion: '2.0.0'",
        "entryPoint: 'load_contract'",
    ),
    "frontend/apps/web/src/app/resolvers/actionResolver.ts": (
        "needsLiteContractAllTreeViewPreflight(seedMeta)",
        "isLiteContractPilotCandidate(candidateMeta)",
        "loadModelLitePreviewContract",
        "loadActionContract(actionId)",
    ),
}

FORBIDDEN_TOKENS = (
    "VITE_LITE_CONTRACT_PILOT=1 by default",
    "Lite default enabled",
    "system.init Lite default",
    "login Lite default",
    "mobile_layout",
    "mobile_display_fields",
    "mobile_action_placement",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-doc", required=True, type=Path)
    parser.add_argument("--makefile", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []

    missing_files = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing_files:
        errors.append(f"missing required Lite governance files: {missing_files}")

    if not args.checkpoint_doc.exists():
        errors.append(f"missing checkpoint doc: {args.checkpoint_doc}")
        checkpoint_text = ""
    else:
        checkpoint_text = read_text(args.checkpoint_doc)
        missing = [token for token in CHECKPOINT_TOKENS if token not in checkpoint_text]
        if missing:
            errors.append(f"checkpoint doc missing tokens: {missing}")

    makefile_text = read_text(args.makefile)
    missing_targets = [target for target in MAKEFILE_TARGETS if target not in makefile_text]
    if missing_targets:
        errors.append(f"Makefile missing Lite governance targets: {missing_targets}")

    for rel_path, tokens in FRONTEND_TOKENS.items():
        path = ROOT / rel_path
        if not path.exists():
            continue
        text = read_text(path)
        missing = [token for token in tokens if token not in text]
        if missing:
            errors.append(f"{rel_path} missing tokens: {missing}")

    searched_sources = [checkpoint_text, makefile_text]
    for rel_path in FRONTEND_TOKENS:
        path = ROOT / rel_path
        if path.exists():
            searched_sources.append(read_text(path))
    forbidden = sorted({token for token in FORBIDDEN_TOKENS if any(token in source for source in searched_sources)})
    if forbidden:
        errors.append(f"forbidden mainline absorption tokens found: {forbidden}")

    report = {
        "ok": not errors,
        "decision": "lite_governance_mainline_absorbed_default_off" if not errors else "blocked",
        "contract_version": "2.0.0",
        "pilot": "project.project:tree",
        "default_path": "legacy ui.contract",
        "feature_flag": "VITE_LITE_CONTRACT_PILOT=1 required for pilot",
        "missing_files": missing_files,
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite mainline absorption guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite mainline absorption guard passed")
    print("- decision: lite_governance_mainline_absorbed_default_off")
    print("- default path: legacy ui.contract")
    print("- pilot: project.project:tree")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
