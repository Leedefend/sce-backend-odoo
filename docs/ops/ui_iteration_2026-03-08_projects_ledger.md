# UI Iteration Baseline - projects.ledger (2026-03-08)

## Baseline Inputs
- Screenshot A: `tmp/png/014.png` (kanban/list shell)
- Screenshot B: `tmp/png/015.png` (record/form shell)

## Observed Gaps
- Kanban had weak hierarchy: important project status signals were mixed with generic metadata.
- Form had high density and poor readability due to flattened field rendering and wide multi-column squeeze.
- Top action/filter chips were too dense for default project ledger surface.

## Implemented Contract Changes
- Added `views.kanban.kanban_profile` for `project.project` user-mode contracts:
  - `title_field`
  - `primary_fields`
  - `secondary_fields`
  - `status_fields`
- Ensured `views.kanban.fields` keeps user-facing fields and excludes technical noise.
- Preserved recursive form layout semantics during governance filtering.
- Added `form_profile` contract block for form rendering fallback.
- Reduced default surface density for project ledger:
  - `filters_primary_max <= 4`
  - `actions_primary_max <= 3`

## Implemented Frontend Changes
- `ActionView` now reads and passes kanban profile metadata.
- `KanbanPage` renders cards as:
  - Title
  - Status chips (status fields)
  - Primary meta block
  - Secondary meta block
- `ContractFormPage` now traverses nested layout nodes recursively and avoids full field-map flatten fallback.
- Form grid readability constraints improved for desktop/tablet/mobile breakpoints.

## Validation
- `make verify.frontend_api` passed after service restart.
- Governance unit assertions were extended for `form_profile` and `kanban_profile` contract expectations.

## Next Acceptance Check
- Re-capture screenshots for the same routes and compare with `014/015`:
  - Card readability: title + status + <=5 meta points visible without cognitive overload.
  - Form readability: key fields visible in first screen; no all-field flatten rendering.
