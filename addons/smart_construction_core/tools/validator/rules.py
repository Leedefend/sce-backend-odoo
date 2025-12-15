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

    def __init__(self, env):
        self.env = env
        self._validate_meta()

    def _validate_meta(self):
        if not self.code or not self.title:
            raise ValueError(f"Rule meta missing: code/title in {self.__class__.__name__}")
        if self.severity not in SEVERITY_LEVELS:
            raise ValueError(f"Invalid severity={self.severity} in {self.code}")

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
