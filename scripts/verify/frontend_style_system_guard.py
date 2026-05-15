#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "frontend/apps/web/src"
MAIN_TS = WEB_SRC / "main.ts"
DESIGN_SYSTEM = WEB_SRC / "styles/design-system.css"
PRODUCT_PATTERNS = WEB_SRC / "styles/product-patterns.css"
THEME_RUNTIME = WEB_SRC / "styles/theme.ts"

HARDCODE_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")
MAX_EXISTING_HARDCODE_COLOR_REFS = 0


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _fail(errors: list[str]) -> int:
    print("[frontend_style_system_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _check_required_file(path: Path, errors: list[str]) -> str:
    text = _read(path)
    if not text:
        errors.append(f"missing or empty file: {_rel(path)}")
    return text


def _check_sfc_style_tail(errors: list[str]) -> None:
    for path in sorted(WEB_SRC.rglob("*.vue")):
        text = _read(path)
        close_index = text.rfind("</style>")
        if close_index < 0:
            continue
        tail = text[close_index + len("</style>") :].strip()
        if tail:
            preview = " ".join(tail.split())[:120]
            errors.append(f"{_rel(path)} has non-empty content after final </style>: {preview}")


def _check_style_bootstrap(errors: list[str]) -> None:
    main_text = _check_required_file(MAIN_TS, errors)
    for token in [
        "import './styles/design-system.css';",
        "import './styles/product-patterns.css';",
        "import { bootTheme } from './styles/theme';",
        "bootTheme();",
    ]:
        if token not in main_text:
            errors.append(f"{_rel(MAIN_TS)} missing style bootstrap token: {token}")

    design_text = _check_required_file(DESIGN_SYSTEM, errors)
    for token in [
        "@import '../../../../packages/design-tokens/dist/web/tokens.light.css';",
        "@import '../../../../packages/design-tokens/dist/web/tokens.dark.css';",
        "--sc-app-bg: var(--sc-semantic-surface-page);",
        "--sc-app-panel: var(--sc-semantic-surface-panel);",
        "--sc-app-text-primary: var(--sc-semantic-text-primary);",
        "--sc-app-text-secondary: var(--sc-semantic-text-secondary);",
        "--sc-app-border: var(--sc-semantic-border-default);",
        "--sc-app-border-strong: var(--sc-semantic-border-strong);",
        "--sc-app-muted-bg: var(--sc-semantic-surface-panel-muted);",
        "--sc-app-shadow: var(--sc-semantic-shadow-panel);",
        "--sc-app-focus-ring: var(--sc-semantic-focus-ring);",
        "--sc-app-danger-bg: var(--sc-semantic-state-danger-bg);",
        ':root[data-sc-theme="dark"]',
    ]:
        if token not in design_text:
            errors.append(f"{_rel(DESIGN_SYSTEM)} missing design-system token: {token}")

    product_text = _check_required_file(PRODUCT_PATTERNS, errors)
    for token in [
        ".sc-page",
        ".sc-panel",
        ".sc-toolbar",
        ".sc-action-group",
        ".sc-form-label",
        ".sc-btn",
        ".sc-btn-primary",
        ".sc-tag",
        ".sc-badge",
        ".sc-alert",
        ".sc-empty",
        ".sc-table-shell",
        ".sc-dialog",
    ]:
        if token not in product_text:
            errors.append(f"{_rel(PRODUCT_PATTERNS)} missing product pattern: {token}")

    theme_text = _check_required_file(THEME_RUNTIME, errors)
    for token in [
        "data-sc-theme-mode",
        "data-sc-theme-resolved",
        "data-sc-theme",
        "prefers-color-scheme: dark",
        "localStorage.getItem(THEME_KEY)",
    ]:
        if token not in theme_text:
            errors.append(f"{_rel(THEME_RUNTIME)} missing theme runtime token: {token}")


def _check_hardcoded_color_baseline(errors: list[str]) -> None:
    total = 0
    by_file: list[tuple[int, Path]] = []
    for path in sorted(WEB_SRC.rglob("*")):
        if path.suffix not in {".vue", ".css"}:
            continue
        count = len(HARDCODE_COLOR_RE.findall(_read(path)))
        if count:
            by_file.append((count, path))
            total += count

    if total > MAX_EXISTING_HARDCODE_COLOR_REFS:
        top = ", ".join(f"{_rel(path)}={count}" for count, path in sorted(by_file, reverse=True)[:8])
        errors.append(
            "hardcoded color reference count increased: "
            f"{total} > {MAX_EXISTING_HARDCODE_COLOR_REFS}; top files: {top}"
        )


def main() -> int:
    errors: list[str] = []
    if not WEB_SRC.is_dir():
        return _fail([f"missing directory: {_rel(WEB_SRC)}"])

    _check_sfc_style_tail(errors)
    _check_style_bootstrap(errors)
    _check_hardcoded_color_baseline(errors)

    if errors:
        return _fail(errors)

    print("[frontend_style_system_guard] PASS")
    print(f"hardcoded_color_refs_max={MAX_EXISTING_HARDCODE_COLOR_REFS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
