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

    _require(menu_tree, "return node.target_type === 'unavailable';", label="unavailable disabled")
    _require(menu_tree, "if (node.target_type === 'unavailable')", label="unavailable title")
    _require(app_shell, "node.target_type === 'directory' || node.target_type === 'unavailable'", label="dispatcher unavailable block")
    _require(app_shell, "if (!node.is_clickable)", label="clickable guard")
    _require(app_shell, "const routePath = asText(node.route);", label="route from explained node")

    print("[verify.frontend.sidebar.unavailable_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

