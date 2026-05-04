#!/usr/bin/env python3
"""Guard terminal shell v2 backend/frontend alignment."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SHELL_HANDLER = ROOT / "addons/smart_core/handlers/terminal_shell_v2.py"
MOBILE_HOME = ROOT / "frontend/apps/mobile/src/pages/home/index.vue"
CORS = ROOT / "addons/smart_core/controllers/intent_dispatcher.py"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def literal_assignments(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out[node.targets[0].id] = node.value.value
    return out


def main() -> int:
    errors: list[str] = []
    shell_source = SHELL_HANDLER.read_text(encoding="utf-8") if SHELL_HANDLER.exists() else ""
    home_source = MOBILE_HOME.read_text(encoding="utf-8") if MOBILE_HOME.exists() else ""
    cors_source = CORS.read_text(encoding="utf-8") if CORS.exists() else ""

    if not shell_source:
        fail(errors, "terminal.shell.v2 handler is required")
    else:
        tree = ast.parse(shell_source)
        assigns = literal_assignments(tree)
        if assigns.get("INTENT_TYPE") != "terminal.shell.v2":
            fail(errors, "terminal shell handler must declare INTENT_TYPE=terminal.shell.v2")
        for token in ("app.catalog", "app.nav", "app.open", "ui.contract.v2"):
            if token not in shell_source:
                fail(errors, f"terminal shell must align backend source intent {token}")
        for token in ("defaultEntry", "defaultOpenTarget", "deliveryProfile", "renderContractIntent"):
            if token not in shell_source:
                fail(errors, f"terminal shell data must include {token}")

    if "terminal.shell.v2" not in home_source:
        fail(errors, "mobile home must consume terminal.shell.v2")
    if "intent: 'app.catalog'" in home_source:
        fail(errors, "mobile home must not orchestrate app.catalog directly")
    if "app: 'project_management'" in home_source or 'app: "project_management"' in home_source:
        fail(errors, "mobile home must not hardcode business app id")
    if "X-SC-Client-Type" not in cors_source:
        fail(errors, "intent CORS must allow X-SC-Client-Type")

    if errors:
        print("terminal shell v2 contract guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("terminal shell v2 contract guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
