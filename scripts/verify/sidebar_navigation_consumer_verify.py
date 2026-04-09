#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_SHELL = ROOT / "frontend" / "apps" / "web" / "src" / "layouts" / "AppShell.vue"
MENU_TREE = ROOT / "frontend" / "apps" / "web" / "src" / "components" / "MenuTree.vue"
COMPOSABLE = ROOT / "frontend" / "apps" / "web" / "src" / "composables" / "useNavigationMenu.ts"


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
    composable = _read(COMPOSABLE)

    _require(app_shell, "useNavigationMenu", label="sidebar navigation source")
    _require(composable, "/api/menu/navigation", label="navigation endpoint")
    _require(app_shell, "navigateByExplainedMenuNode", label="unified navigation dispatcher")
    _require(menu_tree, "ExplainedMenuNode", label="explained menu typing")

    _forbid(app_shell, "buildSceneRegistryFallbackPath", label="legacy scene fallback")
    _forbid(app_shell, "resolveSceneKeyFromNode", label="legacy scene inference")
    _forbid(app_shell, "node.meta?.route", label="legacy meta route derivation")
    _forbid(app_shell, "`/m/${", label="legacy menu id fallback route")

    print("[verify.frontend.sidebar.navigation_consumer] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
