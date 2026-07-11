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
    "可重复验收证据",
    "项目隔离契约由后端输出",
    "前端只消费后端契约",
    "菜单配置展示口径必须与主导航展示口径一致",
    "分组菜单是导航组织能力",
    "真实可配置对象必须由后端契约明确给出",
    "不写回 Odoo 分组菜单",
    "Header、Toolbar、Summary、Main Surface、Primary Actions、Feedback Layer",
    "make verify.system_user_experience.quick",
    "make verify.business_config.unit",
    "make verify.business_config.config_workbench_operation_quick",
    "make verify.business_config.full_acceptance",
    "make verify.system_user_experience.visible_surface_visual_coverage",
    "make verify.system_user_experience.full_browser",
    "make verify.formal_business.release_gate",
    "make verify.business_capability.productization_p1",
    "make verify.business_system.usability_readiness",
    "make verify.production_git.authority.guard",
    "make verify.project_context.selector_product_boundary.guard.prod",
    "make verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "make verify.formal_list_surface.no_test_placeholder_guard.prod",
    "make verify.business_system.usability_readiness.prod",
    "make history.attachment.custody.probe.prod",
    "make verify.legacy_online_attachment.custody.evidence.prod",
    "make verify.legacy_attachment.frontend_browser.sample_manifest.prod",
    "make verify.attachment_upload.surface_manifest.prod",
]

REQUIRED_EVIDENCE_ARTIFACT_PATHS = [
    "artifacts/playwright/system-user-experience-full-browser/summary.json",
    "artifacts/playwright/config-workbench-operation/summary.json",
    "artifacts/playwright/business-form-user-perspective/summary.json",
    "artifacts/playwright/system-user-experience-shell/summary.json",
    "artifacts/backend/business_system_usability_readiness.json",
    "artifacts/product/full_product_capability_scope_v1.json",
    "artifacts/product/formal_business_operation_capability_matrix_v1.json",
    "artifacts/product/formal_business_operation_core_flow_smoke_v1.json",
    "docs/ops/releases/current/",
]

REQUIRED_CLOSEOUT_FIELDS = [
    "分支、提交、部署环境和版本",
    "覆盖的用户角色、页面类型、业务任务和低代码任务",
    "浏览器验收结果与结构化报告路径",
    "已修复的问题类型和仍保留的 backlog",
    "本地、日常开发服务器、生产服务器的验证结论",
    "是否具备交付用户使用的条件",
]

REQUIRED_DOC_TOKEN_GROUPS = {
    "doc": REQUIRED_DOC_TOKENS,
    "evidence_artifact": REQUIRED_EVIDENCE_ARTIFACT_PATHS,
    "closeout_field": REQUIRED_CLOSEOUT_FIELDS,
}

REQUIRED_MAKE_TARGETS = [
    "verify.productization.system_closure.topic_guard",
    "verify.system_user_experience.quick",
    "verify.system_user_experience.visible_surface_visual_coverage",
    "verify.system_user_experience.full_browser",
    "verify.business_config.unit",
    "verify.business_config.config_workbench_operation_quick",
    "verify.business_config.full_acceptance",
    "verify.formal_business.release_gate",
    "verify.business_capability.productization_p1",
    "verify.business_system.usability_readiness",
    "verify.production_git.authority.guard",
    "verify.business_system.usability_readiness.prod",
    "verify.project_context.selector_product_boundary.guard.prod",
    "verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "verify.formal_list_surface.no_test_placeholder_guard.prod",
    "history.attachment.custody.probe.prod",
    "verify.legacy_online_attachment.custody.evidence.prod",
    "verify.legacy_attachment.frontend_browser.sample_manifest.prod",
    "verify.attachment_upload.surface_manifest.prod",
    "verify.frontend.product_language.guard",
]

REQUIRED_DOC_DECLARED_MAKE_TARGETS = [
    "verify.system_user_experience.quick",
    "verify.business_config.unit",
    "verify.business_config.config_workbench_operation_quick",
    "verify.business_config.full_acceptance",
    "verify.system_user_experience.visible_surface_visual_coverage",
    "verify.system_user_experience.full_browser",
    "verify.formal_business.release_gate",
    "verify.business_capability.productization_p1",
    "verify.business_system.usability_readiness",
    "verify.production_git.authority.guard",
    "verify.project_context.selector_product_boundary.guard.prod",
    "verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "verify.formal_list_surface.no_test_placeholder_guard.prod",
    "verify.business_system.usability_readiness.prod",
    "history.attachment.custody.probe.prod",
    "verify.legacy_online_attachment.custody.evidence.prod",
    "verify.legacy_attachment.frontend_browser.sample_manifest.prod",
    "verify.attachment_upload.surface_manifest.prod",
]

