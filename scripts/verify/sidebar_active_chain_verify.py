#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_SHELL = ROOT / "frontend" / "apps" / "web" / "src" / "layouts" / "AppShell.vue"
MENU_TREE = ROOT / "frontend" / "apps" / "web" / "src" / "components" / "MenuTree.vue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(text: str, needle: str, *, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")


def _forbid(text: str, needle: str, *, label: str) -> None:
    if needle in text:
        raise AssertionError(f"forbidden {label}: {needle}")


def main() -> int:
    app_shell = _read(APP_SHELL)
    menu_tree = _read(MENU_TREE)

    _require(app_shell, "const currentRouteContext = computed", label="route context")
    _require(app_shell, "node.active_match", label="active_match usage")
    _require(app_shell, "function matchesActiveNode", label="active matcher")
    _require(app_shell, "function findActiveMenuId", label="active id resolver")
    _require(app_shell, "const activeMenuId = computed", label="active menu computed")
    _require(menu_tree, "ensureExpandedForActive", label="active parent expansion")
    _require(menu_tree, "session.ensureMenuExpanded", label="expanded sync")

    _forbid(app_shell, "route.fullPath.includes", label="legacy fullPath contains active")
    _forbid(app_shell, "route.path.includes", label="legacy path contains active")

    print("[verify.frontend.sidebar.active_chain] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

