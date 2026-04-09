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


def _forbid(text: str, needle: str, *, label: str) -> None:
    if needle in text:
        raise AssertionError(f"forbidden {label}: {needle}")


def main() -> int:
    menu_tree = _read(MENU_TREE)
    app_shell = _read(APP_SHELL)

    _require(menu_tree, "node.target_type === 'directory'", label="directory branch")
    _require(menu_tree, "toggle(nodeKey(node));", label="directory toggle")
    _require(menu_tree, "emit('select', node);", label="select emit")
    _require(app_shell, "node.target_type === 'directory'", label="directory block in dispatcher")

    _forbid(menu_tree, "emit('select', node);\n    return;\n  }\n  if (node.target_type === 'directory'", label="emit before directory block")

    print("[verify.frontend.sidebar.directory_rule] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

