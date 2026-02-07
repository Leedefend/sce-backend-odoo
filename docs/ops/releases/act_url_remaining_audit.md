# act_url Remaining Audit (Pre-Release)

Date: 2026-02-07
Branch: `codex/pre_release_final_control`

## Summary
Core portal menus currently reference `ir.actions.act_url` in Odoo. These routes are valid but transitional.
Plan is to map these menus to scenes in SPA navigation (scene_key injection), so portal access is via scene -> route
and no critical SPA menu depends on act_url at runtime.

## Remaining act_url Entries (Phase 9.3 Classification)

1. 生命周期驾驶舱
- Menu XMLID: `smart_construction_portal.menu_sc_portal_lifecycle`
- Action XMLID: `smart_construction_portal.action_sc_portal_lifecycle`
- act_url: `/portal/lifecycle`
- Scene candidate: `portal.lifecycle`
- Status: scene mapping added (menu/action -> scene key)
- Class: A (direct scene mapping; keep act_url as legacy only)

2. 能力矩阵
- Menu XMLID: `smart_construction_portal.menu_sc_portal_capability_matrix`
- Action XMLID: `smart_construction_portal.action_sc_portal_capability_matrix`
- act_url: `/portal/capability-matrix`
- Scene candidate: `portal.capability_matrix`
- Status: scene mapping added (menu/action -> scene key)
- Class: A (direct scene mapping; keep act_url as legacy only)

3. 工作台
- Menu XMLID: `smart_construction_portal.menu_sc_portal_dashboard`
- Action XMLID: `smart_construction_portal.action_sc_portal_dashboard`
- act_url: `/portal/dashboard`
- Scene candidate: `portal.dashboard`
- Status: scene mapping added (menu/action -> scene key)
- Class: A (direct scene mapping; keep act_url as legacy only)

## Notes
- act_url remains in Odoo menu definitions for legacy compatibility.
- SPA menu navigation uses injected `scene_key` to resolve to scenes, which then route to portal via bridge.
- Phase 9.3 policy: no new act_url entries; act_url is legacy only.
