# -*- coding: utf-8 -*-
"""Rule registry and base class."""
from abc import ABC, abstractmethod


class DataRule(ABC):
    name = "base_rule"
    level = "info"
    description = ""

    def __init__(self, env):
        self.env = env

    @abstractmethod
    def run(self):
        """Execute rule and return dict with checked/issues."""
        raise NotImplementedError


_RULES = []


def register(rule_cls):
    _RULES.append(rule_cls)
    return rule_cls


def get_registered_rules():
    return _RULES
