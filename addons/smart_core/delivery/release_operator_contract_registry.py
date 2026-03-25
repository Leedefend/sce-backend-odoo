# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy

from .release_operator_contract_versions import (
    RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION,
    RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
    RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION,
    RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
)


def build_release_operator_contract_registry() -> dict:
    contracts = {
        "surface": {
            "contract_key": "release_operator_surface",
            "contract_version": RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION,
            "state": "frozen",
            "change_rule": "version_bump_required",
        },
        "read_model": {
            "contract_key": "release_operator_read_model",
            "contract_version": RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION,
            "state": "frozen",
            "change_rule": "version_bump_required",
        },
        "write_model": {
            "contract_key": "release_operator_write_model",
            "contract_version": RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION,
            "state": "frozen",
            "change_rule": "version_bump_required",
        },
    }
    return {
        "contract_version": RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION,
        "contracts": deepcopy(contracts),
    }
