# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


def register_scene_content_providers(registry, addons_root: Path) -> None:
    """Register construction-domain scene content providers.

    This module is loaded by `smart_scene` platform registry engine.
    """

    scene_module = "smart_construction_scene"

    registry.register_spec(
        scene_key="workspace.home",
        provider_key="construction.workspace_home.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "workspace_home_scene_content.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="project.dashboard",
        provider_key="construction.project_dashboard.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "project_dashboard_scene_content.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="project.management",
        provider_key="construction.project_management_dashboard.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "project_dashboard_scene_content.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="scene.registry",
        provider_key="construction.scene_registry.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "profiles" / "scene_registry_content.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="projects.list",
        provider_key="construction.projects_list_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "projects_list_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="projects.intake",
        provider_key="construction.project_intake_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "project_intake_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="projects.ledger",
        provider_key="construction.projects_ledger_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "projects_ledger_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="projects.detail",
        provider_key="construction.projects_detail_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "projects_detail_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="cost.project_budget",
        provider_key="construction.cost_project_budget_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "cost_project_budget_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="task.center",
        provider_key="construction.task_center_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "task_center_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="task.board",
        provider_key="construction.task_board_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "task_board_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="finance.center",
        provider_key="construction.finance_center_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "finance_center_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="finance.workspace",
        provider_key="construction.finance_workspace_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "finance_workspace_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="finance.payment_requests",
        provider_key="construction.payment_entry_workbench_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "payment_entry_workbench_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="payments.approval",
        provider_key="construction.approval_workbench_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "approval_workbench_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="contract.center",
        provider_key="construction.contract_center_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "contract_center_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="contracts.workspace",
        provider_key="construction.contracts_workspace_provider.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "contracts_workspace_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="enterprise.company",
        provider_key="construction.enterprise_bootstrap_provider.company.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "enterprise_bootstrap_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="enterprise.department",
        provider_key="construction.enterprise_bootstrap_provider.department.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "enterprise_bootstrap_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="enterprise.user",
        provider_key="construction.enterprise_bootstrap_provider.user.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "enterprise_bootstrap_provider.py",
        priority=300,
        source="industry_registration",
    )
    registry.register_spec(
        scene_key="enterprise.post",
        provider_key="construction.enterprise_bootstrap_provider.post.v1",
        module_name=scene_module,
        provider_path=addons_root / scene_module / "providers" / "enterprise_bootstrap_provider.py",
        priority=300,
        source="industry_registration",
    )
