#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import unittest

import productization_system_closure_topic_guard as guard


def _doc_text() -> str:
    return "\n".join(guard.REQUIRED_DOC_TOKENS)


def _target(name: str, deps: list[str], body: list[str] | None = None) -> str:
    lines = [f"{name}: {' '.join(deps)}"]
    lines.extend(f"\t@{line}" for line in body or [])
    return "\n".join(lines) + "\n"


def _make_text() -> str:
    targets = [
        _target("verify.productization.system_closure.topic_guard", ["guard.prod.forbid"]),
        _target(
            "verify.system_user_experience.quick",
            [
                "guard.prod.forbid",
                *guard.REQUIRED_QUICK_DEPS,
            ],
            guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.quick"],
        ),
        _target("verify.system_user_experience.visible_surface_visual_coverage", ["guard.prod.forbid"], guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.visible_surface_visual_coverage"]),
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
        _target("verify.frontend.product_language.guard", ["guard.prod.forbid"]),
        _target(
            "verify.business_config.unit",
            ["guard.prod.forbid", *guard.REQUIRED_TARGET_DEPS["verify.business_config.unit"]],
        ),
        _target(
            "verify.business_config.config_workbench_operation_quick",
            ["guard.prod.forbid", *guard.REQUIRED_TARGET_DEPS["verify.business_config.config_workbench_operation_quick"]],
        ),
        _target("verify.system_user_experience.shell_acceptance", ["guard.prod.forbid"], guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.shell_acceptance"]),
        _target("verify.system_user_experience.business_form_user_perspective", ["guard.prod.forbid"], guard.REQUIRED_TARGET_BODY_TOKENS["verify.system_user_experience.business_form_user_perspective"]),
    ]
    return "\n\n".join(targets)


class ProductizationSystemClosureTopicGuardTests(unittest.TestCase):
    def test_complete_minimal_fixture_passes(self) -> None:
        self.assertEqual([], guard.validate(_doc_text(), _make_text()))

    def test_missing_quick_dependency_fails(self) -> None:
        make_text = _make_text().replace(" verify.formal_list_surface.no_test_placeholder_guard", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn("quick gate missing dependency: verify.formal_list_surface.no_test_placeholder_guard", errors)

    def test_prod_readiness_must_keep_readonly_parameters(self) -> None:
        make_text = _make_text().replace("BUSINESS_SYSTEM_READINESS_PROD_READONLY=1", "")
        errors = guard.validate(_doc_text(), make_text)
        self.assertIn(
            "verify.business_system.usability_readiness.prod missing command token: BUSINESS_SYSTEM_READINESS_PROD_READONLY=1",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
