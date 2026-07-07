# -*- coding: utf-8 -*-

from .project_execution_next_actions_builder import ProjectExecutionNextActionsBuilder
from .project_execution_readiness_precheck_builder import ProjectExecutionReadinessPrecheckBuilder
from .project_execution_tasks_builder import ProjectExecutionTasksBuilder


BUILDERS = (
    ProjectExecutionTasksBuilder,
    ProjectExecutionReadinessPrecheckBuilder,
    ProjectExecutionNextActionsBuilder,
)
