#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MENU_TREE = ROOT / "frontend" / "apps" / "web" / "src" / "components" / "MenuTree.vue"
APP_SHELL = ROOT / "frontend" / "apps" / "web" / "src" / "layouts" / "AppShell.vue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, needle: str, *, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")


def main() -> int:
    menu_tree = _read(MENU_TREE)
    app_shell = _read(APP_SHELL)

    _require(menu_tree, "function onSelect(node: ExplainedMenuNode)", label="menu onSelect")
    _require(menu_tree, "if (isNodeDisabled(node))", label="disabled click block")
    _require(menu_tree, "if (node.target_type === 'directory' && node.children?.length)", label="directory toggle rule")
    _require(menu_tree, "toggle(nodeKey(node));", label="directory toggle action")
    _require(menu_tree, "emit('select', node);", label="select emit")

    _require(menu_tree, "function ensureExpandedForActive", label="active chain expander")
    _require(menu_tree, "session.ensureMenuExpanded", label="active expansion sync")
    _require(menu_tree, "if (node.target_type === 'unavailable')", label="unavailable tooltip")

    _require(app_shell, "function navigateByExplainedMenuNode(node: ExplainedMenuNode)", label="unified navigation dispatcher")
    _require(app_shell, "if (!node.is_clickable)", label="clickability block")
    _require(app_shell, "node.target_type === 'directory' || node.target_type === 'unavailable'", label="directory/unavailable block")
    _require(app_shell, "const routePath = asText(node.route);", label="explained route consumption")

    print("[verify.frontend.sidebar.interaction_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

