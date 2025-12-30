# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from odoo.tools import convert
from odoo.tools.misc import file_path


# Scenario registry: scenario_name -> ordered xml file list (relative under module root)
SCENARIOS: Dict[str, List[str]] = {
    # S00 is "default baseline" (usually already loaded by manifest, but loader can load too)
    "s00_min_path": [
        "data/scenario/s00_min_path/10_project_boq.xml",
        "data/scenario/s00_min_path/20_project_links.xml",
        "data/scenario/s00_min_path/30_project_revenue.xml",
    ],
    # S10 contract payment path (optional scenario)
    "s10_contract_payment": [
        "data/scenario/s10_contract_payment/10_contracts.xml",
        "data/scenario/s10_contract_payment/20_payment_requests.xml",
        "data/scenario/s10_contract_payment/30_invoices.xml",
    ],
    "s20_settlement_clearing": {
        "sequence": 20,
        "files": [
            "data/scenario/s20_settlement_clearing/10_payments.xml",
            "data/scenario/s20_settlement_clearing/30_settlement.xml",
            "data/scenario/s20_settlement_clearing/20_clearing.xml",
        ],
    },
    "s30_settlement_workflow": {
        "sequence": 30,
        "files": [
            "data/scenario/s30_settlement_workflow/10_settlement_seed.xml",
            "data/scenario/s30_settlement_workflow/20_settlement_actions.xml",
            "data/scenario/s30_settlement_workflow/30_assert_state.xml",
        ],
    },
    "s40_failure_paths": {
        "sequence": 40,
        "files": [
            "data/scenario/s40_failure_paths/10_invalid_settlement.xml",
            "data/scenario/s40_failure_paths/20_invalid_amounts.xml",
            "data/scenario/s40_failure_paths/30_invalid_links.xml",
        ],
    },
    "s50_repairable_paths": {
        "sequence": 50,
        "files": [
            "data/scenario/s50_repairable_paths/10_bad_seed.xml",
            "data/scenario/s50_repairable_paths/20_fix_patch.xml",
            "data/scenario/s50_repairable_paths/30_assert_state.xml",
        ],
    },
    "s90_users_roles": {
        "sequence": 90,
        "files": [
            "data/scenario/s90_users_roles/10_users.xml",
        ],
    },
}


def _normalize_registry() -> Dict[str, Dict[str, List[str] | int]]:
    """
    Normalize SCENARIOS to:
      {name: {"sequence": int, "files": List[str]}}
    Backward compatible with legacy list-only entries.
    """
    normalized: Dict[str, Dict[str, List[str] | int]] = {}
    for name, spec in SCENARIOS.items():
        if isinstance(spec, dict):
            files = spec.get("files") or []
            seq = int(spec.get("sequence", 0))
        else:
            files = spec
            seq = 0
        normalized[name] = {
            "sequence": seq,
            "files": files,
        }
    return normalized


def _filter_files(files: List[str], step: str | None) -> List[str]:
    if not step or step == "all":
        return files
    step = step.strip().lower()
    if step == "bad":
        prefixes = ("10_",)
    elif step == "fix":
        prefixes = ("20_", "30_")
    else:
        raise ValueError(f"unknown step '{step}'. use bad|fix|all")

    filtered = [
        relpath for relpath in files if Path(relpath).name.startswith(prefixes)
    ]
    if not filtered:
        raise ValueError(f"no files matched step '{step}'")
    return filtered


def load_scenario(
    env,
    scenario: str,
    mode: str = "update",
    step: str | None = None,
) -> None:
    """
    Load a demo scenario XML files into current DB using Odoo converter.
    - env: Odoo env from odoo shell
    - scenario: key in SCENARIOS
    - mode: 'init' or 'update'. Use update for idempotent reloads.
    """
    scenario = (scenario or "").strip()
    if not scenario:
        raise ValueError("scenario is required, e.g. 's10_contract_payment'")

    if scenario not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS.keys()))
        raise ValueError(f"unknown scenario '{scenario}'. known: {known}")

    module = "smart_construction_demo"
    registry = _normalize_registry()
    files = registry[scenario]["files"]
    files = _filter_files(files, step)

    # idref is used by Odoo converter to resolve xmlids in-file
    idref = {}

    for relpath in files:
        abspath = file_path(f"{module}/{relpath}")

        # convert_file will parse XML and create/update records.
        # mode='update' makes this idempotent-friendly for repeated loads.
        convert.convert_file(
            env,
            module,
            abspath,
            idref,
            mode=mode,
            noupdate=False,
            kind="data",
        )

    env.cr.commit()


def load_all(env, mode: str = "update") -> None:
    """
    Load all registered scenarios in stable order.
    """
    registry = _normalize_registry()
    ordered = sorted(
        registry.items(),
        key=lambda item: (item[1]["sequence"], item[0]),
    )
    for scenario, _spec in ordered:
        load_scenario(env, scenario, mode=mode)
