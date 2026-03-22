# -*- coding: utf-8 -*-

from .project_header_builder import ProjectHeaderBuilder
from .project_metrics_builder import ProjectMetricsBuilder
from .project_progress_builder import ProjectProgressBuilder
from .project_contract_builder import ProjectContractBuilder
from .project_cost_builder import ProjectCostBuilder
from .project_finance_builder import ProjectFinanceBuilder
from .project_risk_builder import ProjectRiskBuilder
from .project_next_actions_builder import ProjectNextActionsBuilder


BUILDERS = (
    ProjectHeaderBuilder,
    ProjectMetricsBuilder,
    ProjectProgressBuilder,
    ProjectContractBuilder,
    ProjectCostBuilder,
    ProjectFinanceBuilder,
    ProjectRiskBuilder,
    ProjectNextActionsBuilder,
)
