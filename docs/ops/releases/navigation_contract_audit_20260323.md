# Navigation Contract Audit 2026-03-23

## Audit Target

- Layer Target: `Scene Navigation Contract / Frontend Navigation Consumption`
- Module:
  - `addons/smart_core/handlers/system_init.py`
  - `addons/smart_core/core/scene_nav_contract_builder.py`
  - `addons/smart_core/identity/identity_resolver.py`
  - `addons/smart_construction_core/core_extension.py`
  - `frontend/apps/web/src/layouts/AppShell.vue`
- Reason: `确认发布级侧边导航为什么对 PM 演示角色只暴露单一入口，并锁定最小修复面`

## Current Runtime Chain

The current startup chain for navigation is:

```text
native nav tree
-> role_surface build
-> role_surface nav prune
-> delivery scene filter / preload subset
-> scene_nav_contract build
-> frontend AppShell consume data.nav
```

The key implementation points are:
- `system_init.py`
  - first prunes native nav through `identity_resolver.filter_nav_for_role_surface(...)`
  - then replaces `data["nav"]` with `scene_nav_contract["nav"]`
- `scene_nav_contract_builder.py`
  - uses role scene candidates as the primary visible group
  - hides remaining grouped scenes by default when candidate scenes exist
- `AppShell.vue`
  - renders sidebar from `session.menuTree`
  - `session.menuTree` is effectively driven by the scene-first nav after startup

## Confirmed Findings

### 1. Sidebar is no longer driven by the original root menu surface

Even though role surface still carries allowed root menus such as:
- `smart_construction_core.menu_sc_project_center`
- `smart_construction_core.menu_sc_contract_center`
- `smart_construction_core.menu_sc_cost_center`

the final sidebar is not rendered from that native root tree.

`system_init.py` replaces `data["nav"]` with `scene_nav_contract["nav"]`.

So frontend sidebar exposure is now controlled mainly by the scene nav contract, not by the original Odoo root menu hierarchy.

### 2. PM role surface is broad, but scene-nav exposure is narrow

For `pm`, `ROLE_SURFACE_OVERRIDES` in `smart_construction_core/core_extension.py` defines:
- multiple root menu XMLIDs
- multiple landing scene candidates

However, `build_scene_nav_contract()` only guarantees the visibility of role candidate leaves under:
- `我的场景`

When candidate leaves exist, the builder sets:

```text
remaining_hidden = true
```

unless `include_remaining_nav_scenes` is explicitly enabled.

That means the sidebar can legitimately shrink to:
- only `我的场景`
- only the candidate scenes that survive delivery filtering

### 3. Current PM release surface can collapse to a single visible entry

`ROLE_SURFACE_OVERRIDES["pm"]["landing_scene_candidates"]` currently includes:
- `portal.dashboard`
- `projects.ledger`
- `projects.list`
- `project.initiation`
- `projects.intake`

But the final visible candidate set depends on delivery-ready scenes and preload subset.

With the current release-ready slice surface, the effective visible result can collapse to:
- `projects.intake`

This matches the observed sidebar behavior:
- a single entry under `我的场景`

### 4. Frontend is faithfully consuming a thin contract

`AppShell.vue` is not the primary source of the problem.

It renders:
- tree nodes from `filteredMenu`
- role shortcut buttons from `roleSurface.menu_xmlids`

The tree itself comes from the final contract nav.

So the main release issue is contract shaping and release entry strategy, not sidebar rendering failure.

### 5. Role shortcut buttons are not a sufficient release navigation surface

`AppShell.vue` also renders `roleMenus`, which are derived from `roleSurface.menu_xmlids`.

But these are:
- small shortcut buttons above the tree
- not the main information architecture of the released sidebar

They cannot replace a properly structured release navigation tree.

## Mismatch Summary

### Intended Release Expectation

For the PM demo role, the release surface should make it obvious that the product currently supports:
- project initiation
- project lifecycle entry
- my work

and should not force discovery through hidden deep links or context-implicit jumps.

### Actual Runtime Behavior

- role surface advertises broad domain access
- native nav is pruned by allowed root menus
- scene nav contract then replaces native nav
- scene nav contract keeps role candidate scenes as primary
- remaining groups are hidden
- resulting sidebar can collapse to a single release entry

## Conclusion

The thin sidebar is an outcome of the current release navigation contract policy.

The minimal implementation direction should therefore be:
- keep contract ownership in backend
- define explicit release navigation exposure rules
- only then align frontend consumption and add browser smoke

It should not be fixed by ad hoc frontend menu stuffing.
