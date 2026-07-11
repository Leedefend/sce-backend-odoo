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
    return "\n".join(guard.REQUIRED_DOC_TOKENS)


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

    def test_duplicate_required_target_fails(self) -> None:
        make_text = _make_text() + "\n" + _target("verify.frontend.product_language.guard", ["guard.prod.forbid"])
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("Makefile duplicate target: verify.frontend.product_language.guard", errors)

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

    def test_prod_readiness_must_keep_readonly_parameters(self) -> None:
        make_text = _make_text().replace("BUSINESS_SYSTEM_READINESS_PROD_READONLY=1", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_system.usability_readiness.prod missing command token: BUSINESS_SYSTEM_READINESS_PROD_READONLY=1",
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


if __name__ == "__main__":
    unittest.main()
