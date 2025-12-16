# -*- coding: utf-8 -*-
"""Rule registry and base class."""
from dataclasses import dataclass
from typing import Any, Dict, List, Set
from abc import ABC, abstractmethod

SEVERITY_ERROR = "ERROR"
SEVERITY_WARN = "WARN"
SEVERITY_INFO = "INFO"
SEVERITY_LEVELS: Set[str] = {SEVERITY_ERROR, SEVERITY_WARN, SEVERITY_INFO}


@dataclass
class RuleResult:
    code: str
    title: str
    severity: str
    checked: int
    issues: List[Dict[str, Any]]


class BaseRule(ABC):
    code: str = None
    title: str = None
    severity: str = SEVERITY_WARN

    def __init__(self, env, scope=None):
        self.env = env
        self.scope = scope or {}
        self._validate_meta()

    def _validate_meta(self):
        if not self.code or not self.title:
            raise ValueError(f"Rule meta missing: code/title in {self.__class__.__name__}")
        if self.severity not in SEVERITY_LEVELS:
            raise ValueError(f"Invalid severity={self.severity} in {self.code}")

    # ---- scope helpers ----
    def _scope_domain(self, model_name: str):
        """Build domain honoring validator scope.

        约定：
        - res_model/res_ids：限定校验目标记录
        - project_id/company_id：进一步收敛到项目/公司维度
        """
        scope = self.scope or {}
        res_model = scope.get("res_model")
        res_ids = scope.get("res_ids") or []
        project_id = scope.get("project_id")
        company_id = scope.get("company_id")

        Model = self.env[model_name]
        domain = []
        if res_model == model_name and res_ids:
            domain.append(("id", "in", res_ids))
        if project_id and "project_id" in Model._fields:
            domain.append(("project_id", "=", project_id))
        if company_id and "company_id" in Model._fields:
            domain.append(("company_id", "=", company_id))
        return domain

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Execute rule and return dict with checked/issues."""
        raise NotImplementedError


_RULES: List[type] = []


def register(rule_cls):
    _RULES.append(rule_cls)
    return rule_cls


def get_registered_rules():
    return _RULES
