#!/usr/bin/env python3
"""Guard user-facing low-code business config wording.

This guard intentionally checks only phrases that have already been replaced in
the default user path. It does not ban technical identifiers such as
``ui.business.config.contract`` or advanced governance labels.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SCAN_PATHS = [
    ROOT / "frontend/apps/web/src/views/BusinessConfigSurfaceView.vue",
    ROOT / "frontend/apps/web/src/views/MenuConfigView.vue",
    ROOT / "frontend/apps/web/src/views/WorkbenchView.vue",
    ROOT / "frontend/apps/web/src/views/ActionView.vue",
    ROOT / "frontend/apps/web/src/views/HomeView.vue",
    ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
    ROOT / "frontend/apps/web/src/pages/contractForm",
    ROOT / "frontend/apps/web/src/app",
    ROOT / "addons/smart_core/handlers",
    ROOT / "addons/smart_core/delivery",
    ROOT / "docs/low_code_config_capability_iteration.md",
    ROOT / "docs/low_code_config_capability_matrix.md",
]

BANNED_PHRASES = [
    "契约快照",
    "契约上下文",
    "页面缺少契约",
    "当前契约",
    "调度契约",
    "业务契约",
    "契约缺口",
    "缺契约",
    "发布契约",
    "补齐契约",
    "生成基础配置",
    "暂无菜单配置版本",
    "适用用户组",
]

REQUIRED_CONTRACT_FORM_SNIPPETS = [
    "function readableFallbackFieldLabel(fieldKey: string)",
    "return rowLabel || readableFallbackFieldLabel(key);",
]

FORBIDDEN_CONTRACT_FORM_SNIPPETS = [
    "return rowLabel || key;",
]

TEXT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".md"}


def iter_files(path: Path):
    if path.is_file():
        yield path
        return
    if not path.exists():
        return
    for item in path.rglob("*"):
        if item.is_file() and item.suffix in TEXT_EXTENSIONS:
            yield item


def main() -> int:
    violations = []
    for scan_path in SCAN_PATHS:
        for file_path in iter_files(scan_path):
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                for phrase in BANNED_PHRASES:
                    if phrase in line:
                        violations.append((file_path.relative_to(ROOT), line_no, phrase, line.strip()))

    if violations:
        print("[business_config_user_language_guard] FAIL")
        for file_path, line_no, phrase, line in violations:
            print(f" - {file_path}:{line_no}: banned phrase {phrase!r}: {line}")
        return 1

    contract_form_sources = [
        ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
        ROOT / "frontend/apps/web/src/pages/contractForm/formConfigHelpers.ts",
    ]
    contract_form_text = "\n".join(path.read_text(encoding="utf-8") for path in contract_form_sources)
    snippet_violations = []
    for snippet in REQUIRED_CONTRACT_FORM_SNIPPETS:
        if snippet not in contract_form_text:
            snippet_violations.append(f"missing required contract form snippet: {snippet}")
    for snippet in FORBIDDEN_CONTRACT_FORM_SNIPPETS:
        if snippet in contract_form_text:
            snippet_violations.append(f"forbidden contract form snippet: {snippet}")
    if snippet_violations:
        print("[business_config_user_language_guard] FAIL")
        for violation in snippet_violations:
            print(" - " + violation)
        return 1

    print("[business_config_user_language_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
