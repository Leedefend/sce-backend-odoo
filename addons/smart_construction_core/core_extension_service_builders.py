# -*- coding: utf-8 -*-
from __future__ import annotations


def scene_package_service_class():
    from odoo.addons.smart_construction_scene.services.scene_package_service import (
        ScenePackageService,
    )

    return ScenePackageService


def scene_governance_service_class():
    from odoo.addons.smart_construction_scene.services.scene_governance_service import (
        SceneGovernanceService,
    )

    return SceneGovernanceService


def describe_project_capabilities(env, project):
    from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
        LifecycleCapabilityService,
    )

    return LifecycleCapabilityService(env).describe_project(project)


def build_portal_dashboard(env):
    from odoo.addons.smart_construction_core.services.portal_dashboard_service import (
        PortalDashboardService,
    )

    return PortalDashboardService(env).build_dashboard()


def build_capability_matrix(env):
    from odoo.addons.smart_construction_core.services.capability_matrix_service import (
        CapabilityMatrixService,
    )

    return CapabilityMatrixService(env).build_matrix()


def get_project_insight(env, record, scene):
    from odoo.addons.smart_construction_core.services.insight.project_insight_service import (
        ProjectInsightService,
    )

    return ProjectInsightService(env).get_insight(record, scene=scene)


def build_portal_execute_button_contract(env, model, res_id, method):
    from odoo.addons.smart_construction_core.services.portal_execute_button_service import (
        PortalExecuteButtonService,
    )

    return PortalExecuteButtonService(env).build_contract(
        model=model,
        res_id=res_id,
        method=method,
    )


def build_project_execution_service(env):
    from odoo.addons.smart_construction_core.services.project_execution_service import (
        ProjectExecutionService,
    )

    return ProjectExecutionService(env)


def build_project_dashboard_service(env):
    from odoo.addons.smart_construction_core.services.project_dashboard_service import (
        ProjectDashboardService,
    )

    return ProjectDashboardService(env)


def build_project_plan_bootstrap_service(env):
    from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import (
        ProjectPlanBootstrapService,
    )

    return ProjectPlanBootstrapService(env)


def build_cost_tracking_service(env):
    from odoo.addons.smart_construction_core.services.cost_tracking_service import (
        CostTrackingService,
    )

    return CostTrackingService(env)


def build_payment_slice_service(env):
    from odoo.addons.smart_construction_core.services.payment_slice_service import (
        PaymentSliceService,
    )

    return PaymentSliceService(env)


def build_settlement_slice_service(env):
    from odoo.addons.smart_construction_core.services.settlement_slice_service import (
        SettlementSliceService,
    )

    return SettlementSliceService(env)
