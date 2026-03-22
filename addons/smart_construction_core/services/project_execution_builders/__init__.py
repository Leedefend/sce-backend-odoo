# -*- coding: utf-8 -*-

from .project_execution_next_actions_builder import ProjectExecutionNextActionsBuilder
from .project_execution_pilot_precheck_builder import ProjectExecutionPilotPrecheckBuilder
from .project_execution_tasks_builder import ProjectExecutionTasksBuilder


BUILDERS = (
    ProjectExecutionTasksBuilder,
    ProjectExecutionPilotPrecheckBuilder,
    ProjectExecutionNextActionsBuilder,
)
