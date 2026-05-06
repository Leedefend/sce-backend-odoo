# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract


class SystemInitDiagnosticsHelper:
    SOURCE_KIND = "system_init_diagnostics_projection"
    SOURCE_AUTHORITIES = ("diagnostics_collector", "system_init_request", "odoo_env")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="system_init_diagnostics_helper",
        )

    @staticmethod
    def collect(diagnostics_collector, env, params: dict) -> tuple[bool, dict | None]:
        diag_enabled = diagnostics_collector.diagnostics_enabled(env)
        diagnostic_info = None
        if diag_enabled:
            diagnostic_info = diagnostics_collector.collect_system_init(env, params)
        return diag_enabled, diagnostic_info

    @staticmethod
    def log_debug(logger, env, params: dict, diagnostic_info: dict, self_params: dict | None = None) -> None:
        logger.info("[B1] system.init 诊断信息: %s", diagnostic_info)
        logger.info("[system_init][debug] params: %s", params)
        logger.info("[system_init][debug] self.params: %s", self_params or {})
        logger.info("[system_init][debug] self.env.cr.dbname: %s", env.cr.dbname)
