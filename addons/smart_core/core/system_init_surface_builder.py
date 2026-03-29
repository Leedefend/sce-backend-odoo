# -*- coding: utf-8 -*-
from __future__ import annotations


def _as_text(value) -> str:
    return str(value or "").strip()


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _pick_role_surface_provider(data: dict, scene_keys_latest: set) -> tuple[dict, dict]:
    nav_meta = data.get("nav_meta") if isinstance(data.get("nav_meta"), dict) else {}
    root_xmlid = _as_text(nav_meta.get("debug_root_xmlid") or nav_meta.get("root_xmlid"))

    providers_raw = data.get("role_surface_override_providers")
    providers = providers_raw if isinstance(providers_raw, dict) else {}

    candidates = []
    skipped_count = 0
    for provider_key, provider in providers.items():
        if not isinstance(provider_key, str) or not isinstance(provider, dict):
            skipped_count += 1
            continue
        enabled = bool(provider.get("enabled", True))
        if not enabled:
            continue
        overrides = provider.get("role_surface_overrides")
        if not isinstance(overrides, dict):
            skipped_count += 1
            continue
        priority = _as_int(provider.get("priority"), 0)
        domain_key = _as_text(provider.get("domain_key") or provider.get("domain") or provider_key)
        root_xmlids = provider.get("root_xmlids") if isinstance(provider.get("root_xmlids"), list) else []
        scene_codes = provider.get("scene_codes") if isinstance(provider.get("scene_codes"), list) else []
        root_match = True
        if root_xmlids:
            root_match = root_xmlid in {str(x).strip() for x in root_xmlids if str(x).strip()}
        scene_match = True
        if scene_codes:
            scene_match = bool({str(x).strip() for x in scene_codes if str(x).strip()} & set(scene_keys_latest or set()))
        match = root_match and scene_match
        candidates.append(
            {
                "provider_key": provider_key,
                "domain_key": domain_key,
                "priority": priority,
                "root_match": root_match,
                "scene_match": scene_match,
                "match": match,
                "overrides": overrides,
            }
        )

    selected = None
    matched = [item for item in candidates if item.get("match")]
    if matched:
        matched.sort(key=lambda item: (-int(item.get("priority") or 0), str(item.get("provider_key") or "")))
        selected = matched[0]
    elif candidates:
        candidates.sort(key=lambda item: (-int(item.get("priority") or 0), str(item.get("provider_key") or "")))
        selected = candidates[0]

    top_priority = None
    if matched:
        top_priority = int(matched[0].get("priority") or 0)
    top_matched = [item for item in matched if int(item.get("priority") or 0) == top_priority] if matched else []
    ambiguous_match = len(top_matched) > 1
    issues = []
    if ambiguous_match:
        issues.append("provider_ambiguous_same_priority")
    if not matched and candidates:
        issues.append("provider_no_match_priority_fallback")

    if selected:
        selected_key = str(selected.get("provider_key") or "")
        selected_priority = selected.get("priority")
        provider_sample = [
            {
                "provider_key": str(item.get("provider_key") or ""),
                "domain_key": str(item.get("domain_key") or ""),
                "priority": int(item.get("priority") or 0),
                "match": bool(item.get("match")),
            }
            for item in (matched[:5] if matched else sorted(candidates, key=lambda item: (-int(item.get("priority") or 0), str(item.get("provider_key") or "")))[:5])
        ]
        return selected.get("overrides") or {}, {
            "selected_provider": selected_key,
            "selected_priority": selected_priority,
            "match_mode": "matched" if selected.get("match") else "priority_fallback",
            "root_xmlid": root_xmlid,
            "provider_count": len(candidates),
            "provider_skipped_count": skipped_count,
            "ambiguous": ambiguous_match,
            "issues": issues,
            "matched_provider_count": len(matched),
            "matched_top_priority_count": len(top_matched),
            "matched_provider_keys": [str(item.get("provider_key") or "") for item in top_matched[:5]],
            "provider_sample": provider_sample,
        }

    legacy = data.get("role_surface_overrides")
    if isinstance(legacy, dict):
        return legacy, {
            "selected_provider": "legacy_inline",
            "selected_priority": None,
            "match_mode": "legacy",
            "root_xmlid": root_xmlid,
            "provider_count": 0,
            "provider_skipped_count": skipped_count,
            "ambiguous": False,
            "issues": [],
        }

    return {}, {
        "selected_provider": "none",
        "selected_priority": None,
        "match_mode": "none",
        "root_xmlid": root_xmlid,
        "provider_count": len(candidates),
        "provider_skipped_count": skipped_count,
        "ambiguous": False,
        "issues": [],
    }

class SystemInitSurfaceBuilder:
    @staticmethod
    def apply(*, surface_ctx) -> tuple[dict, dict]:
        data = surface_ctx.data
        contract_mode = surface_ctx.contract_mode
        scene_diagnostics = surface_ctx.scene_diagnostics
        capability_surface_engine = surface_ctx.capability_surface_engine
        identity_resolver = surface_ctx.identity_resolver
        user_groups_xmlids = surface_ctx.user_groups_xmlids
        nav_tree = surface_ctx.nav_tree
        scene_diagnostics_builder = surface_ctx.scene_diagnostics_builder
        build_capability_groups_fn = surface_ctx.build_capability_groups_fn
        apply_delivery_surface_governance_fn = surface_ctx.apply_delivery_surface_governance_fn

        pre_governance_scene_count = len(data.get("scenes") or []) if isinstance(data.get("scenes"), list) else 0
        pre_governance_capability_count = (
            len(data.get("capabilities") or []) if isinstance(data.get("capabilities"), list) else 0
        )
        data = apply_delivery_surface_governance_fn(data, contract_mode)
        data["capability_groups"] = build_capability_groups_fn(data.get("capabilities") or [])
        data["capability_surface_summary"] = capability_surface_engine.build_summary(
            data.get("capabilities") or [],
            data.get("capability_groups") or [],
        )
        post_governance_scene_count = len(data.get("scenes") or []) if isinstance(data.get("scenes"), list) else 0
        post_governance_capability_count = (
            len(data.get("capabilities") or []) if isinstance(data.get("capabilities"), list) else 0
        )
        scene_diagnostics["governance"] = scene_diagnostics_builder.governance(
            contract_mode=contract_mode,
            before_scene_count=pre_governance_scene_count,
            before_capability_count=pre_governance_capability_count,
            after_scene_count=post_governance_scene_count,
            after_capability_count=post_governance_capability_count,
        )
        scenes_payload = data.get("scenes") if isinstance(data.get("scenes"), list) else []
        scene_keys_latest = {
            (s.get("code") or s.get("key"))
            for s in scenes_payload
            if isinstance(s, dict) and (s.get("code") or s.get("key"))
        }
        role_surface_overrides, role_surface_provider_meta = _pick_role_surface_provider(data, scene_keys_latest)
        data["role_surface"] = identity_resolver.build_role_surface(
            user_groups_xmlids,
            nav_tree,
            scene_keys_latest,
            role_surface_overrides=role_surface_overrides,
        )
        data["role_surface_provider_meta"] = role_surface_provider_meta
        if isinstance(scene_diagnostics, dict):
            scene_diagnostics["role_surface_provider"] = role_surface_provider_meta
        data["role_surface_map"] = identity_resolver.build_role_surface_map_payload()
        return data, scene_diagnostics
