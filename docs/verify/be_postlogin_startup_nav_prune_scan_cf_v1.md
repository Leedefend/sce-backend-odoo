# BE Post-Login Startup Nav Prune Scan CF

## Goal

Inventory the exact bounded startup emitters behind the live `wutao/demo`
post-login failure: role-surface landing selection versus scene-nav collapse.

## Bounded Candidates

1. Role-surface landing emitter:
   - Live inspect returns:
     - `role_surface.role_code=executive`
     - `role_surface.landing_scene_key=portal.dashboard`
     - `default_route.scene_key=portal.dashboard`
   - Relevant bounded code surface:
     - [identity_resolver.py](/mnt/e/sc-backend-odoo/addons/smart_core/identity/identity_resolver.py:9)
     - [core_extension.py](/mnt/e/sc-backend-odoo/addons/smart_construction_scene/core_extension.py:8)
     - [system_init_surface_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/system_init_surface_builder.py:121)
   - Freeze:
     - startup landing currently resolves from role-surface identity, not from
       `project.management`

2. Scene-nav collapse emitter:
   - Live inspect returns `nav_menu_count=0` and `nav_release_count=0`
   - Relevant bounded code surface:
     - [scene_nav_contract_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/scene_nav_contract_builder.py:155)
     - [system_init_scene_runtime_surface_builder.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/system_init_scene_runtime_surface_builder.py:72)
     - [scene_nav_node_defaults.py](/mnt/e/sc-backend-odoo/addons/smart_core/core/scene_nav_node_defaults.py:11)
   - Freeze:
     - the startup scene-nav contract is being built from a candidate set that
       collapses to no delivery-ready leaf for this session

3. Scene-ready row incompleteness:
   - `scene_ready_contract_v1.scenes` does include a nested
     `scene.key=project.management` row
   - that row has no top-level `scene_key`, no `entry`, and no `target`
   - this keeps `project.management` visible as a semantic row but not yet
     strong enough to serve as startup/open navigation authority

## Scan Result

Strongest bounded candidate:
- `scene-nav collapse` is the strongest direct startup blocker because it alone
  explains the immediate `暂无导航数据 / 菜单树为空` state.

Secondary candidate:
- `role-surface landing -> portal.dashboard` remains a neighboring startup
  emitter, but it is secondary until the navigation contract stops collapsing
  to empty.

## Decision

The next implementation batch should stay on backend `scene_orchestration` and
prioritize repairing startup scene-nav candidate delivery for this session.
Role-surface landing should remain in scope only as a secondary adjustment if
the nav supply repair still leaves `portal.dashboard` as an unusable primary
landing.
