# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract


class SystemInitResponseMetaBuilder:
    SOURCE_KIND = "system_init_response_meta_projection"
    SOURCE_AUTHORITIES = ("system_init_payload", "scene_diagnostics", "contract_assembler")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            response_envelope_only=True,
        )

    @staticmethod
    def build(
        *,
        contract_assembler,
        data: dict,
        scene_diagnostics: dict,
        elapsed_ms: int,
        nav_versions: str,
        parts_version: dict,
        etags: dict,
        intent_type: str,
        contract_version: str,
        api_version: str,
        contract_mode: str,
        nav_fp: str,
        startup_profile: dict | None = None,
        **_compat_kwargs,
    ) -> tuple[dict, dict]:
        scene_trace_meta = contract_assembler.build_scene_trace_meta(data, scene_diagnostics, elapsed_ms)
        meta = contract_assembler.build_meta(
            elapsed_ms=elapsed_ms,
            nav_versions=nav_versions,
            parts_version=parts_version,
            etags=etags,
            intent_type=intent_type,
            contract_version=contract_version,
            api_version=api_version,
            contract_mode=contract_mode,
            scene_trace_meta=scene_trace_meta,
        )
        top_etag = contract_assembler.build_top_etag(
            data,
            nav_fp=nav_fp,
            contract_mode=contract_mode,
            contract_version=contract_version,
            api_version=api_version,
        )
        if isinstance(startup_profile, dict) and startup_profile:
            meta["startup_profile"] = startup_profile
        return scene_trace_meta, {**meta, "etag": top_etag}
