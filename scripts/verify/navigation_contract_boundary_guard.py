#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_contains(path: str, needle: str, message: str, failures: list[str]) -> None:
    if needle not in read(path):
        failures.append(f"{path}: {message}")


def assert_not_contains(path: str, needle: str, message: str, failures: list[str]) -> None:
    if needle in read(path):
        failures.append(f"{path}: {message}")


def main() -> int:
    failures: list[str] = []

    assert_contains(
        "addons/smart_core/core/delivery_menu_defaults.py",
        "normalize_entry_target",
        "delivery menus must use the backend navigation entry_target normalizer",
        failures,
    )
    assert_contains(
        "addons/smart_core/core/navigation_entry_target.py",
        "def build_scene_entry_target",
        "backend must own formal scene entry_target construction",
        failures,
    )
    assert_contains(
        "addons/smart_core/core/navigation_entry_target.py",
        "def build_compatibility_entry_target",
        "backend must own compatibility entry_target construction",
        failures,
    )
    assert_contains(
        "addons/smart_construction_core/core_extension_policy_maps.py",
        '"smart_construction_core.menu_sc_dashboard_cost_cockpit_fact": "cost.control"',
        "cost cockpit menu must be declared as a backend scene target",
        failures,
    )
    assert_contains(
        "addons/smart_construction_core/core_extension_policy_maps.py",
        '"smart_construction_core.action_sc_dashboard_cost_cockpit_fact": "cost.control"',
        "cost cockpit action must be declared as a backend scene target",
        failures,
    )
    assert_contains(
        "addons/smart_core/delivery/menu_target_interpreter_service.py",
        "normalize_entry_target",
        "menu interpreter must reuse the backend navigation entry_target normalizer",
        failures,
    )
    assert_not_contains(
        "addons/smart_core/delivery/menu_target_interpreter_service.py",
        "def _build_entry_target",
        "menu interpreter must not keep a second entry_target schema",
        failures,
    )
    for path in (
        "addons/smart_core/governance/scene_normalizer.py",
        "addons/smart_core/identity/identity_resolver.py",
        "addons/smart_core/core/system_init_payload_builder.py",
    ):
        assert_not_contains(
            path,
            "def _build_entry_target",
            "backend surfaces must reuse navigation_entry_target instead of local entry_target builders",
            failures,
        )
    assert_contains(
        "addons/smart_core/handlers/execute_button.py",
        "normalize_odoo_action_result",
        "button execution results must be wrapped by backend entry_target contract",
        failures,
    )
    assert_contains(
        "addons/smart_construction_core/services/execute_button_service.py",
        "normalize_odoo_action_result",
        "legacy execute button service must wrap next_action with entry_target",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/app/resolvers/menuResolverCore.js",
        "resolveEntryTarget(node)",
        "menu resolver must consume backend entry_target before legacy fields",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/services/action_service.ts",
        "action.entry_target",
        "action navigation must consume explicit entry_target when present",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/app/runtime/actionViewContractActionRuntime.ts",
        "resolveContractActionResponseNavigation",
        "contract action runtime must navigate from backend entry_target response",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/layouts/AppShell.vue",
        "buildEntryTargetRouteTarget",
        "sidebar menu selection must route through backend entry_target",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/layouts/AppShell.vue",
        "buildMenuSelectionQuery",
        "sidebar menu selection must sanitize route query instead of inheriting business context",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/layouts/AppShell.vue",
        "query: menuQuery",
        "sidebar menu selection must use sanitized menu query",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/layouts/AppShell.vue",
        "query: route.query",
        "sidebar menu selection must not leak current page query such as project_id",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/views/MenuView.vue",
        "buildEntryTargetRouteTarget",
        "menu route resolution must route through backend entry_target",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/views/ActionView.vue",
        "buildEntryTargetRouteTarget",
        "menu-only action redirects must route through backend entry_target",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/pages/contractForm/useActionResponseNavigation.ts",
        "resultRecord?.entry_target",
        "contract form button responses must consume backend entry_target",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/services/action_service.ts",
        "buildEntryTargetRouteTarget",
        "action service must route through backend entry_target",
        failures,
    )
    assert_contains(
        "frontend/apps/web/src/app/routeQuery.ts",
        "buildCanonicalSceneRouteTarget",
        "scene route creation must stay centralized",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/router/index.ts",
        "getSceneRegistry",
        "router must not infer scene identity by scanning scene registry",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/router/index.ts",
        ".find((scene)",
        "router must not guess scene identity from action/menu ids",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/router/index.ts",
        "ProjectManagementDashboardView",
        "project.management must use generic SceneView rather than a frontend business-specific route component",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/views/SceneView.vue",
        "ProjectManagementDashboardView",
        "generic scene rendering must not embed a project-management-specific surface",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/views/SceneView.vue",
        "shouldRenderDashboardSurface",
        "scene dashboard pages must resolve to backend targets instead of frontend dashboard shortcuts",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/router/index.ts",
        "scene-project-management",
        "project.management must not be captured by a dedicated frontend route",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/app/routeQuery.ts",
        "sceneKey === 'projects.list'",
        "canonical route helper must not contain project-specific defaults",
        failures,
    )
    assert_not_contains(
        "frontend/apps/web/src/app/resolvers/menuResolverCore.js",
        "explicitSceneKey ===",
        "menu resolver must not whitelist scene keys in frontend",
        failures,
    )

    if failures:
        print("navigation contract boundary guard failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("navigation contract boundary guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
