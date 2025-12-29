# -*- coding: utf-8 -*-
from __future__ import annotations

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
}


def load_scenario(env, scenario: str, mode: str = "update") -> None:
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
    files = SCENARIOS[scenario]

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
