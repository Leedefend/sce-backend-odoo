# -*- coding: utf-8 -*-

RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION = "release_operator_surface_v1"
RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION = "release_operator_read_model_v1"
RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION = "release_operator_write_model_v1"
RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION = "release_operator_contract_registry_v1"

SOURCE_KIND = "release_operator_contract_version_registry"
SOURCE_AUTHORITIES = ("static_release_operator_contract_versions",)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "rebuildable": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "contract_metadata_only": True,
    }
