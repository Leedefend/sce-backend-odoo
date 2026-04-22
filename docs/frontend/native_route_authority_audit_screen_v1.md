# Native Route Authority Audit Screen v1

## Goal

Classify scanned frontend native-route candidates into:

- allowed compatibility bridges
- remaining scene-first boundary misalignments

This screen uses only the bounded scan output from
`native_route_authority_audit_scan_v1.md`.

## Fixed Architecture Declaration

- Layer Target: Frontend governance screen
- Module: native route authority audit
- Module Ownership: frontend route consumers
- Kernel or Scenario: scenario
- Reason: decide whether remaining native-route references are still acting as
  public authority or are now only compatibility/runtime shell bridges

## Classification Rule

- allowed compatibility bridge:
  native route remains registered or referenced only to absorb legacy entry,
  runtime fallback, or shell rendering compatibility after scene-first redirect
- remaining misalignment:
  frontend still uses native route as ordinary product navigation authority when
  scene-first contract output is already sufficient

## Screen Result

### Allowed Compatibility Bridges

- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:82)` `/m/:menuId` registration:
  retained as compatibility route because ordinary entry has already been
  intercepted in guard logic
- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:88)` `/a/:actionId` registration:
  retained as compatibility route because ordinary entry is now redirected to
  scene-first when resolvable
- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:90)` `/r/:model/:id` registration:
  retained as compatibility route because ordinary entry is now redirected to
  scene-first when record-entry semantics are available
- `[frontend/apps/web/src/pages/ModelListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ModelListPage.vue:24)` legacy list redirect:
  this is an explicit compatibility bridge from old list URL shape into current
  contract-driven navigation
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:340)` and `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:343)` compact shell recognition:
  these are shell rendering concerns for already-entered compatibility routes,
  not independent navigation authority
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:439)` `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:465)` `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:780)` `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:784)` title/source/breadcrumb handling:
  these are observational shell behaviors for compatibility routes, not entry
  authority themselves

### Remaining Boundary Misalignments

- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:140)` menu guard native fallback remains a temporary compatibility seam:
  this stays adjacent to the authority boundary because public menu outputs are
  not yet proven scene-complete in every path

### Rechecked Consumer Status

- `MenuView`:
  latest bounded recheck no longer supports the earlier conclusion that the
  previously flagged branches still navigate through direct native action-route
  authority. Current behavior is better described as scene-first resolution with
  explicit workbench diagnostics when scene identity cannot be proven.
- `RecordView`:
  latest bounded recheck no longer supports the earlier conclusion that the
  previously flagged user-action edges still open direct native action-route
  authority. Current behavior is better described as scene-first reopen logic
  plus workbench downgrade when scene identity is missing.
- governance status:
  the dominant residual after the recheck is evidence drift between the earlier
  audit wording and current runtime reality, not a newly confirmed consumer
  runtime misalignment in MenuView or RecordView.

## Frozen Follow-Up Direction

The next bounded batch should first realign governance evidence and only reopen
consumer runtime implementation if a later verify or tighter bounded scan proves
a still-active product-authority branch in MenuView or RecordView.
