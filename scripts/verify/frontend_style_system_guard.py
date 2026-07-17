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
DESIGN_COMPONENTS = WEB_SRC / "components/design-system"
FORM_SECTION = WEB_SRC / "components/template/FormSection.vue"

REQUIRED_PRODUCT_COMPONENTS = {
    "ScPage.vue", "ScPageHeader.vue", "ScSection.vue", "ScPanel.vue", "ScIcon.vue",
    "ScButton.vue", "ScIconButton.vue", "ScStatusBadge.vue", "ScMoney.vue",
    "ScField.vue", "ScSelect.vue", "ScRelationField.vue", "ScDateField.vue",
    "ScErrorSummary.vue", "ScEmptyState.vue", "ScErrorState.vue", "ScDialog.vue",
    "ScDrawer.vue", "ScActionBar.vue", "ScDataTable.vue", "ScMobileRecordCard.vue",
    "ScRelationshipFlow.vue", "ScAuditTrail.vue",
}

REQUIRED_PRODUCT_CONSUMERS = {
    "ScActionBar": "components/business/MyWorkApprovalWorkspace.vue",
    "ScAuditTrail": "components/product-record/ProductAuditSection.vue",
    "ScDataTable": "pages/ListPage.vue",
    "ScDateField": "components/template/FormSection.vue",
    "ScDialog": "pages/contractForm/RelationSearchDialog.vue",
    "ScEmptyState": "pages/ListPage.vue",
    "ScErrorState": "views/NotFoundView.vue",
    "ScField": "components/business/MyWorkApprovalWorkspace.vue",
    "ScIcon": "components/template/FormSection.vue",
    "ScMoney": "components/product-record/ProductFactGrid.vue",
    "ScPage": "pages/ListPage.vue",
    "ScPageHeader": "pages/ListPage.vue",
    "ScPanel": "components/product-record/ProductBusinessSections.vue",
    "ScRelationField": "components/template/FormSection.vue",
    "ScRelationshipFlow": "components/product-record/ProductRelationshipFlow.vue",
    "ScSection": "components/business/MyWorkApprovalWorkspace.vue",
    "ScSelect": "components/template/FormSection.vue",
    "ScStatusBadge": "components/product-record/ProductRecordStatus.vue",
}

GENERIC_BOUNDARY_RE = re.compile(
    r"\b(?:role_code|project_member|payment\.request|construction\.contract|"
    r"project\.project|sc\.settlement|sc\.payment|menu_[0-9]+|action_[0-9]+)\b",
    re.IGNORECASE,
)

SIZE_LIMITS = {
    WEB_SRC / "layouts/AppShell.vue": 1600,
    WEB_SRC / "pages/ListPage.vue": 2300,
    WEB_SRC / "pages/ContractFormPage.vue": 1800,
    WEB_SRC / "pages/ContractFormRoute.vue": 800,
    WEB_SRC / "views/ActionView.vue": 3684,
}

HARDCODE_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(")
DARK_CLASS_ENUMERATION_RE = re.compile(r"data-sc-theme\s*=\s*['\"]dark['\"][^{]*:is\(", re.IGNORECASE)
MIXED_ICON_GLYPH_RE = re.compile(r"[×→★☆↑↓✓⋮]")
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


def _check_product_component_boundary(errors: list[str]) -> None:
    if not DESIGN_COMPONENTS.is_dir():
        errors.append(f"missing design-system directory: {_rel(DESIGN_COMPONENTS)}")
        return
    present = {path.name for path in DESIGN_COMPONENTS.glob("*.vue")}
    for missing in sorted(REQUIRED_PRODUCT_COMPONENTS - present):
        errors.append(f"missing product component: {missing}")
    for path in sorted(DESIGN_COMPONENTS.glob("*")):
        if path.suffix not in {".vue", ".ts"}:
            continue
        match = GENERIC_BOUNDARY_RE.search(_read(path))
        if match:
            errors.append(f"{_rel(path)} crosses generic component boundary: {match.group(0)}")

    for component, relative_consumer in REQUIRED_PRODUCT_CONSUMERS.items():
        consumer = WEB_SRC / relative_consumer
        text = _check_required_file(consumer, errors)
        if f"<{component}" not in text:
            errors.append(f"{_rel(consumer)} does not consume required product component: {component}")

    for path in sorted(WEB_SRC.rglob("*")):
        if path.suffix not in {".vue", ".css"}:
            continue
        if DARK_CLASS_ENUMERATION_RE.search(_read(path)):
            errors.append(f"{_rel(path)} restores broad dark-theme class enumeration")
        if path.suffix == ".vue" and MIXED_ICON_GLYPH_RE.search(_read(path)):
            errors.append(f"{_rel(path)} mixes Unicode icon glyphs with the formal SVG icon system")


def _check_complexity_and_accessibility(errors: list[str]) -> None:
    for path, limit in SIZE_LIMITS.items():
        lines = len(_read(path).splitlines())
        if not lines:
            errors.append(f"missing complexity target: {_rel(path)}")
        elif lines > limit:
            errors.append(f"{_rel(path)} exceeds {limit} lines: {lines}")

    for path in sorted((WEB_SRC / "pages/contractForm").glob("useRecord*.ts")):
        lines = len(_read(path).splitlines())
        if lines > 500:
            errors.append(f"new record runtime exceeds 500 lines: {_rel(path)}={lines}")

    form_text = _check_required_file(FORM_SECTION, errors)
    for token in ['aria-required', 'aria-invalid', 'aria-describedby', 'data-field-key']:
        if token not in form_text:
            errors.append(f"{_rel(FORM_SECTION)} missing accessible field token: {token}")

    for retired in [WEB_SRC / "views/RecordView.vue", WEB_SRC / "pages/ModelFormPage.vue"]:
        if retired.exists():
            errors.append(f"retired compatibility delegate still exists: {_rel(retired)}")

    router_text = _read(WEB_SRC / "router/index.ts")
    if router_text.count("import('../pages/ContractFormRoute.vue')") != 2:
        errors.append("record and form routes must converge on ContractFormRoute.vue")


def main() -> int:
    errors: list[str] = []
    if not WEB_SRC.is_dir():
        return _fail([f"missing directory: {_rel(WEB_SRC)}"])

    _check_sfc_style_tail(errors)
    _check_style_bootstrap(errors)
    _check_hardcoded_color_baseline(errors)
    _check_product_component_boundary(errors)
    _check_complexity_and_accessibility(errors)

    if errors:
        return _fail(errors)

    print("[frontend_style_system_guard] PASS")
    print(f"hardcoded_color_refs_max={MAX_EXISTING_HARDCODE_COLOR_REFS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
