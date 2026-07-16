#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# These files and directories form the reusable product surface. Business
# packages may carry industry semantics; the shared renderer may not.
PROTECTED_FILES = (
    ROOT / "frontend/apps/web/src/layouts/AppShell.vue",
    ROOT / "frontend/apps/web/src/views/HomeView.vue",
)
PROTECTED_DIRS = (
    ROOT / "frontend/apps/web/src/components/page",
    ROOT / "frontend/apps/web/src/components/product-shell",
    ROOT / "frontend/apps/web/src/components/role-home",
    ROOT / "frontend/apps/web/src/app/shared-surface",
    ROOT / "frontend/apps/web/src/composables/shared-surface",
)

RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "role-presentation-map",
        re.compile(r"(?:ROLE|role)[A-Za-z_]*(?:LABEL|TITLE|PRESENTATION|HOME)[A-Za-z_]*\s*(?::[^=]+)?=\s*[{[]"),
        "共享层不得维护角色到标题、说明或首页内容的映射。",
    ),
    (
        "business-domain-map",
        re.compile(r"(?:DOMAIN|domain)[A-Za-z_]*(?:LABEL|GROUP|MAP|BY_)[A-Za-z_]*\s*(?::[^=]+)?=\s*[{[]"),
        "共享层不得维护菜单分组到业务域的映射。",
    ),
    (
        "role-code-branch",
        re.compile(r"(?:role_code|roleCode|role)\s*(?:===|==|includes\(|startsWith\(|match\(|\.test\()"),
        "共享层不得按角色码分支。",
    ),
    (
        "model-branch",
        re.compile(r"(?:model|res_model)\s*(?:===|==|!==|!=|includes\(|startsWith\(|match\(|\.test\()"),
        "共享层不得按业务模型分支。",
    ),
    (
        "metadata-business-inference",
        re.compile(r"(?:sceneKey|scene_key|groupKey|group_key|zoneKey|zone_key|zone|xmlid|xml_id)\s*\.?(?:includes|startsWith|match)\("),
        "共享层不得从 scene/group/zone/XML ID 推导业务语义。",
    ),
    (
        "route-metadata-presentation-map",
        re.compile(r"\[[^\]]*['\"][^'\"]+['\"][^\]]*\]\.includes\(String\(routeSceneKey", re.DOTALL),
        "共享层不得用场景键清单决定页面展示方式。",
    ),
    (
        "industry-literal",
        re.compile(r"['\"`]([^'\"`]*(?:项目|合同|结算|付款|财务|经营|施工|税务)[^'\"`]*)['\"`]"),
        "共享层不得硬编码行业标题、说明或 fallback。",
    ),
    (
        "business-identifier-literal",
        re.compile(r"['\"`][^'\"`]*(?:smart_construction|project\.project|payment[._-]|settlement[._-]|finance[._-]|construction\.)[^'\"`]*['\"`]"),
        "共享层不得硬编码行业模块、模型或 XML ID。",
    ),
)


def source_files() -> list[Path]:
    files = [path for path in PROTECTED_FILES if path.is_file()]
    for directory in PROTECTED_DIRS:
        if not directory.is_dir():
            continue
        files.extend(path for path in directory.rglob("*") if path.suffix in {".ts", ".vue"})
    return sorted(set(files))


def main() -> int:
    findings: list[tuple[str, str, int, str]] = []
    for path in source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for rule_id, pattern, message in RULES:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append((rule_id, rel, line, message))

    if findings:
        print("[frontend_shared_surface_semantic_boundary_guard] FAIL")
        for rule_id, rel, line, message in findings:
            print(f"- {rel}:{line} [{rule_id}] {message}")
        return 1

    shell_text = (ROOT / "frontend/apps/web/src/layouts/AppShell.vue").read_text(encoding="utf-8")
    if "isPlatformAdmin.value && hudEnabled.value" not in shell_text:
        print("[frontend_shared_surface_semantic_boundary_guard] FAIL")
        print("- frontend/apps/web/src/layouts/AppShell.vue [diagnostic-admin-boundary] 诊断界面必须同时受平台管理员身份约束。")
        return 1

    print("[frontend_shared_surface_semantic_boundary_guard] PASS")
    print(f"files_scanned={len(source_files())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
