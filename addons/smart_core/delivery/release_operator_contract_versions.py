# -*- coding: utf-8 -*-

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

RELEASE_OPERATOR_SURFACE_CONTRACT_VERSION = "release_operator_surface_v1"
RELEASE_OPERATOR_READ_MODEL_CONTRACT_VERSION = "release_operator_read_model_v1"
RELEASE_OPERATOR_WRITE_MODEL_CONTRACT_VERSION = "release_operator_write_model_v1"
RELEASE_OPERATOR_CONTRACT_REGISTRY_VERSION = "release_operator_contract_registry_v1"

SOURCE_KIND = "release_operator_contract_version_registry"
SOURCE_AUTHORITIES = ("static_release_operator_contract_versions",)
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        contract_metadata_only=True,
    )
