# Portal Pages -> SPA Migration (Planning Stub)

Status: Planning (no implementation in this phase)

## Goal
Retire Odoo server-rendered portal pages by moving core portal surfaces into SPA routes.

## Target Pages
- `/portal/lifecycle` -> `/s/portal.lifecycle` (SPA scene)
- `/portal/capability-matrix` -> `/s/portal.capability_matrix`
- `/portal/dashboard` -> `/s/portal.dashboard`

## Candidates to Remain Server-Rendered
- None identified yet (to be validated)

## Required Work (Future)
- Define SPA views for portal pages.
- Replace `act_url` usage with scene routes.
- Remove portal bridge dependency.

## Mapping Plan
- Odoo menu -> scene_key -> SPA route
- Scene target -> SPA route (no Odoo portal jump)

## Risks
- Requires porting portal JS logic into SPA components.
- Requires test coverage for new SPA views.
