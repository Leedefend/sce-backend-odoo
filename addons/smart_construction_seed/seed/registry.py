# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True)
class SeedStep:
    name: str
    description: str
    run: Callable  # (env) -> None


_REGISTRY: Dict[str, SeedStep] = {}
_PROFILES: Dict[str, List[str]] = {
    "base": [
        "sanity",
        "tax_defaults",
        "icp_defaults",
        "dictionary_min",
    ],
    "demo_full": [
        "sanity",
        "dictionary",
        "tax_defaults",
        "demo_10_users",
        "demo_user_prefs",
        "demo_20_projects",
        "demo_30_tenders",
        "demo_40_contracts",
        "demo_50_boq_wbs",
        "demo_60_attachments",
        "demo_90_verify",
    ],
}


def register(step: SeedStep) -> None:
    if step.name in _REGISTRY:
        raise ValueError(f"seed step already registered: {step.name}")
    _REGISTRY[step.name] = step


def list_steps() -> List[str]:
    return sorted(_REGISTRY.keys())


def list_profiles() -> List[str]:
    return sorted(_PROFILES.keys())


def _resolve_names(names: List[str]) -> List[SeedStep]:
    missing = [n for n in names if n not in _REGISTRY]
    if missing:
        raise ValueError(f"unknown seed steps: {missing}; available={list_steps()}")
    return [_REGISTRY[n] for n in names]


def resolve_steps(selected: str) -> List[SeedStep]:
    """selected: 'all', profile:<name>, <profile_name> or comma-separated names"""
    if not selected or selected.strip().lower() == "all":
        return [_REGISTRY[k] for k in list_steps()]
    sel = selected.strip()
    if sel.startswith("profile:"):
        profile = sel.split(":", 1)[1].strip()
        if profile not in _PROFILES:
            raise ValueError(f"unknown seed profile: {profile}; available={list_profiles()}")
        return _resolve_names(_PROFILES[profile])
    if sel in _PROFILES:
        return _resolve_names(_PROFILES[sel])
    names = [x.strip() for x in sel.split(",") if x.strip()]
    return _resolve_names(names)


def run_steps(env, selected: str) -> List[str]:
    executed: List[str] = []
    for step in resolve_steps(selected):
        step.run(env)
        executed.append(step.name)
    return executed
