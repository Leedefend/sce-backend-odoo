#!/usr/bin/env python3
"""Guard the shared frontend Lite terminal consumer boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminal.ts"
STORE_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalStore.ts"
RENDERER_INPUT_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRendererInput.ts"
RENDERER_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRenderer.ts"
PAGE_INTEGRATION_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalPageIntegration.ts"
RUNTIME_MOUNT_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLiteTerminalRuntimeMount.ts"
BASE_CONTRACT_PATH = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractLite.ts"
MAKEFILE_PATH = ROOT / "Makefile"

REQUIRED_BOUNDARY_TOKENS = (
    "LITE_TERMINAL_CLIENTS = ['web_pc', 'wx_mini', 'harmony_h5']",
    "type LiteTerminalClient",
    "type LiteTerminalConsumerBoundary",
    "createLiteTerminalConsumerBoundary",
    "parseLiteTerminalContract",
    "isUnifiedPageContractLite",
    "widgetIds",
    "fieldCodes",
    "actionIds",
)

FORBIDDEN_BOUNDARY_TOKENS = (
    "role_code",
    "roleSurface",
    "default_route",
    "permissions",
    "permission",
    "groups",
    "capability",
    "router",
    "window.location",
    "localStorage",
    "sessionStorage",
    "fetch(",
    "axios",
    "/odoo",
    "jsonrpc",
)

REQUIRED_MAKEFILE_TOKENS = (
    "verify.unified_page_contract.lite.terminal_consumer_boundary",
    "unified_page_contract_lite_terminal_consumer_boundary_guard.py",
)

REQUIRED_STORE_TOKENS = (
    "createLiteTerminalContractStore",
    "parseLiteTerminalContract",
    "setFromContract",
    "snapshot",
    "LiteTerminalConsumerBoundary",
)

REQUIRED_RENDERER_INPUT_TOKENS = (
    "LiteTerminalRendererInput",
    "LiteTerminalRendererInputSnapshot",
    "createLiteTerminalRendererInput",
    "createLiteTerminalRendererInputSnapshot",
    "LiteTerminalContractStoreSnapshot",
    "widgetCount",
    "fieldCount",
    "actionCount",
)

REQUIRED_RENDERER_TOKENS = (
    "LiteTerminalRendererOutput",
    "LiteTerminalRendererOutputSnapshot",
    "createLiteTerminalRendererOutput",
    "createLiteTerminalRendererOutputSnapshot",
    "LiteTerminalRendererInput",
    "fieldNodeCount",
    "actionNodeCount",
)

REQUIRED_PAGE_INTEGRATION_TOKENS = (
    "LiteTerminalPageIntegration",
    "LiteTerminalPageIntegrationSnapshot",
    "createLiteTerminalPageIntegration",
    "createLiteTerminalPageIntegrationSnapshot",
    "LiteTerminalRendererOutput",
    "rootNodeId",
    "mountedNodeCount",
)

REQUIRED_RUNTIME_MOUNT_TOKENS = (
    "LiteTerminalRuntimeMount",
    "LiteTerminalRuntimeMountSnapshot",
    "createLiteTerminalRuntimeMount",
    "createLiteTerminalRuntimeMountSnapshot",
    "LiteTerminalPageIntegration",
    "mountedNodeCount",
    "status: 'mounted'",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    for path in (
        BOUNDARY_PATH,
        STORE_PATH,
        RENDERER_INPUT_PATH,
        RENDERER_PATH,
        PAGE_INTEGRATION_PATH,
        RUNTIME_MOUNT_PATH,
        BASE_CONTRACT_PATH,
        MAKEFILE_PATH,
    ):
        if not path.exists():
            errors.append(f"missing file: {path.relative_to(ROOT)}")

    boundary = read_text(BOUNDARY_PATH) if BOUNDARY_PATH.exists() else ""
    store = read_text(STORE_PATH) if STORE_PATH.exists() else ""
    renderer_input = read_text(RENDERER_INPUT_PATH) if RENDERER_INPUT_PATH.exists() else ""
    renderer = read_text(RENDERER_PATH) if RENDERER_PATH.exists() else ""
    page_integration = read_text(PAGE_INTEGRATION_PATH) if PAGE_INTEGRATION_PATH.exists() else ""
    runtime_mount = read_text(RUNTIME_MOUNT_PATH) if RUNTIME_MOUNT_PATH.exists() else ""
    base_contract = read_text(BASE_CONTRACT_PATH) if BASE_CONTRACT_PATH.exists() else ""
    makefile = read_text(MAKEFILE_PATH) if MAKEFILE_PATH.exists() else ""

    for token in REQUIRED_BOUNDARY_TOKENS:
        if token not in boundary:
            errors.append(f"boundary missing token: {token}")
    forbidden = sorted(token for token in FORBIDDEN_BOUNDARY_TOKENS if token in boundary)
    if forbidden:
        errors.append(f"boundary contains forbidden semantic/runtime tokens: {forbidden}")
    for token in REQUIRED_STORE_TOKENS:
        if token not in store:
            errors.append(f"store missing token: {token}")
    store_forbidden = sorted(token for token in FORBIDDEN_BOUNDARY_TOKENS if token in store)
    if store_forbidden:
        errors.append(f"store contains forbidden semantic/runtime tokens: {store_forbidden}")
    for token in REQUIRED_RENDERER_INPUT_TOKENS:
        if token not in renderer_input:
            errors.append(f"renderer input missing token: {token}")
    renderer_forbidden = sorted(token for token in FORBIDDEN_BOUNDARY_TOKENS if token in renderer_input)
    if renderer_forbidden:
        errors.append(f"renderer input contains forbidden semantic/runtime tokens: {renderer_forbidden}")
    for token in REQUIRED_RENDERER_TOKENS:
        if token not in renderer:
            errors.append(f"renderer missing token: {token}")
    renderer_output_forbidden = sorted(token for token in FORBIDDEN_BOUNDARY_TOKENS if token in renderer)
    if renderer_output_forbidden:
        errors.append(f"renderer contains forbidden semantic/runtime tokens: {renderer_output_forbidden}")
    for token in REQUIRED_PAGE_INTEGRATION_TOKENS:
        if token not in page_integration:
            errors.append(f"page integration missing token: {token}")
    page_integration_forbidden = sorted(token for token in FORBIDDEN_BOUNDARY_TOKENS if token in page_integration)
    if page_integration_forbidden:
        errors.append(f"page integration contains forbidden semantic/runtime tokens: {page_integration_forbidden}")
    for token in REQUIRED_RUNTIME_MOUNT_TOKENS:
        if token not in runtime_mount:
            errors.append(f"runtime mount missing token: {token}")
    runtime_mount_forbidden = sorted(token for token in FORBIDDEN_BOUNDARY_TOKENS if token in runtime_mount)
    if runtime_mount_forbidden:
        errors.append(f"runtime mount contains forbidden semantic/runtime tokens: {runtime_mount_forbidden}")

    if "export type LiteClientType = 'web_pc' | 'wx_mini' | 'harmony_h5';" not in base_contract:
        errors.append("base Lite contract does not expose the three supported terminal clients")
    if "export function isUnifiedPageContractLite" not in base_contract:
        errors.append("base Lite contract validator is missing")

    for token in REQUIRED_MAKEFILE_TOKENS:
        if token not in makefile:
            errors.append(f"Makefile missing token: {token}")

    frontend_contract_files = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "frontend").rglob("*Lite*.ts")
        if "node_modules" not in path.parts
    )
    unexpected_terminal_contracts = [
        path for path in frontend_contract_files
        if path.endswith("unifiedPageContractLiteTerminal.ts") is False
        and path.endswith("unifiedPageContractLiteTerminalStore.ts") is False
        and path.endswith("unifiedPageContractLiteTerminalRendererInput.ts") is False
        and path.endswith("unifiedPageContractLiteTerminalRenderer.ts") is False
        and path.endswith("unifiedPageContractLiteTerminalPageIntegration.ts") is False
        and path.endswith("unifiedPageContractLiteTerminalRuntimeMount.ts") is False
        and path.endswith("unifiedPageContractLite.ts") is False
        and "unifiedPageContractLitePilot.ts" not in path
    ]
    if unexpected_terminal_contracts:
        errors.append(f"unexpected Lite terminal contract files: {unexpected_terminal_contracts}")

    report = {
        "ok": not errors,
        "boundary": BOUNDARY_PATH.relative_to(ROOT).as_posix(),
        "store": STORE_PATH.relative_to(ROOT).as_posix(),
        "rendererInput": RENDERER_INPUT_PATH.relative_to(ROOT).as_posix(),
        "renderer": RENDERER_PATH.relative_to(ROOT).as_posix(),
        "pageIntegration": PAGE_INTEGRATION_PATH.relative_to(ROOT).as_posix(),
        "runtimeMount": RUNTIME_MOUNT_PATH.relative_to(ROOT).as_posix(),
        "baseContract": BASE_CONTRACT_PATH.relative_to(ROOT).as_posix(),
        "frontendLiteFiles": frontend_contract_files,
        "policy": "shared_terminal_consumer_boundary_only",
        "errors": errors,
    }
    write_report(args.report, report)

    if errors:
        print("Unified Semantic Page Contract Lite terminal consumer boundary guard failed:")
        for error in errors:
            print(f"- {error}")
        print(f"- report: {args.report}")
        return 1

    print("Unified Semantic Page Contract Lite terminal consumer boundary guard passed")
    print("- policy: shared_terminal_consumer_boundary_only")
    print(f"- report: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
