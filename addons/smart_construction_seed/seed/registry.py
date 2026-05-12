# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True)
class SeedStep:
    name: str
    description: str
    run: Callable  # (env) -> None


_REGISTRY: Dict[str, SeedStep] = {}
_DEMO_STEP_MARKERS = ("demo", "showroom")
_DEMO_DB_NAMES = {"sc_demo", "sc_test"}
_PROFILES: Dict[str, List[str]] = {
    "base": [
        "sanity",
        "company_currency_cny",
        "tax_defaults",
        "icp_defaults",
        "dictionary_min",
        "project_stages_min",
        "users_bootstrap",
    ],
    "demo_full": [
        "sanity",
        "dictionary",
        "company_currency_cny",
        "tax_defaults",
        "demo_10_users",
        "demo_user_prefs",
        "demo_20_projects",
        "demo_30_tenders",
        "demo_40_contracts",
        "demo_50_boq_wbs",
        "demo_60_attachments",
        "z_demo_full_my_work",
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


def _is_demo_allowed(env) -> bool:
    if os.getenv("SC_ALLOW_DEMO_DATA") in ("1", "true", "True", "yes", "YES"):
        return True
    db_name = str(getattr(getattr(env, "cr", None), "dbname", "") or "").strip()
    if db_name in _DEMO_DB_NAMES or db_name.startswith("sc_demo_") or db_name.startswith("sc_test_"):
        return True
    try:
        ICP = env["ir.config_parameter"].sudo()
        return ICP.get_param("sc.login.env") == "demo" or ICP.get_param("sc.bootstrap.mode") == "demo"
    except Exception:
        return False


def _is_demo_step(step_name: str) -> bool:
    normalized = str(step_name or "").strip().lower()
    return any(marker in normalized for marker in _DEMO_STEP_MARKERS)


def _guard_demo_steps(env, steps: List[SeedStep]) -> None:
    demo_steps = [step.name for step in steps if _is_demo_step(step.name)]
    if demo_steps and not _is_demo_allowed(env):
        db_name = str(getattr(getattr(env, "cr", None), "dbname", "") or "").strip()
        raise ValueError(
            "demo seed steps are forbidden outside demo databases: "
            f"db={db_name or '-'} steps={demo_steps}. "
            "Use sc_demo/sc_test or set SC_ALLOW_DEMO_DATA=1 for an intentional demo rebuild."
        )


def run_steps(env, selected: str) -> List[str]:
    executed: List[str] = []
    steps = resolve_steps(selected)
    _guard_demo_steps(env, steps)
    for step in steps:
        step.run(env)
        executed.append(step.name)
    return executed
