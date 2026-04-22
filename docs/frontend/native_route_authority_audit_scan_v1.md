# Native Route Authority Audit Scan v1

## Goal

Find remaining frontend candidate consumers that still treat native `/m`, `/a`,
or `/r` routes as ordinary product authority.

This scan does not classify severity or decide implementation.

## Scope

Bounded scan target:

- `frontend/apps/web/src/router/**`
- `frontend/apps/web/src/views/**`
- `frontend/apps/web/src/pages/**`
- `frontend/apps/web/src/layouts/**`
- `frontend/apps/web/src/app/**`

## Fixed Architecture Declaration

- Layer Target: Frontend governance scan
- Module: native route authority audit
- Module Ownership: frontend route consumers
- Kernel or Scenario: scenario
- Reason: produce candidate input for the next screen without reopening repo-wide
  governance search

## Scan Output

The following are raw candidate captures only. This scan does not classify
whether each point is a real boundary misalignment or an allowed compatibility
bridge.

### Router and Compatibility Entrypoints

- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:82)` still registers `/m/:menuId`
- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:88)` still registers `/a/:actionId`
- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:90)` still registers `/r/:model/:id`
- `[frontend/apps/web/src/router/index.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/router/index.ts:140)` still redirects some menu flows through `name: 'action'`
- `[frontend/apps/web/src/pages/ModelListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ModelListPage.vue:24)` still redirects legacy list entry to `name: 'action'`

### View-Level Navigation Candidates

- `[frontend/apps/web/src/views/MenuView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/MenuView.vue:149)` pushes leaf menu open to `name: 'action'`
- `[frontend/apps/web/src/views/MenuView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/MenuView.vue:181)` pushes unresolved scene redirect branch to `name: 'action'`
- `[frontend/apps/web/src/views/MenuView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/MenuView.vue:239)` pushes fallback redirect branch to `name: 'action'`
- `[frontend/apps/web/src/views/RecordView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/RecordView.vue:848)` still opens some button-driven navigation to `name: 'action'`
- `[frontend/apps/web/src/views/RecordView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/RecordView.vue:880)` still opens response-driven navigation to `name: 'action'`
- `[frontend/apps/web/src/views/RecordView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/RecordView.vue:927)` still opens effect target action to `name: 'action'`

### Shell and Layout Recognition Candidates

- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:340)` still treats `route.name === 'action' || 'record'` as compact topbar worksurface
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:343)` still treats `action/record` as compact worksurface shell
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:439)` still maps `route.name === 'record'` to page title fallback
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:465)` still marks `action/record` entry source as `capability`
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:780)` still appends breadcrumb labels for `action`
- `[frontend/apps/web/src/layouts/AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue:784)` still appends breadcrumb labels for `record`
