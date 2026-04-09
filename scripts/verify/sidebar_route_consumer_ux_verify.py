#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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
    app_shell = _read(APP_SHELL)

    _require(app_shell, "const routePath = node.is_clickable", label="breadcrumb route gating")
    _require(app_shell, "asText(node.route)", label="breadcrumb consume explained route")
    _require(app_shell, "function findMenuNodeById", label="role shortcut node resolver")
    _require(app_shell, "navigateByExplainedMenuNode(node);", label="role shortcut unified dispatch")

    _forbid(app_shell, "router.push(`/m/${menuId}`)", label="role shortcut legacy /m route")
    _forbid(app_shell, "crumbs.push({ label, to: `/m/${id}` });", label="breadcrumb legacy /m route")

    print("[verify.frontend.sidebar.route_consumer_ux] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

