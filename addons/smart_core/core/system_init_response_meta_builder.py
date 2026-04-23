# -*- coding: utf-8 -*-
from __future__ import annotations


class SystemInitResponseMetaBuilder:
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
        return scene_trace_meta, {**meta, "etag": top_etag}
