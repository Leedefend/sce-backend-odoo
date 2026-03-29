# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.capability_provider import (
    build_capability_groups as provider_build_capability_groups,
    load_capabilities_for_user as provider_load_capabilities_for_user,
)
from odoo.addons.smart_core.core.extension_loader import run_extension_hooks
from odoo.addons.smart_core.core.runtime_fetch_bootstrap_helper import build_runtime_fetch_bootstrap_surface
from odoo.addons.smart_core.core.system_init_components_factory import SystemInitComponentsFactory
from odoo.addons.smart_core.core.system_init_identity_payload import SystemInitIdentityPayload
from odoo.addons.smart_core.core.system_init_nav_request_builder import SystemInitNavRequestBuilder
from odoo.addons.smart_core.core.system_init_payload_builder import SystemInitPayloadBuilder
from odoo.addons.smart_core.core.system_init_surface_builder import SystemInitSurfaceBuilder
from odoo.addons.smart_core.core.system_init_surface_context import SystemInitSurfaceContext
from odoo.addons.smart_core.core.system_init_extension_fact_merger import merge_extension_facts
from odoo.addons.smart_core.core.scene_diagnostics_builder import SceneDiagnosticsBuilder
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver
from odoo.addons.smart_core.utils.contract_governance import (
    apply_contract_governance,
    normalize_capabilities,
    resolve_contract_mode,
)


def build_runtime_fetch_context(env, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params if isinstance(params, dict) else {}
    contract_mode = resolve_contract_mode(params)
    delivery_surface_governance_fn = apply_contract_governance
    user = env.user
    identity_resolver = IdentityResolver(env)
    user_groups_xmlids = identity_resolver.user_group_xmlids(user)
    components = SystemInitComponentsFactory.create()
    nav_request = SystemInitNavRequestBuilder.build(params, params.get("scene") or "web")
    nav_meta = {
        "debug_params_keys": sorted(list(params.keys())),
        "debug_root_xmlid": nav_request.get("root_xmlid"),
        "root_xmlid": nav_request.get("root_xmlid"),
    }
    data = SystemInitPayloadBuilder.build_base(
        user_dict=SystemInitIdentityPayload.build(user, user_groups_xmlids),
        nav_tree=[],
        nav_meta=nav_meta,
        default_route={"menu_id": None},
        intents=[],
        feature_flags={"ai_enabled": True},
        capabilities=normalize_capabilities(provider_load_capabilities_for_user(env, user)),
        scene_channel="runtime",
        channel_selector="runtime_fetch",
        channel_source_ref="runtime_fetch",
        contract_mode=contract_mode,
        contract_version="1.0.0",
    )
    data.update({"contract_mode": contract_mode})
    return build_runtime_fetch_bootstrap_surface(
        data=data,
        env=env,
        user=user,
        contract_mode=contract_mode,
        components=components,
        identity_resolver=identity_resolver,
        user_groups_xmlids=user_groups_xmlids,
        build_capability_groups_fn=provider_build_capability_groups,
        apply_contract_governance_fn=delivery_surface_governance_fn,
        scene_diagnostics_builder=SceneDiagnosticsBuilder,
        run_extension_hooks_fn=run_extension_hooks,
        merge_extension_facts_fn=merge_extension_facts,
        surface_context_cls=SystemInitSurfaceContext,
        surface_builder=SystemInitSurfaceBuilder,
    )
