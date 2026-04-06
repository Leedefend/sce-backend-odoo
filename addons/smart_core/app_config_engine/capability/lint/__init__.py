# -*- coding: utf-8 -*-

from .schema_lint import run_schema_lint
from .ownership_lint import run_ownership_lint

__all__ = [
    "run_schema_lint",
    "run_ownership_lint",
]
