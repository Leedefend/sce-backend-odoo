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
    "make verify.system_user_experience.full_browser",
    "make verify.business_system.usability_readiness",
    "make verify.business_system.usability_readiness.prod",
]

REQUIRED_MAKE_TARGETS = [
    "verify.productization.system_closure.topic_guard",
    "verify.system_user_experience.quick",
    "verify.system_user_experience.full_browser",
    "verify.business_system.usability_readiness",
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


def _target_line(text: str, target: str) -> str:
    pattern = re.compile(rf"^{re.escape(target)}\s*:(?P<deps>[^\n]*)$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(0) if match else ""


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
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
