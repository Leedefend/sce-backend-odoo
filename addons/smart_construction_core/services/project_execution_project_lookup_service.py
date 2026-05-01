# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger(__name__)


class ProjectExecutionProjectLookupService:
    def __init__(self, env):
        self.env = env

    @staticmethod
    def _log_exception(event: str, **context: Any) -> None:
        _logger.exception("project.execution.advance.%s context=%s", str(event or "unknown"), context)

    def resolve_project(self, *, project_id: int, trace_id: str = ""):
        try:
            project_model = self.env["project.project"]
            return project_model.browse(int(project_id or 0)).exists()
        except Exception:
            self._log_exception("project_lookup_failed", project_id=int(project_id or 0), trace_id=str(trace_id or ""))
            return False
