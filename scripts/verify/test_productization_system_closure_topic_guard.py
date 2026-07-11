#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest
from unittest import mock

import productization_system_closure_topic_guard as guard


class _FakePath:
    def __init__(self, text: str) -> None:
        self._text = text

    def is_file(self) -> bool:
        return True

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._text

    def relative_to(self, _root: object) -> str:
        return "fake"


def _doc_text() -> str:
    return "\n".join(
        [
            *guard.REQUIRED_DOC_TOKENS,
            *guard.REQUIRED_EVIDENCE_ARTIFACT_PATHS,
            *guard.REQUIRED_CLOSEOUT_FIELDS,
        ]
    )


def _target(name: str, deps: list[str], body: list[str] | None = None) -> str:
    lines = [f"{name}: {' '.join(deps)}"]
    lines.extend(f"\t@{line}" for line in body or [])
    return "\n".join(lines) + "\n"


def _multiline_target(name: str, deps: list[str], body: list[str] | None = None) -> str:
    lines = [f"{name}: \\"]
    lines.extend(f"  {dep} \\" for dep in deps[:-1])
    lines.append(f"  {deps[-1] if deps else ''}".rstrip())
    lines.extend(f"\t@{line}" for line in body or [])
    return "\n".join(lines) + "\n"


def _make_text() -> str:
    targets = [
        _target(
            "verify.productization.system_closure.topic_guard",
            ["guard.prod.forbid"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.productization.system_closure.topic_guard"],
        ),
        _target(
            "verify.system_user_experience.quick",
            [
                "guard.prod.forbid",
                *guard.REQUIRED_QUICK_DEPS,
            ],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.quick"],
        ),
        _target(
            "verify.system_user_experience.visible_surface_visual_coverage",
            ["guard.prod.forbid"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.visible_surface_visual_coverage"],
        ),
        _target(
            "verify.system_user_experience.full_browser",
            ["guard.prod.forbid", *guard.REQUIRED_TARGET_DEPS["verify.system_user_experience.full_browser"]],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.full_browser"],
        ),
        _target(
            "verify.business_system.usability_readiness",
            guard.REQUIRED_TARGET_DEPS["verify.business_system.usability_readiness"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.business_system.usability_readiness"],
        ),
        _target("verify.production_git.authority.guard", []),
        _target(
            "verify.business_system.usability_readiness.prod",
            guard.REQUIRED_TARGET_DEPS["verify.business_system.usability_readiness.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.business_system.usability_readiness.prod"],
        ),
        _target(
            "verify.project_context.selector_product_boundary.guard.prod",
            guard.REQUIRED_TARGET_DEPS["verify.project_context.selector_product_boundary.guard.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.project_context.selector_product_boundary.guard.prod"],
        ),
        _target(
            "verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
            guard.REQUIRED_TARGET_DEPS["verify.formal_menu.runtime_no_legacy_carrier_guard.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.formal_menu.runtime_no_legacy_carrier_guard.prod"],
        ),
        _target(
            "verify.formal_list_surface.no_test_placeholder_guard.prod",
            guard.REQUIRED_TARGET_DEPS["verify.formal_list_surface.no_test_placeholder_guard.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.formal_list_surface.no_test_placeholder_guard.prod"],
        ),
        _target(
            "history.attachment.custody.probe.prod",
            guard.REQUIRED_TARGET_DEPS["history.attachment.custody.probe.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["history.attachment.custody.probe.prod"],
        ),
        _target(
            "verify.legacy_online_attachment.custody.evidence.prod",
            guard.REQUIRED_TARGET_DEPS["verify.legacy_online_attachment.custody.evidence.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.legacy_online_attachment.custody.evidence.prod"],
        ),
        _target(
            "verify.legacy_attachment.frontend_browser.sample_manifest.prod",
            guard.REQUIRED_TARGET_DEPS["verify.legacy_attachment.frontend_browser.sample_manifest.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.legacy_attachment.frontend_browser.sample_manifest.prod"],
        ),
        _target(
            "verify.attachment_upload.surface_manifest.prod",
            guard.REQUIRED_TARGET_DEPS["verify.attachment_upload.surface_manifest.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.attachment_upload.surface_manifest.prod"],
        ),
        _target("verify.frontend.product_language.guard", ["guard.prod.forbid"]),
        _target(
            "verify.business_config.unit",
            ["guard.prod.forbid", *guard.REQUIRED_TARGET_DEPS["verify.business_config.unit"]],
        ),
        _target(
            "verify.business_config.config_workbench_operation_quick",
            [
                "guard.prod.forbid",
                *guard.REQUIRED_TARGET_DEPS["verify.business_config.config_workbench_operation_quick"],
            ],
        ),
        _target(
            "verify.business_config.full_acceptance",
            guard.REQUIRED_TARGET_DEPS["verify.business_config.full_acceptance"],
        ),
        _target(
            "verify.formal_business.release_gate",
            guard.REQUIRED_TARGET_DEPS["verify.formal_business.release_gate"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.formal_business.release_gate"],
        ),
        _target(
            "verify.business_capability.productization_p1",
            guard.REQUIRED_TARGET_DEPS["verify.business_capability.productization_p1"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.business_capability.productization_p1"],
        ),
        _target(
            "verify.system_user_experience.shell_acceptance",
            ["guard.prod.forbid"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.shell_acceptance"],
        ),
        _target(
            "verify.system_user_experience.business_form_user_perspective",
            ["guard.prod.forbid"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.business_form_user_perspective"],
        ),
    ]
    return "\n\n".join(targets)


class ProductizationSystemClosureTopicGuardTests(unittest.TestCase):
    def test_complete_minimal_fixture_passes(self) -> None:
        self.assertEqual([], guard.validate(_doc_text(), _make_text()))

    def test_main_reports_body_order_rule_count(self) -> None:
        with mock.patch.object(guard, "DOC", _FakePath(_doc_text())), mock.patch.object(
            guard,
            "MAKEFILE",
            _FakePath(_make_text()),
        ), mock.patch("builtins.print") as print_mock:
            self.assertEqual(0, guard.main())

        payload = print_mock.call_args.args[0]
        self.assertIn('"required_target_body_order_tokens": 3', payload)
        self.assertIn('"required_doc_token_groups": 3', payload)
        self.assertIn('"required_evidence_artifact_paths": 9', payload)
        self.assertIn('"required_closeout_fields": 6', payload)
        self.assertIn('"required_doc_declared_make_targets": 18', payload)
        self.assertIn('"inspected_make_targets": 22', payload)
        self.assertIn('"required_target_mode_groups": 2', payload)
        self.assertIn('"required_prod_readonly_targets": 8', payload)
        self.assertIn('"required_prod_forbid_targets": 9', payload)
        self.assertIn('"required_dependency_targets": 15', payload)
        self.assertIn('"required_command_token_targets": 17', payload)
        self.assertIn('"required_command_order_targets": 1', payload)

    def test_duplicate_doc_token_fails(self) -> None:
        duplicated_tokens = [*guard.REQUIRED_DOC_TOKENS, "用户体验"]
        with mock.patch.object(guard, "REQUIRED_DOC_TOKENS", duplicated_tokens), mock.patch.dict(
            guard.REQUIRED_DOC_TOKEN_GROUPS,
            {"doc": duplicated_tokens},
        ):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn("doc token duplicated: 用户体验", errors)

    def test_cross_classified_doc_token_fails(self) -> None:
        cross_classified_paths = [*guard.REQUIRED_EVIDENCE_ARTIFACT_PATHS, "可重复验收证据"]
        with mock.patch.object(guard, "REQUIRED_EVIDENCE_ARTIFACT_PATHS", cross_classified_paths), mock.patch.dict(
            guard.REQUIRED_DOC_TOKEN_GROUPS,
            {"evidence_artifact": cross_classified_paths},
        ):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn("doc token cross-classified: 可重复验收证据 in doc and evidence_artifact", errors)

    def test_doc_declared_make_target_must_be_required_make_target(self) -> None:
        doc_tokens = [*guard.REQUIRED_DOC_TOKENS, "make verify.untracked.topic.gate"]
        with mock.patch.object(guard, "REQUIRED_DOC_TOKENS", doc_tokens), mock.patch.dict(
            guard.REQUIRED_DOC_TOKEN_GROUPS,
            {"doc": doc_tokens},
        ):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "doc declared make target not guarded as required Makefile target: verify.untracked.topic.gate",
            errors,
        )

    def test_required_doc_declared_make_target_duplicate_fails(self) -> None:
        duplicated_targets = [
            *guard.REQUIRED_DOC_DECLARED_MAKE_TARGETS,
            "verify.system_user_experience.quick",
        ]
        with mock.patch.object(guard, "REQUIRED_DOC_DECLARED_MAKE_TARGETS", duplicated_targets):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn("required doc-declared make target duplicated: verify.system_user_experience.quick", errors)

    def test_required_doc_declared_make_target_must_be_required_make_target(self) -> None:
        required_doc_targets = [*guard.REQUIRED_DOC_DECLARED_MAKE_TARGETS, "verify.untracked.topic.gate"]
        with mock.patch.object(guard, "REQUIRED_DOC_DECLARED_MAKE_TARGETS", required_doc_targets):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "required doc-declared make target not guarded as required Makefile target: verify.untracked.topic.gate",
            errors,
        )

    def test_required_doc_declared_make_target_must_be_in_doc_tokens(self) -> None:
        required_doc_targets = [*guard.REQUIRED_DOC_DECLARED_MAKE_TARGETS, "verify.frontend.product_language.guard"]
        with mock.patch.object(guard, "REQUIRED_DOC_DECLARED_MAKE_TARGETS", required_doc_targets):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "required doc-declared make target missing from doc tokens: verify.frontend.product_language.guard",
            errors,
        )

    def test_doc_must_keep_frontend_backend_contract_boundary(self) -> None:
        doc_text = _doc_text().replace("前端只消费后端契约", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 前端只消费后端契约", errors)

    def test_doc_must_keep_menu_alignment_boundary(self) -> None:
        doc_text = _doc_text().replace("菜单配置展示口径必须与主导航展示口径一致", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 菜单配置展示口径必须与主导航展示口径一致", errors)

    def test_doc_must_keep_group_menu_boundary(self) -> None:
        doc_text = _doc_text().replace("分组菜单是导航组织能力", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 分组菜单是导航组织能力", errors)

    def test_doc_must_keep_configurable_menu_contract_boundary(self) -> None:
        doc_text = _doc_text().replace("真实可配置对象必须由后端契约明确给出", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 真实可配置对象必须由后端契约明确给出", errors)

    def test_doc_must_keep_odoo_group_menu_write_boundary(self) -> None:
        doc_text = _doc_text().replace("不写回 Odoo 分组菜单", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 不写回 Odoo 分组菜单", errors)

    def test_doc_must_keep_repeatable_acceptance_evidence_boundary(self) -> None:
        doc_text = _doc_text().replace("可重复验收证据", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 可重复验收证据", errors)

    def test_doc_must_keep_browser_report_closeout_field(self) -> None:
        doc_text = _doc_text().replace("浏览器验收结果与结构化报告路径", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 浏览器验收结果与结构化报告路径", errors)

    def test_doc_must_keep_backlog_closeout_field(self) -> None:
        doc_text = _doc_text().replace("已修复的问题类型和仍保留的 backlog", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 已修复的问题类型和仍保留的 backlog", errors)

    def test_doc_must_keep_three_environment_closeout_field(self) -> None:
        doc_text = _doc_text().replace("本地、日常开发服务器、生产服务器的验证结论", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 本地、日常开发服务器、生产服务器的验证结论", errors)

    def test_doc_must_keep_user_delivery_decision_field(self) -> None:
        doc_text = _doc_text().replace("是否具备交付用户使用的条件", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: 是否具备交付用户使用的条件", errors)

    def test_doc_must_keep_full_browser_summary_artifact_path(self) -> None:
        doc_text = _doc_text().replace("artifacts/playwright/system-user-experience-full-browser/summary.json", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn(
            "doc missing token: artifacts/playwright/system-user-experience-full-browser/summary.json",
            errors,
        )

    def test_doc_must_keep_business_readiness_artifact_path(self) -> None:
        doc_text = _doc_text().replace("artifacts/backend/business_system_usability_readiness.json", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: artifacts/backend/business_system_usability_readiness.json", errors)

    def test_doc_must_keep_production_record_directory_path(self) -> None:
        doc_text = _doc_text().replace("docs/ops/releases/current/", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: docs/ops/releases/current/", errors)

    def test_topic_guard_must_forbid_production_write_context(self) -> None:
        make_text = _make_text().replace(
            "verify.productization.system_closure.topic_guard: guard.prod.forbid",
            "verify.productization.system_closure.topic_guard:",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("topic guard must use guard.prod.forbid", errors)

    def test_topic_guard_requires_exact_production_forbid_dependency(self) -> None:
        make_text = _make_text().replace(
            "verify.productization.system_closure.topic_guard: guard.prod.forbid",
            "verify.productization.system_closure.topic_guard: guard.prod.forbidden",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("topic guard must use guard.prod.forbid", errors)

    def test_topic_guard_must_run_its_regression_tests(self) -> None:
        make_text = _make_text().replace(
            "cd scripts/verify && python3 test_productization_system_closure_topic_guard.py",
            "",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.productization.system_closure.topic_guard missing command token: cd scripts/verify && python3 test_productization_system_closure_topic_guard.py",
            errors,
        )

    def test_topic_guard_commands_must_stay_in_order(self) -> None:
        make_text = _make_text().replace(
            "\t@cd scripts/verify && python3 test_productization_system_closure_topic_guard.py\n"
            "\t@python3 scripts/verify/productization_system_closure_topic_guard.py",
            "\t@python3 scripts/verify/productization_system_closure_topic_guard.py\n"
            "\t@cd scripts/verify && python3 test_productization_system_closure_topic_guard.py",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("verify.productization.system_closure.topic_guard command order mismatch", errors)

    def test_duplicate_required_command_token_fails(self) -> None:
        duplicated_body_tokens = {
            **guard.REQUIRED_TARGET_BODY_TOKENS,
            "verify.productization.system_closure.topic_guard": [
                *guard.REQUIRED_TARGET_BODY_TOKENS["verify.productization.system_closure.topic_guard"],
                "python3 scripts/verify/productization_system_closure_topic_guard.py",
            ],
        }
        with mock.patch.object(guard, "REQUIRED_TARGET_BODY_TOKENS", duplicated_body_tokens):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "verify.productization.system_closure.topic_guard required command token duplicated: python3 scripts/verify/productization_system_closure_topic_guard.py",
            errors,
        )

    def test_duplicate_command_order_token_fails(self) -> None:
        duplicated_order_tokens = {
            "verify.productization.system_closure.topic_guard": [
                *guard.REQUIRED_TARGET_BODY_ORDER["verify.productization.system_closure.topic_guard"],
                "python3 scripts/verify/productization_system_closure_topic_guard.py",
            ],
        }
        with mock.patch.object(guard, "REQUIRED_TARGET_BODY_ORDER", duplicated_order_tokens):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "verify.productization.system_closure.topic_guard command order token duplicated: python3 scripts/verify/productization_system_closure_topic_guard.py",
            errors,
        )

    def test_command_order_target_must_have_required_command_inventory(self) -> None:
        make_text = _make_text()
        order_only_target = {
            "verify.system_user_experience.quick": [
                "node --check frontend/apps/web/scripts/config_workbench_operation_acceptance.mjs",
            ],
        }
        body_tokens_without_target = {
            key: value
            for key, value in guard.REQUIRED_TARGET_BODY_TOKENS.items()
            if key != "verify.system_user_experience.quick"
        }
        with mock.patch.object(guard, "REQUIRED_TARGET_BODY_ORDER", order_only_target), mock.patch.object(
            guard,
            "REQUIRED_TARGET_BODY_TOKENS",
            body_tokens_without_target,
        ):
            errors = guard.validate(_doc_text(), make_text)

        self.assertIn(
            "verify.system_user_experience.quick command order target missing required command token inventory",
            errors,
        )

    def test_command_order_token_must_be_required_command_token(self) -> None:
        order_tokens = {
            "verify.productization.system_closure.topic_guard": [
                "echo unguarded command",
            ],
        }
        with mock.patch.object(guard, "REQUIRED_TARGET_BODY_ORDER", order_tokens):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "verify.productization.system_closure.topic_guard command order token not guarded as required command token: echo unguarded command",
            errors,
        )

    def test_duplicate_makefile_command_fails(self) -> None:
        duplicated_command = "\t@python3 scripts/verify/productization_system_closure_topic_guard.py"
        make_text = _make_text().replace(
            duplicated_command,
            f"{duplicated_command}\n{duplicated_command}",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.productization.system_closure.topic_guard Makefile command duplicated: python3 scripts/verify/productization_system_closure_topic_guard.py",
            errors,
        )

    def test_duplicate_required_target_fails(self) -> None:
        make_text = _make_text() + "\n" + _target("verify.frontend.product_language.guard", ["guard.prod.forbid"])
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("Makefile duplicate target: verify.frontend.product_language.guard", errors)

    def test_duplicate_required_target_inventory_fails(self) -> None:
        duplicated_targets = [*guard.REQUIRED_MAKE_TARGETS, "verify.frontend.product_language.guard"]
        with mock.patch.object(guard, "REQUIRED_MAKE_TARGETS", duplicated_targets):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn("required Makefile target duplicated: verify.frontend.product_language.guard", errors)

    def test_duplicate_auxiliary_inspected_target_fails(self) -> None:
        make_text = _make_text() + "\n" + _target(
            "verify.system_user_experience.shell_acceptance",
            ["guard.prod.forbid"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.shell_acceptance"],
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("Makefile duplicate target: verify.system_user_experience.shell_acceptance", errors)

    def test_missing_quick_dependency_fails(self) -> None:
        make_text = _make_text().replace(" verify.formal_list_surface.no_test_placeholder_guard", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("quick gate missing dependency: verify.formal_list_surface.no_test_placeholder_guard", errors)

    def test_quick_dependency_requires_exact_target_name(self) -> None:
        make_text = _make_text().replace(
            " verify.formal_list_surface.no_test_placeholder_guard",
            " verify.formal_list_surface.no_test_placeholder_guard_fake",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("quick gate missing dependency: verify.formal_list_surface.no_test_placeholder_guard", errors)

    def test_duplicate_quick_required_dependency_fails(self) -> None:
        duplicated_deps = [*guard.REQUIRED_QUICK_DEPS, "verify.product.page_structure"]
        with mock.patch.object(guard, "REQUIRED_QUICK_DEPS", duplicated_deps):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn("quick gate required dependency duplicated: verify.product.page_structure", errors)

    def test_duplicate_quick_makefile_dependency_fails(self) -> None:
        make_text = _make_text().replace(
            "verify.product.page_structure",
            "verify.product.page_structure verify.product.page_structure",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("quick gate Makefile dependency duplicated: verify.product.page_structure", errors)

    def test_duplicate_required_target_dependency_fails(self) -> None:
        duplicated_target_deps = {
            **guard.REQUIRED_TARGET_DEPS,
            "verify.business_config.full_acceptance": [
                *guard.REQUIRED_TARGET_DEPS["verify.business_config.full_acceptance"],
                "verify.user_menu.reachability.guard",
            ],
        }
        with mock.patch.object(guard, "REQUIRED_TARGET_DEPS", duplicated_target_deps):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "verify.business_config.full_acceptance required dependency duplicated: verify.user_menu.reachability.guard",
            errors,
        )

    def test_duplicate_target_makefile_dependency_fails(self) -> None:
        make_text = _make_text().replace(
            "verify.user_menu.reachability.guard",
            "verify.user_menu.reachability.guard verify.user_menu.reachability.guard",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_config.full_acceptance Makefile dependency duplicated: verify.user_menu.reachability.guard",
            errors,
        )

    def test_prod_readiness_must_keep_readonly_parameters(self) -> None:
        make_text = _make_text().replace("BUSINESS_SYSTEM_READINESS_PROD_READONLY=1", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_system.usability_readiness.prod missing command token: BUSINESS_SYSTEM_READINESS_PROD_READONLY=1",
            errors,
        )

    def test_prod_target_must_not_use_forbid_guard(self) -> None:
        make_text = _make_text().replace(
            "verify.business_system.usability_readiness.prod: guard.prod.readonly",
            "verify.business_system.usability_readiness.prod: guard.prod.forbid",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("verify.business_system.usability_readiness.prod must use guard.prod.readonly", errors)
        self.assertIn("verify.business_system.usability_readiness.prod must not use guard.prod.forbid", errors)

    def test_nonprod_release_gate_must_not_use_readonly_guard(self) -> None:
        make_text = _make_text().replace(
            "verify.formal_business.release_gate: guard.prod.forbid",
            "verify.formal_business.release_gate: guard.prod.readonly",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("verify.formal_business.release_gate must use guard.prod.forbid", errors)
        self.assertIn("verify.formal_business.release_gate must not use guard.prod.readonly", errors)

    def test_target_mode_group_duplicate_fails(self) -> None:
        duplicated_targets = [
            *guard.REQUIRED_PROD_READONLY_TARGETS,
            "verify.business_system.usability_readiness.prod",
        ]
        with mock.patch.object(guard, "REQUIRED_PROD_READONLY_TARGETS", duplicated_targets), mock.patch.dict(
            guard.REQUIRED_TARGET_MODE_GROUPS,
            {"prod_readonly": duplicated_targets},
        ):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn("prod_readonly target duplicated: verify.business_system.usability_readiness.prod", errors)

    def test_target_mode_cross_classification_fails(self) -> None:
        cross_classified_targets = [
            *guard.REQUIRED_PROD_FORBID_TARGETS,
            "verify.business_system.usability_readiness.prod",
        ]
        with mock.patch.object(guard, "REQUIRED_PROD_FORBID_TARGETS", cross_classified_targets), mock.patch.dict(
            guard.REQUIRED_TARGET_MODE_GROUPS,
            {"prod_forbid": cross_classified_targets},
        ):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "target mode cross-classified: verify.business_system.usability_readiness.prod in prod_readonly and prod_forbid",
            errors,
        )

    def test_target_mode_member_must_be_required_make_target(self) -> None:
        unguarded_targets = [*guard.REQUIRED_PROD_READONLY_TARGETS, "verify.untracked.prod"]
        with mock.patch.object(guard, "REQUIRED_PROD_READONLY_TARGETS", unguarded_targets), mock.patch.dict(
            guard.REQUIRED_TARGET_MODE_GROUPS,
            {"prod_readonly": unguarded_targets},
        ):
            errors = guard.validate(_doc_text(), _make_text())

        self.assertIn(
            "prod_readonly target not guarded as required Makefile target: verify.untracked.prod",
            errors,
        )

    def test_full_browser_gate_must_keep_config_workbench_acceptance(self) -> None:
        make_text = _make_text().replace(" verify.business_config.config_workbench_operation_acceptance", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.system_user_experience.full_browser missing dependency: verify.business_config.config_workbench_operation_acceptance",
            errors,
        )

    def test_full_browser_gate_must_keep_business_form_acceptance(self) -> None:
        make_text = _make_text().replace(" verify.system_user_experience.business_form_user_perspective", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.system_user_experience.full_browser missing dependency: verify.system_user_experience.business_form_user_perspective",
            errors,
        )

    def test_full_lowcode_acceptance_target_must_exist(self) -> None:
        target = _target(
            "verify.business_config.full_acceptance",
            guard.REQUIRED_TARGET_DEPS["verify.business_config.full_acceptance"],
        )
        make_text = _make_text().replace(target, "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("Makefile missing target: verify.business_config.full_acceptance", errors)

    def test_full_lowcode_acceptance_must_keep_config_workbench_browser_acceptance(self) -> None:
        make_text = _make_text().replace(" verify.business_config.config_workbench_operation_acceptance", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_config.full_acceptance missing dependency: verify.business_config.config_workbench_operation_acceptance",
            errors,
        )

    def test_full_lowcode_acceptance_must_keep_menu_navigation_alignment(self) -> None:
        make_text = _make_text().replace(" verify.business_config.low_code_menu_navigation_alignment", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_config.full_acceptance missing dependency: verify.business_config.low_code_menu_navigation_alignment",
            errors,
        )

    def test_doc_must_keep_formal_business_release_gate(self) -> None:
        doc_text = _doc_text().replace("make verify.formal_business.release_gate", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: make verify.formal_business.release_gate", errors)

    def test_formal_business_release_gate_must_keep_prod_forbid_dependency(self) -> None:
        make_text = _make_text().replace(
            "verify.formal_business.release_gate: guard.prod.forbid",
            "verify.formal_business.release_gate:",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("verify.formal_business.release_gate missing dependency: guard.prod.forbid", errors)

    def test_formal_business_release_gate_must_keep_ops_script(self) -> None:
        make_text = _make_text().replace("scripts/ops/validate_formal_business_release_gate.sh", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.formal_business.release_gate missing command token: scripts/ops/validate_formal_business_release_gate.sh",
            errors,
        )

    def test_business_capability_p1_gate_must_keep_ops_script(self) -> None:
        make_text = _make_text().replace("scripts/ops/validate_business_capability_productization_p1.sh", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_capability.productization_p1 missing command token: scripts/ops/validate_business_capability_productization_p1.sh",
            errors,
        )

    def test_multiline_target_dependencies_are_supported(self) -> None:
        single_line_target = _target(
            "verify.system_user_experience.full_browser",
            ["guard.prod.forbid", *guard.REQUIRED_TARGET_DEPS["verify.system_user_experience.full_browser"]],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.full_browser"],
        )
        multiline_target = _multiline_target(
            "verify.system_user_experience.full_browser",
            ["guard.prod.forbid", *guard.REQUIRED_TARGET_DEPS["verify.system_user_experience.full_browser"]],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.full_browser"],
        )
        make_text = _make_text().replace(single_line_target, multiline_target)
        self.assertEqual([], guard.validate(_doc_text(), make_text))

    def test_prod_project_context_guard_must_keep_readonly_dependency(self) -> None:
        make_text = _make_text().replace(
            "verify.project_context.selector_product_boundary.guard.prod: guard.prod.readonly",
            "verify.project_context.selector_product_boundary.guard.prod:",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.project_context.selector_product_boundary.guard.prod missing dependency: guard.prod.readonly",
            errors,
        )

    def test_prod_project_context_guard_must_keep_readonly_parameter(self) -> None:
        make_text = _make_text().replace("PROD_READONLY_VERIFY=1", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.project_context.selector_product_boundary.guard.prod missing command token: PROD_READONLY_VERIFY=1",
            errors,
        )

    def test_prod_formal_menu_guard_must_keep_readonly_dependency(self) -> None:
        make_text = _make_text().replace(
            "verify.formal_menu.runtime_no_legacy_carrier_guard.prod: guard.prod.readonly",
            "verify.formal_menu.runtime_no_legacy_carrier_guard.prod:",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.formal_menu.runtime_no_legacy_carrier_guard.prod missing dependency: guard.prod.readonly",
            errors,
        )

    def test_prod_formal_list_guard_must_keep_readonly_parameter(self) -> None:
        target_with_token = _target(
            "verify.formal_list_surface.no_test_placeholder_guard.prod",
            guard.REQUIRED_TARGET_DEPS["verify.formal_list_surface.no_test_placeholder_guard.prod"],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.formal_list_surface.no_test_placeholder_guard.prod"],
        )
        target_without_token = target_with_token.replace(
            "PROD_READONLY_VERIFY=1",
            "",
        )
        make_text = _make_text().replace(target_with_token, target_without_token)
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.formal_list_surface.no_test_placeholder_guard.prod missing command token: PROD_READONLY_VERIFY=1",
            errors,
        )

    def test_doc_must_keep_attachment_production_gate_commands(self) -> None:
        doc_text = _doc_text().replace("make verify.attachment_upload.surface_manifest.prod", "")
        errors = guard.validate(doc_text, _make_text())
        self.assertIn("doc missing token: make verify.attachment_upload.surface_manifest.prod", errors)

    def test_attachment_custody_prod_gate_must_keep_readonly_dependency(self) -> None:
        make_text = _make_text().replace(
            "history.attachment.custody.probe.prod: guard.prod.readonly",
            "history.attachment.custody.probe.prod:",
        )
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("history.attachment.custody.probe.prod missing dependency: guard.prod.readonly", errors)

    def test_online_attachment_custody_prod_gate_must_keep_evidence_script(self) -> None:
        make_text = _make_text().replace("scripts/verify/legacy_online_attachment_custody_evidence.py", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.legacy_online_attachment.custody.evidence.prod missing command token: scripts/verify/legacy_online_attachment_custody_evidence.py",
            errors,
        )

    def test_attachment_upload_manifest_prod_gate_must_keep_required_models(self) -> None:
        make_text = _make_text().replace("LEGACY_ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.attachment_upload.surface_manifest.prod missing command token: LEGACY_ATTACHMENT_UPLOAD_SURFACE_REQUIRED_MODELS",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
