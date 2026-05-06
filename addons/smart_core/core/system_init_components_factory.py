# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.contract_assembler import ContractAssembler
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.governance.capability_surface_engine import CapabilitySurfaceEngine
from odoo.addons.smart_core.governance.scene_drift_engine import SceneDriftEngine
from odoo.addons.smart_core.governance.scene_normalizer import SceneNormalizer
from odoo.addons.smart_core.runtime.auto_degrade_engine import AutoDegradeEngine


class SystemInitComponentsFactory:
    SOURCE_KIND = "system_init_runtime_components_factory"
    SOURCE_AUTHORITIES = ("scene_normalizer", "scene_drift_engine", "auto_degrade_engine", "capability_surface_engine", "contract_assembler")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="system_init_components_factory",
        )

    @staticmethod
    def create() -> dict:
        return {
            "scene_normalizer": SceneNormalizer(),
            "scene_drift_engine": SceneDriftEngine(),
            "auto_degrade_engine": AutoDegradeEngine(),
            "capability_surface_engine": CapabilitySurfaceEngine(),
            "contract_assembler": ContractAssembler(),
        }