REQUIRED_PROD_READONLY_TARGETS = [
    "verify.business_system.usability_readiness.prod",
    "verify.project_context.selector_product_boundary.guard.prod",
    "verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "verify.formal_list_surface.no_test_placeholder_guard.prod",
    "history.attachment.custody.probe.prod",
    "verify.legacy_online_attachment.custody.evidence.prod",
    "verify.legacy_attachment.frontend_browser.sample_manifest.prod",
    "verify.attachment_upload.surface_manifest.prod",
]

REQUIRED_PROD_FORBID_TARGETS = [
    "verify.productization.system_closure.topic_guard",
    "verify.system_user_experience.quick",
    "verify.system_user_experience.visible_surface_visual_coverage",
    "verify.system_user_experience.full_browser",
    "verify.business_config.unit",
    "verify.business_config.config_workbench_operation_quick",
    "verify.formal_business.release_gate",
    "verify.business_capability.productization_p1",
    "verify.business_system.usability_readiness",
]

REQUIRED_TARGET_MODE_GROUPS = {
    "prod_readonly": REQUIRED_PROD_READONLY_TARGETS,
    "prod_forbid": REQUIRED_PROD_FORBID_TARGETS,
}

REQUIRED_QUICK_DEPS = [
    "verify.productization.system_closure.topic_guard",
    "verify.system_user_experience.coverage_guard",
    "verify.frontend.product_language.guard",
    "verify.frontend.config_workbench_navigation_boundary.guard",
    "verify.project_context.selector_product_boundary.guard",
    "verify.formal_menu.runtime_no_legacy_carrier_guard",
    "verify.formal_list_surface.no_test_placeholder_guard",
    "verify.product.page_structure",
]

