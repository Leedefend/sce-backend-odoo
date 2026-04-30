# act_url Remaining Audit (Resolved)

Date: 2026-02-07
Branch: `codex/pre_release_final_control`

## Summary
Core portal menus no longer reference `ir.actions.act_url` in Odoo. The legacy portal native menu entries are removed from module install data and existing databases are cleaned by `smart_construction_portal` migration `17.0.1.1`.

Portal access is now scene/route based, so a rebuilt database must not recreate these development-era native menus.

## Removed act_url Entries

1. 生命周期驾驶舱
- Menu XMLID: `smart_construction_portal.menu_sc_portal_lifecycle`
- Action XMLID: `smart_construction_portal.action_sc_portal_lifecycle`
- act_url: `/portal/lifecycle`
- Scene candidate: `portal.lifecycle`
- Status: removed from install data and upgrade migration
- Replacement: `scene_key=portal.lifecycle`

2. 能力矩阵
- Menu XMLID: `smart_construction_portal.menu_sc_portal_capability_matrix`
- Action XMLID: `smart_construction_portal.action_sc_portal_capability_matrix`
- act_url: `/portal/capability-matrix`
- Scene candidate: `portal.capability_matrix`
- Status: removed from install data and upgrade migration
- Replacement: `scene_key=portal.capability_matrix`, `route=/s/portal.capability_matrix`

3. 工作台
- Menu XMLID: `smart_construction_portal.menu_sc_portal_dashboard`
- Action XMLID: `smart_construction_portal.action_sc_portal_dashboard`
- act_url: `/portal/dashboard`
- Scene candidate: `portal.dashboard`
- Status: removed from install data and upgrade migration
- Replacement: `scene_key=portal.dashboard`

## Notes
- New database rebuilds must not create these XMLIDs.
- Existing databases must report zero rows for the listed `smart_construction_portal` menu/action XMLIDs after module upgrade.
- Phase policy: no new portal native menu backed by `ir.actions.act_url`; expose portal capability through scene contract only.
