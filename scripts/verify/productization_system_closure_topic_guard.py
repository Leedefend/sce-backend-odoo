#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "product" / "productization_system_closure_topic_v1.md"
MAKEFILE = ROOT / "Makefile"

REQUIRED_DOC_TOKENS = [
    "topic/productization-system-closure",
    "用户体验",
    "后端契约边界",
    "低代码配置边界",
    "业务办理闭环",
    "附件闭环",
    "发布链路",
    "项目隔离契约由后端输出",
    "前端只消费后端契约",
    "菜单配置展示口径必须与主导航展示口径一致",
    "Header、Toolbar、Summary、Main Surface、Primary Actions、Feedback Layer",
    "make verify.system_user_experience.quick",
    "make verify.business_config.unit",
    "make verify.business_config.config_workbench_operation_quick",
    "make verify.business_config.full_acceptance",
    "make verify.system_user_experience.visible_surface_visual_coverage",
    "make verify.system_user_experience.full_browser",
    "make verify.business_system.usability_readiness",
    "make verify.production_git.authority.guard",
    "make verify.project_context.selector_product_boundary.guard.prod",
    "make verify.business_system.usability_readiness.prod",
]

REQUIRED_MAKE_TARGETS = [
    "verify.productization.system_closure.topic_guard",
    "verify.system_user_experience.quick",
    "verify.system_user_experience.visible_surface_visual_coverage",
    "verify.system_user_experience.full_browser",
    "verify.business_system.usability_readiness",
    "verify.production_git.authority.guard",
    "verify.business_system.usability_readiness.prod",
    "verify.project_context.selector_product_boundary.guard.prod",
    "verify.frontend.product_language.guard",
]

REQUIRED_QUICK_DEPS = [
    "verify.productization.system_closure.topic_guard",
    "verify.system_user_experience.coverage_guard",
    "verify.frontend.product_language.guard",
    "verify.frontend.config_workbench_navigation_boundary.guard",
    "verify.project_context.selector_product_boundary.guard",
    "verify.product.page_structure",
]

REQUIRED_TARGET_DEPS = {
    "verify.business_config.unit": [
        "verify.frontend.product_language.guard",
    ],
    "verify.business_config.config_workbench_operation_quick": [
        "verify.frontend.product_language.guard",
    ],
    "verify.business_system.usability_readiness": [
        "guard.prod.forbid",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.business_system.usability_readiness.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.project_context.selector_product_boundary.guard.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.system_user_experience.full_browser": [
        "verify.system_user_experience.coverage_guard",
        "verify.product.page_structure",
        "verify.business_config.config_workbench_operation_acceptance",
        "verify.business_config.config_workbench_operation_summary_guard",
        "verify.system_user_experience.shell_acceptance",
        "verify.system_user_experience.visible_surface_visual_coverage",
        "verify.system_user_experience.business_form_user_perspective",
    ],
}

REQUIRED_TARGET_BODY_TOKENS = {
    "verify.business_system.usability_readiness": [
        'BUSINESS_SYSTEM_READINESS_INCLUDE_P1="$(BUSINESS_SYSTEM_READINESS_INCLUDE_P1)"',
        "scripts/ops/validate_business_system_usability_readiness.sh",
    ],
    "verify.business_system.usability_readiness.prod": [
        "BUSINESS_SYSTEM_READINESS_PROD_READONLY=1",
        "BUSINESS_SYSTEM_READINESS_INCLUDE_P1=0",
        "scripts/ops/validate_business_system_usability_readiness.sh",
    ],
    "verify.project_context.selector_product_boundary.guard.prod": [
        "python3 -m py_compile scripts/verify/project_context_selector_product_boundary_guard.py",
        "PROD_READONLY_VERIFY=1",
        "scripts/verify/project_context_selector_product_boundary_guard.py",
    ],
    "verify.system_user_experience.shell_acceptance": [
        "scripts/system_user_experience_shell_acceptance.mjs",
        "scripts/system_user_experience_shell_summary_guard.mjs",
    ],
    "verify.system_user_experience.business_form_user_perspective": [
        "frontend/apps/web/scripts/business_form_user_perspective_acceptance.mjs",
        "scripts/business_form_user_perspective_summary_guard.mjs",
    ],
    "verify.system_user_experience.visible_surface_visual_coverage": [
        "frontend/apps/web/scripts/user_page_visual_coverage.cjs",
        "scripts/user_visible_surface_visual_coverage_summary_guard.mjs",
    ],
    "verify.system_user_experience.full_browser": [
        "scripts/system_user_experience_full_browser_summary_guard.mjs",
    ],
}


def _target_line(text: str, target: str) -> str:
    pattern = re.compile(rf"^{re.escape(target)}\s*:(?P<deps>[^\n]*)$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(0) if match else ""


def _target_body(text: str, target: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(target)}\s*:[^\n]*\n(?P<body>(?:\t[^\n]*\n|[ \t]*\n)*)",
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group("body") if match else ""


def main() -> int:
    errors: list[str] = []
    doc_text = DOC.read_text(encoding="utf-8") if DOC.is_file() else ""
    make_text = MAKEFILE.read_text(encoding="utf-8") if MAKEFILE.is_file() else ""

    if not doc_text:
        errors.append(f"missing doc: {DOC.relative_to(ROOT)}")
    if not make_text:
        errors.append("missing Makefile")

    for token in REQUIRED_DOC_TOKENS:
        if token not in doc_text:
            errors.append(f"doc missing token: {token}")

    for target in REQUIRED_MAKE_TARGETS:
        if not _target_line(make_text, target):
            errors.append(f"Makefile missing target: {target}")

    quick_line = _target_line(make_text, "verify.system_user_experience.quick")
    for dep in REQUIRED_QUICK_DEPS:
        if dep not in quick_line:
            errors.append(f"quick gate missing dependency: {dep}")

    for target, deps in REQUIRED_TARGET_DEPS.items():
        target_line = _target_line(make_text, target)
        if not target_line:
            errors.append(f"Makefile missing target: {target}")
            continue
        for dep in deps:
            if dep not in target_line:
                errors.append(f"{target} missing dependency: {dep}")

    for target, tokens in REQUIRED_TARGET_BODY_TOKENS.items():
        target_body = _target_body(make_text, target)
        if not target_body:
            errors.append(f"Makefile missing command body: {target}")
            continue
        for token in tokens:
            if token not in target_body:
                errors.append(f"{target} missing command token: {token}")

    topic_line = _target_line(make_text, "verify.productization.system_closure.topic_guard")
    if topic_line and "guard.prod.forbid" not in topic_line:
        errors.append("topic guard must use guard.prod.forbid")

    result = {
        "guard": "productization_system_closure_topic_guard",
        "status": "FAIL" if errors else "PASS",
        "doc": str(DOC.relative_to(ROOT)),
        "errors": errors,
        "required_doc_tokens": len(REQUIRED_DOC_TOKENS),
        "required_make_targets": len(REQUIRED_MAKE_TARGETS),
        "required_quick_dependencies": len(REQUIRED_QUICK_DEPS),
        "required_target_dependencies": sum(len(deps) for deps in REQUIRED_TARGET_DEPS.values()),
        "required_target_body_tokens": sum(len(tokens) for tokens in REQUIRED_TARGET_BODY_TOKENS.values()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
