# Platform Release and Industry Capability Relationship v1

## Purpose

This note freezes the relationship between platform product release governance and industry module capability delivery. It keeps release governance in `smart_core` while allowing construction modules to provide the business facts that make a product edition useful.

## Core Position

Platform release is the carrier. Industry capability is the content.

`smart_core` owns product identity, edition policy, release state, source authority, navigation projection, scene snapshot binding, and release gates. Industry modules own business models, menu/action facts, scene profile/policy/provider assets, and domain-specific capability semantics.

The platform must not import construction modules to implement business behavior. It may project industry-provided runtime facts through platform-owned adapters and contracts.

## Relationship Model

| Layer | Owner | Artifact | Responsibility |
|---|---|---|---|
| Product identity | `smart_core` | `construction.standard`, `construction.preview`, `platform.standard`, `platform.preview` | Names the releaseable edition and resolves base/edition keys. |
| Product release policy | `smart_core` | `sc.product.policy` runtime payload | Freezes release state, access level, menu groups, scenes, capabilities, and scene bindings. |
| Industry capability facts | `smart_construction_*` / Odoo native records | `ir.ui.menu`, `ir.actions`, scene profile/policy/provider, domain models | Supplies user-visible business entries and capability semantics. |
| Projection adapter | `smart_core` | `ProductPolicyCatalogSyncService` | Converts authorized industry menu/action facts into a platform product policy payload. |
| Runtime delivery | `smart_core` | `DeliveryEngine`, `MenuService`, `SceneService`, `CapabilityService` | Builds `delivery_engine_v1` nav/scenes/capabilities from the selected policy and runtime authorization facts. |

## Current Runtime Rule

For `construction.*` editions, product policy resolution follows this order:

1. Use active `sc.product.policy` if it already has a non-empty release surface.
2. Use platform release DB policy if configured and non-empty.
3. If the construction policy exists but has no release surface, rebuild from construction menu/action catalog facts.
4. If no stored policy exists, use the construction catalog projection when available.
5. Only fall back to a minimal empty policy when no authorized catalog facts are available.

The catalog projection is still platform-governed: it carries source authority, has no business-fact authority, and only describes user-visible entry/control facts.

## Authorization Rule

Published policy menus are not displayed merely because they exist in `sc.product.policy`.

`MenuService` must intersect product-policy menus with the current user's native authorized menu facts (`menu_id`, `menu_xmlid`, `scene_key`, or route). Platform admins may see the full policy surface. This prevents product release policy from bypassing Odoo/native authorization.

## Boundary Rules

- `smart_core` may define product release schema, policy projection, source authority, and release gates.
- `smart_core` may read generic Odoo menu/action facts as platform input.
- `smart_core` must not encode construction business rules, settlement semantics, BOQ semantics, or role-specific construction workflows.
- Industry modules may contribute scene profiles, policies, providers, menus, actions, and domain models.
- Industry modules must not define a private frontend schema or bypass `delivery_engine_v1` / scene-ready contracts.
- Release policy is not historical business truth. It is a rebuildable delivery projection.

## Practical Interpretation

When a construction business page should be included in a platformized release:

1. The industry module exposes the real model/action/menu/scene/profile facts.
2. Platform projection turns those facts into product policy nodes.
3. Release governance freezes or promotes the edition state.
4. Runtime delivery filters the policy by the current user's authorized native menu surface.
5. Frontend consumes the platform delivery contract, not a construction-private schema.

This keeps platform release governance reusable across industries while preserving construction-specific capability ownership in construction modules.
