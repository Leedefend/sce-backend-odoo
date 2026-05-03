# -*- coding: utf-8 -*-

from .project_plan_next_actions_builder import ProjectPlanNextActionsBuilder
from .project_plan_summary_builder import ProjectPlanSummaryBuilder
from .project_plan_tasks_builder import ProjectPlanTasksBuilder


BUILDERS = (
    ProjectPlanSummaryBuilder,
    ProjectPlanTasksBuilder,
    ProjectPlanNextActionsBuilder,
)
