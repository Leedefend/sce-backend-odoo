# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True)
class SeedStep:
    name: str
    description: str
    run: Callable  # (env) -> None


_REGISTRY: Dict[str, SeedStep] = {}


def register(step: SeedStep) -> None:
    if step.name in _REGISTRY:
        raise ValueError(f"seed step already registered: {step.name}")
    _REGISTRY[step.name] = step


def list_steps() -> List[str]:
    return sorted(_REGISTRY.keys())


def resolve_steps(selected: str) -> List[SeedStep]:
    """selected: 'all' or comma-separated names"""
    if not selected or selected.strip().lower() == "all":
        return [_REGISTRY[k] for k in list_steps()]
    names = [x.strip() for x in selected.split(",") if x.strip()]
    missing = [n for n in names if n not in _REGISTRY]
    if missing:
        raise ValueError(f"unknown seed steps: {missing}; available={list_steps()}")
    return [_REGISTRY[n] for n in names]


def run_steps(env, selected: str) -> List[str]:
    executed: List[str] = []
    for step in resolve_steps(selected):
        step.run(env)
        executed.append(step.name)
    return executed
