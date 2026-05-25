# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from odoo.tools import convert
from odoo.tools.misc import file_path


BASE_SEED_FILES: List[str] = [
    "data/base/00_dictionary.xml",
    "data/base/dictionary_demo.xml",
    "data/base/cost_demo.xml",
    "data/base/10_partners.xml",
    "data/base/20_projects.xml",
    "data/base/25_project_tasks.xml",
]


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
    "s60_project_cockpit": {
        "sequence": 60,
        "files": [
            "data/scenario/s60_project_cockpit/10_cockpit_business_facts.xml",
        ],
    },
    "s70_daily_business_surface": {
        "sequence": 70,
        "files": [
            "data/scenario/s70_daily_business_surface/10_daily_business_records.xml",
        ],
    },
    "s80_execution_management_surface": {
        "sequence": 80,
        "files": [
            "data/scenario/s80_execution_management_surface/10_execution_management_records.xml",
        ],
    },
    "s85_admin_finance_surface": {
        "sequence": 85,
        "files": [
            "data/scenario/s85_admin_finance_surface/10_admin_finance_records.xml",
        ],
    },
    "s86_tender_rental_finance_surface": {
        "sequence": 86,
        "files": [
            "data/scenario/s86_tender_rental_finance_surface/10_tender_rental_finance_records.xml",
        ],
    },
    "s87_resource_contract_surface": {
        "sequence": 87,
        "files": [
            "data/scenario/s87_resource_contract_surface/10_resource_contract_records.xml",
        ],
    },
    "s88_output_invoice_surface": {
        "sequence": 88,
        "files": [
            "data/scenario/s88_output_invoice_surface/10_output_invoice_records.xml",
        ],
    },
    "s89_quality_safety_surface": {
        "sequence": 89,
        "files": [
            "data/scenario/s89_quality_safety_surface/10_quality_safety_records.xml",
        ],
    },
    "s90_users_roles": {
        "sequence": 90,
        "files": [
            "data/scenario/s90_users_roles/10_users.xml",
        ],
    },
}

SCENARIO_ALIASES = {
    "project_normal": "s60_project_cockpit",
    "project_over_budget": "s60_project_cockpit",
    "project_payment_delay": "s60_project_cockpit",
}

SCENARIO_PROFILES: Dict[str, Dict[str, object]] = {
    "project_normal": {
        "label": "正常项目",
        "release_ready": True,
        "showcase_project": "展厅-智慧园区运营中心",
        "expected_risk": "EXECUTION_COST_MISSING",
    },
    "project_over_budget": {
        "label": "超预算项目",
        "release_ready": True,
        "showcase_project": "展厅-产线升级改造工程",
        "expected_risk": "PAYMENT_EXCEEDS_COST",
    },
    "project_payment_delay": {
        "label": "付款风险项目",
        "release_ready": True,
        "showcase_project": "展厅-装配式住宅试点",
        "expected_risk": "PAYMENT_MISSING",
    },
}


RELEASE_SCENARIOS: List[str] = [
    "s00_min_path",
    "s10_contract_payment",
    "s20_settlement_clearing",
    "s30_settlement_workflow",
    "s60_project_cockpit",
    "s70_daily_business_surface",
    "s80_execution_management_surface",
    "s85_admin_finance_surface",
    "s86_tender_rental_finance_surface",
    "s87_resource_contract_surface",
    "s88_output_invoice_surface",
    "s89_quality_safety_surface",
    "s90_users_roles",
]


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
    ensure_base: bool = True,
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

    scenario = SCENARIO_ALIASES.get(scenario, scenario)

    if scenario not in SCENARIOS:
        known = ", ".join(sorted(SCENARIOS.keys()))
        raise ValueError(f"unknown scenario '{scenario}'. known: {known}")

    if scenario == "s90_users_roles":
        _ensure_demo_user_xmlids(env)
    if scenario == "s50_repairable_paths":
        _reset_s50_repairable_records(env)

    module = "smart_construction_demo"
    if ensure_base:
        load_base_seed(env, mode=mode)

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


def load_base_seed(env, mode: str = "update") -> None:
    """
    Recreate shared demo base records that scenarios reference.

    The module install path intentionally runs user_acceptance_project_cleanup
    after loading the default demo records, which removes the base projects and
    their XMLIDs. Scenario replay must restore that base first.
    """
    module = "smart_construction_demo"
    idref = {}
    for relpath in BASE_SEED_FILES:
        abspath = file_path(f"{module}/{relpath}")
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
    load_base_seed(env, mode=mode)
    registry = _normalize_registry()
    ordered = sorted(
        registry.items(),
        key=lambda item: (item[1]["sequence"], item[0]),
    )
    for scenario, _spec in ordered:
        load_scenario(env, scenario, mode=mode, ensure_base=False)


def load_release_seed(env, mode: str = "update") -> None:
    """
    Load release-grade demo seed set.

    Excludes process-only failure drills (s40/s50), keeps business-complete
    walkthrough path for product demo and acceptance.
    """
    known = set(SCENARIOS.keys())
    load_base_seed(env, mode=mode)
    for scenario in RELEASE_SCENARIOS:
        if scenario not in known:
            raise ValueError(f"release scenario '{scenario}' not registered")
        load_scenario(env, scenario, mode=mode, ensure_base=False)


def _ensure_demo_user_xmlids(env) -> None:
    module = "smart_construction_demo"
    login_to_xmlid = {
        "demo_pm": "sc_demo_user_pm",
        "demo_finance": "sc_demo_user_finance",
        "demo_cost": "sc_demo_user_cost",
        "demo_audit": "sc_demo_user_audit",
        "demo_readonly": "sc_demo_user_readonly",
        "svc_e2e_smoke": "sc_demo_user_e2e_smoke",
        "sc_test_admin": "sc_demo_user_test_admin",
    }
    Users = env["res.users"].sudo().with_context(active_test=False)
    imd = env["ir.model.data"].sudo()
    for login, xmlid in login_to_xmlid.items():
        user = Users.search([("login", "=", login)], limit=1)
        if not user:
            continue
        if not user.active:
            user.write({"active": True})
        existing = imd.search(
            [("module", "=", module), ("name", "=", xmlid)],
            limit=1,
        )
        if existing:
            if existing.model != "res.users" or existing.res_id != user.id:
                existing.write({"model": "res.users", "res_id": user.id})
            continue
        imd.create(
            {
                "module": module,
                "name": xmlid,
                "model": "res.users",
                "res_id": user.id,
                "noupdate": True,
            }
        )


def _reset_s50_repairable_records(env) -> None:
    """Replay S50 from its intended bad seed without mutating guarded fields."""
    for xmlid in (
        "smart_construction_demo.sc_demo_payment_050_001",
        "smart_construction_demo.sc_demo_settlement_line_050_001",
        "smart_construction_demo.sc_demo_settlement_050_001",
    ):
        model_name, res_id = env["ir.model.data"]._xmlid_to_res_model_res_id(
            xmlid,
            raise_if_not_found=False,
        )
        if not model_name or not res_id:
            continue
        record = env[model_name].sudo().browse(res_id).exists()
        if record:
            record.with_context(allow_transition=True, allow_contract_change=True).unlink()
    env.cr.commit()
