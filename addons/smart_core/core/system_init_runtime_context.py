# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class SystemInitRuntimeContext:
    env: Any
    user: Any
    params: dict
    data: dict
    nav_tree: list
    scene_channel: str
    rollback_active: bool
    trace_id: str
    diagnostics_collector: Any
    scene_diagnostics: dict
    load_scene_contract_fn: Callable
    load_scenes_fallback_fn: Callable
    merge_missing_scenes_fn: Callable
    append_resolve_error_fn: Callable