REQUIRED_TARGET_DEPS = {
    "verify.business_config.unit": [
        "verify.frontend.product_language.guard",
    ],
    "verify.business_config.config_workbench_operation_quick": [
        "verify.frontend.product_language.guard",
    ],
    "verify.business_config.full_acceptance": [
        "verify.business_config.unit",
        "verify.frontend.build",
        "verify.business_config.config_workbench_operation_acceptance",
        "verify.business_config.low_code_menu_navigation_alignment",
        "verify.business_config.low_code_global_stability",
        "verify.user_menu.reachability.guard",
    ],
    "verify.formal_business.release_gate": [
        "guard.prod.forbid",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.business_capability.productization_p1": [
        "guard.prod.forbid",
        "check-compose-project",
        "check-compose-env",
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
    "verify.formal_menu.runtime_no_legacy_carrier_guard.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
        "verify.formal_menu.no_legacy_carrier_guard",
    ],
    "verify.formal_list_surface.no_test_placeholder_guard.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
    ],
    "history.attachment.custody.probe.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.legacy_online_attachment.custody.evidence.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.legacy_attachment.frontend_browser.sample_manifest.prod": [
        "guard.prod.readonly",
        "check-compose-project",
        "check-compose-env",
    ],
    "verify.attachment_upload.surface_manifest.prod": [
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
    "verify.productization.system_closure.topic_guard": [
        "python3 -m py_compile scripts/verify/productization_system_closure_topic_guard.py scripts/verify/test_productization_system_closure_topic_guard.py",
        "cd scripts/verify && python3 test_productization_system_closure_topic_guard.py",
        "python3 scripts/verify/productization_system_closure_topic_guard.py",
    ],
    "verify.system_user_experience.quick": [
        "node --check frontend/apps/web/scripts/config_workbench_operation_acceptance.mjs",
        "node --check frontend/apps/web/scripts/config_workbench_operation_summary_guard.mjs",
        "node --check frontend/apps/web/scripts/business_form_user_perspective_acceptance.mjs",
        "node --check frontend/apps/web/scripts/business_form_user_perspective_summary_guard.mjs",
        "node --check frontend/apps/web/scripts/system_user_experience_shell_acceptance.mjs",
        "node --check frontend/apps/web/scripts/system_user_experience_shell_summary_guard.mjs",
        "node --check frontend/apps/web/scripts/user_page_visual_coverage.cjs",
        "node --check frontend/apps/web/scripts/user_visible_surface_visual_coverage_summary_guard.mjs",
        "node --check frontend/apps/web/scripts/system_user_experience_full_browser_summary_guard.mjs",
        "git diff --check",
    ],
    "verify.business_system.usability_readiness": [
        'BUSINESS_SYSTEM_READINESS_INCLUDE_P1="$(BUSINESS_SYSTEM_READINESS_INCLUDE_P1)"',
        "scripts/ops/validate_business_system_usability_readiness.sh",
    ],
    "verify.formal_business.release_gate": [
        "MIGRATION_ARTIFACT_ROOT",
        "scripts/ops/validate_formal_business_release_gate.sh",
    ],
    "verify.business_capability.productization_p1": [
        "MIGRATION_ARTIFACT_ROOT",
        "scripts/ops/validate_business_capability_productization_p1.sh",
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
    "verify.formal_menu.runtime_no_legacy_carrier_guard.prod": [
        "python3 -m py_compile scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py",
        "PROD_READONLY_VERIFY=1",
        "scripts/verify/formal_menu_runtime_no_legacy_carrier_guard.py",
    ],
    "verify.formal_list_surface.no_test_placeholder_guard.prod": [
        "python3 -m py_compile scripts/verify/formal_list_surface_no_test_placeholder_guard.py",
        "PROD_READONLY_VERIFY=1",
        "scripts/verify/formal_list_surface_no_test_placeholder_guard.py",
    ],
    "history.attachment.custody.probe.prod": [
        "MIGRATION_ARTIFACT_ROOT",
        "scripts/migration/history_attachment_custody_probe.py",
    ],
    "verify.legacy_online_attachment.custody.evidence.prod": [
        "LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_JOB_ROOT",
        "LEGACY_ATTACHMENT_CUSTODY_EVIDENCE_SOURCE_CONTAINS",
        "scripts/verify/legacy_online_attachment_custody_evidence.py",
    ],
    "verify.legacy_attachment.frontend_browser.sample_manifest.prod": [
        "LEGACY_ATTACHMENT_BROWSER_SAMPLE_MANIFEST_OUTPUT",
        "scripts/verify/legacy_attachment_frontend_browser_sample_manifest.py",
    ],
    "verify.attachment_upload.surface_manifest.prod": [
        "LEGACY_ATTACHMENT_UPLOAD_SURFACE_OUTPUT",
        "LEGACY_ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS",
        "scripts/verify/attachment_upload_surface_manifest.py",
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

REQUIRED_TARGET_BODY_ORDER = {
    "verify.productization.system_closure.topic_guard": [
        "python3 -m py_compile scripts/verify/productization_system_closure_topic_guard.py scripts/verify/test_productization_system_closure_topic_guard.py",
        "cd scripts/verify && python3 test_productization_system_closure_topic_guard.py",
        "python3 scripts/verify/productization_system_closure_topic_guard.py",
    ],
}


def _target_line(text: str, target: str) -> str:
    lines = text.splitlines()
    prefix_pattern = re.compile(rf"^{re.escape(target)}\s*:")
    for index, line in enumerate(lines):
        if not prefix_pattern.match(line):
            continue
        chunks = [line.rstrip()]
        cursor = index
        while chunks[-1].endswith("\\"):
            chunks[-1] = chunks[-1][:-1].rstrip()
            cursor += 1
            if cursor >= len(lines):
                break
            chunks.append(lines[cursor].strip())
        return " ".join(chunk for chunk in chunks if chunk)
    return ""


def _target_line_count(text: str, target: str) -> int:
    pattern = re.compile(rf"^{re.escape(target)}\s*:", re.MULTILINE)
    return len(pattern.findall(text))


def _target_deps(text: str, target: str) -> list[str]:
    target_line = _target_line(text, target)
    if not target_line:
        return []
    return target_line.split(":", 1)[1].split()


def _target_body(text: str, target: str) -> str:
    lines = text.splitlines()
    prefix_pattern = re.compile(rf"^{re.escape(target)}\s*:")
    for index, line in enumerate(lines):
        if not prefix_pattern.match(line):
            continue
        cursor = index
        while lines[cursor].rstrip().endswith("\\"):
            cursor += 1
            if cursor >= len(lines):
                return ""
        body_lines = []
        for body_line in lines[cursor + 1 :]:
            if not body_line.startswith("\t") and body_line.strip():
                break
            if body_line.startswith("\t") or not body_line.strip():
                body_lines.append(body_line)
        return "\n".join(body_lines) + ("\n" if body_lines else "")
    return ""


def _tokens_in_order(text: str, tokens: list[str]) -> bool:
    cursor = -1
    for token in tokens:
        index = text.find(token, cursor + 1)
        if index < 0:
            return False
        cursor = index
    return True


def _target_commands(target_body: str) -> list[str]:
    commands: list[str] = []
    for line in target_body.splitlines():
        command = line.strip()
        if not command:
            continue
        if command.startswith("@"):
            command = command[1:]
        commands.append(command)
    return commands


def _duplicate_tokens(tokens: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for token in tokens:
        if token in seen and token not in duplicates:
            duplicates.append(token)
        seen.add(token)
    return duplicates


def _doc_declared_make_targets() -> list[str]:
    targets: list[str] = []
    for token in REQUIRED_DOC_TOKENS:
        if token.startswith("make "):
            targets.append(" ".join(token.removeprefix("make ").split()))
    return targets


def _inspected_make_targets() -> list[str]:
    targets = [
        *REQUIRED_MAKE_TARGETS,
        *REQUIRED_TARGET_DEPS.keys(),
        *REQUIRED_TARGET_BODY_TOKENS.keys(),
        *REQUIRED_TARGET_BODY_ORDER.keys(),
    ]
    return list(dict.fromkeys(targets))


def validate(doc_text: str, make_text: str) -> list[str]:
    errors: list[str] = []

    if not doc_text:
        errors.append(f"missing doc: {DOC.relative_to(ROOT)}")
    if not make_text:
        errors.append("missing Makefile")

    seen_doc_token_groups: dict[str, str] = {}
    for group, tokens in REQUIRED_DOC_TOKEN_GROUPS.items():
        for token in _duplicate_tokens(tokens):
            errors.append(f"{group} token duplicated: {token}")
        for token in tokens:
            previous_group = seen_doc_token_groups.get(token)
            if previous_group and previous_group != group:
                errors.append(f"doc token cross-classified: {token} in {previous_group} and {group}")
            seen_doc_token_groups[token] = group

    for token in [token for tokens in REQUIRED_DOC_TOKEN_GROUPS.values() for token in tokens]:
        if token not in doc_text:
            errors.append(f"doc missing token: {token}")

    for target in _doc_declared_make_targets():
        if target not in REQUIRED_MAKE_TARGETS:
            errors.append(f"doc declared make target not guarded as required Makefile target: {target}")
        if target not in REQUIRED_DOC_DECLARED_MAKE_TARGETS:
            errors.append(f"doc declared make target not allowed in topic doc: {target}")

    doc_declared_make_targets = _doc_declared_make_targets()
    for target in _duplicate_tokens(doc_declared_make_targets):
        errors.append(f"doc declared make target duplicated: {target}")
    for target in _duplicate_tokens(REQUIRED_DOC_DECLARED_MAKE_TARGETS):
        errors.append(f"required doc-declared make target duplicated: {target}")
    for target in REQUIRED_DOC_DECLARED_MAKE_TARGETS:
        if target not in REQUIRED_MAKE_TARGETS:
            errors.append(f"required doc-declared make target not guarded as required Makefile target: {target}")
        if target not in doc_declared_make_targets:
            errors.append(f"required doc-declared make target missing from doc tokens: {target}")

    seen_target_mode_groups: dict[str, str] = {}
    for group, targets in REQUIRED_TARGET_MODE_GROUPS.items():
        for target in _duplicate_tokens(targets):
            errors.append(f"{group} target duplicated: {target}")
        for target in targets:
            previous_group = seen_target_mode_groups.get(target)
            if previous_group and previous_group != group:
                errors.append(f"target mode cross-classified: {target} in {previous_group} and {group}")
            seen_target_mode_groups[target] = group
            if target not in REQUIRED_MAKE_TARGETS:
                errors.append(f"{group} target not guarded as required Makefile target: {target}")

    for target in _duplicate_tokens(REQUIRED_MAKE_TARGETS):
        errors.append(f"required Makefile target duplicated: {target}")

    for target in _inspected_make_targets():
        if not _target_line(make_text, target):
            errors.append(f"Makefile missing target: {target}")
        elif _target_line_count(make_text, target) > 1:
            errors.append(f"Makefile duplicate target: {target}")

    quick_deps = _target_deps(make_text, "verify.system_user_experience.quick")
    for dep in _duplicate_tokens(REQUIRED_QUICK_DEPS):
        errors.append(f"quick gate required dependency duplicated: {dep}")
    for dep in _duplicate_tokens(quick_deps):
        errors.append(f"quick gate Makefile dependency duplicated: {dep}")
    for dep in REQUIRED_QUICK_DEPS:
        if dep not in quick_deps:
            errors.append(f"quick gate missing dependency: {dep}")

    for target, deps in REQUIRED_TARGET_DEPS.items():
        target_line = _target_line(make_text, target)
        if not target_line:
            errors.append(f"Makefile missing target: {target}")
            continue
        actual_deps = _target_deps(make_text, target)
        for dep in _duplicate_tokens(deps):
            errors.append(f"{target} required dependency duplicated: {dep}")
        for dep in _duplicate_tokens(actual_deps):
            errors.append(f"{target} Makefile dependency duplicated: {dep}")
        for dep in deps:
            if dep not in actual_deps:
                errors.append(f"{target} missing dependency: {dep}")

    for target in REQUIRED_PROD_READONLY_TARGETS:
        actual_deps = _target_deps(make_text, target)
        if "guard.prod.readonly" not in actual_deps:
            errors.append(f"{target} must use guard.prod.readonly")
        if "guard.prod.forbid" in actual_deps:
            errors.append(f"{target} must not use guard.prod.forbid")

    for target in REQUIRED_PROD_FORBID_TARGETS:
        actual_deps = _target_deps(make_text, target)
        if "guard.prod.forbid" not in actual_deps:
            errors.append(f"{target} must use guard.prod.forbid")
        if "guard.prod.readonly" in actual_deps:
            errors.append(f"{target} must not use guard.prod.readonly")

    for target, tokens in REQUIRED_TARGET_BODY_TOKENS.items():
        target_body = _target_body(make_text, target)
        if not target_body:
            errors.append(f"Makefile missing command body: {target}")
            continue
        for command in _duplicate_tokens(_target_commands(target_body)):
            errors.append(f"{target} Makefile command duplicated: {command}")
        for token in _duplicate_tokens(tokens):
            errors.append(f"{target} required command token duplicated: {token}")
        for token in tokens:
            if token not in target_body:
                errors.append(f"{target} missing command token: {token}")

    for target, tokens in REQUIRED_TARGET_BODY_ORDER.items():
        target_body = _target_body(make_text, target)
        required_command_tokens = REQUIRED_TARGET_BODY_TOKENS.get(target, [])
        if not required_command_tokens:
            errors.append(f"{target} command order target missing required command token inventory")
        for token in _duplicate_tokens(tokens):
            errors.append(f"{target} command order token duplicated: {token}")
        for token in tokens:
            if token not in required_command_tokens:
                errors.append(f"{target} command order token not guarded as required command token: {token}")
        if target_body and not _tokens_in_order(target_body, tokens):
            errors.append(f"{target} command order mismatch")

    topic_line = _target_line(make_text, "verify.productization.system_closure.topic_guard")
    if topic_line and "guard.prod.forbid" not in _target_deps(make_text, "verify.productization.system_closure.topic_guard"):
        errors.append("topic guard must use guard.prod.forbid")

    return errors


def main() -> int:
    doc_text = DOC.read_text(encoding="utf-8") if DOC.is_file() else ""
    make_text = MAKEFILE.read_text(encoding="utf-8") if MAKEFILE.is_file() else ""
    errors = validate(doc_text, make_text)

    result = {
        "guard": "productization_system_closure_topic_guard",
        "status": "FAIL" if errors else "PASS",
        "doc": str(DOC.relative_to(ROOT)),
        "errors": errors,
        "required_doc_tokens": len(REQUIRED_DOC_TOKENS),
        "required_doc_token_groups": len(REQUIRED_DOC_TOKEN_GROUPS),
        "required_evidence_artifact_paths": len(REQUIRED_EVIDENCE_ARTIFACT_PATHS),
        "required_closeout_fields": len(REQUIRED_CLOSEOUT_FIELDS),
        "required_make_targets": len(REQUIRED_MAKE_TARGETS),
        "required_doc_declared_make_targets": len(REQUIRED_DOC_DECLARED_MAKE_TARGETS),
        "inspected_make_targets": len(_inspected_make_targets()),
        "required_target_mode_groups": len(REQUIRED_TARGET_MODE_GROUPS),
        "required_prod_readonly_targets": len(REQUIRED_PROD_READONLY_TARGETS),
        "required_prod_forbid_targets": len(REQUIRED_PROD_FORBID_TARGETS),
        "required_quick_dependencies": len(REQUIRED_QUICK_DEPS),
        "required_dependency_targets": len(REQUIRED_TARGET_DEPS),
        "required_target_dependencies": sum(len(deps) for deps in REQUIRED_TARGET_DEPS.values()),
        "required_command_token_targets": len(REQUIRED_TARGET_BODY_TOKENS),
        "required_target_body_tokens": sum(len(tokens) for tokens in REQUIRED_TARGET_BODY_TOKENS.values()),
        "required_command_order_targets": len(REQUIRED_TARGET_BODY_ORDER),
        "required_target_body_order_tokens": sum(len(tokens) for tokens in REQUIRED_TARGET_BODY_ORDER.values()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
