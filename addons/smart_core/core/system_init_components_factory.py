# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.contract_assembler import ContractAssembler
from odoo.addons.smart_core.governance.capability_surface_engine import CapabilitySurfaceEngine
from odoo.addons.smart_core.governance.scene_drift_engine import SceneDriftEngine
from odoo.addons.smart_core.governance.scene_normalizer import SceneNormalizer
from odoo.addons.smart_core.runtime.auto_degrade_engine import AutoDegradeEngine


class SystemInitComponentsFactory:
    @staticmethod
    def create() -> dict:
        return {
            "scene_normalizer": SceneNormalizer(),
            "scene_drift_engine": SceneDriftEngine(),
            "auto_degrade_engine": AutoDegradeEngine(),
            "capability_surface_engine": CapabilitySurfaceEngine(),
            "contract_assembler": ContractAssembler(),
        }
