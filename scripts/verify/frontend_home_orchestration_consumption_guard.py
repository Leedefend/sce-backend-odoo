#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
HOME_ORCHESTRATION = ROOT / "frontend/apps/web/src/app/homeOrchestration.ts"
SESSION_STORE = ROOT / "frontend/apps/web/src/stores/session.ts"
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_home_orchestration_consumption_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _expect(text: str, scope: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{scope} missing token: {token}")


def main() -> int:
    home_text = _read(HOME_VIEW)
    home_orchestration_text = _read(HOME_ORCHESTRATION)
    session_text = _read(SESSION_STORE)
    builder_text = _read(HOME_BUILDER)
    errors: list[str] = []

    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")
    if not session_text:
        errors.append(f"missing file: {SESSION_STORE.relative_to(ROOT).as_posix()}")
    if not home_orchestration_text:
        errors.append(f"missing file: {HOME_ORCHESTRATION.relative_to(ROOT).as_posix()}")
    if not builder_text:
        errors.append(f"missing file: {HOME_BUILDER.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    _expect(
        session_text,
        "session.ts",
        [
            "semantic_protocol?: {",
            "page_orchestration_v1?: {",
            "page_orchestration?: {",
            "role_variant?: {",
        ],
        errors,
    )
    _expect(
        home_text,
        "HomeView.vue",
        [
            "const workspacePageOrchestration = computed(() => (",
            "const workspacePageOrchestrationV1 = computed(() => (",
            "const workspacePageOrchestrationV1DataSources = computed(() => (",
            "const orchestrationBlocks = computed(() => {",
            "flattenHomeOrchestrationBlocks(",
            "workspacePageOrchestrationV1DataSources.value",
            "const orchestrationSectionOrderMap = computed(() => orchestrationSectionDerived.value.orderMap);",
            "const orchestrationSectionSemanticMap = computed(() => orchestrationSectionDerived.value.semanticMap);",
            "const roleVariantCode = computed(() => {",
            "const orchestrationPage = workspacePageOrchestrationV1.value.page;",
            "function homeSectionClass(key: string) {",
            "orchestrationSectionOrderMap.value.get(key)",
            ":class=\"homeSectionClass('hero')\"",
            ":class=\"homeSectionClass('metrics')\"",
            ":class=\"homeSectionClass('today_actions')\"",
            ":class=\"homeSectionClass('risk')\"",
            "HUD: orchestration_blocks={{ orchestrationBlocks.length }} · role_variant={{ roleVariantCode || '-' }}",
            "normalizeTone(row.tone)",
            "normalizeProgress(row.progress)",
        ],
        errors,
    )
    _expect(
        home_orchestration_text,
        "homeOrchestration.ts",
        [
            "export function flattenHomeOrchestrationBlocks(",
            "const zones = Array.isArray(pageOrchestrationV1.zones)",
            "const hasV1Zones = zones.length > 0;",
            "const dataSourceKey = toText(blockRow.data_source);",
            "const dataSource = dataSources[dataSourceKey];",
            "const sourceType = toText((dataSource as Record<string, unknown>).source_type);",
            "if (hasV1Zones) return flattenedV1;",
        ],
        errors,
    )
    _expect(
        builder_text,
        "workspace_home_contract_builder.py",
        [
            '"semantic_protocol": {',
            '"page_orchestration_v1": _build_page_orchestration_v1(role_code)',
            '"page_orchestration": _build_page_orchestration(role_code)',
            '"role_variant": {',
        ],
        errors,
    )

    if errors:
        return _fail(errors)

    print("[frontend_home_orchestration_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
