# Phase 2.1 Role Entry Layer

## Scope
- Sidebar adds a top-level virtual group: 我的工作
- Entries are configuration-driven (front-end only)
- Feature flag can disable the entire group

## Feature Flag
- URL or localStorage: `sc_role_entries=0` to hide the group
- Default: enabled

## Config
File: `addons/smart_construction_core/static/src/config/role_entry_map.js`

Minimal structure per entry:
- `key`
- `label`
- `icon`
- `default_action.menu_xmlid`
- `default_action.action_xmlid`

Fail-safe rules:
- If menu/action cannot be resolved, the entry is hidden
- Empty config -> group not rendered

## Verification
1) Default on: group visible with 4 entries
2) `sc_role_entries=0`: group hidden
3) Remove all config entries: group hidden
4) Clicking each entry navigates to the expected list
5) Active state highlights when action/menu matches
