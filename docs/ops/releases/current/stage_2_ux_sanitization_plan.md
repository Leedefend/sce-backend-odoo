# Stage 2 UX Sanitization Plan

## Scope
- Frontend and documentation only.
- No backend behavior changes.
- Keep existing suggested-action and contract consumption unchanged.

## Goals
- Remove technical/internal text from user-facing pages.
- Keep technical diagnostics available in HUD/dev surfaces.
- Normalize cell rendering so boolean/null/false values are user-friendly.

## Commit Plan
1. `docs(stage2): define ux sanitization scope and commit plan`
2. `feat(frontend): add user-facing value formatter utility`
3. `refactor(frontend): use value formatter in list page cells`
4. `refactor(frontend): use value formatter in field value component`
5. `refactor(frontend): use value formatter in kanban cards`
6. `fix(frontend): hide technical error metadata outside hud mode`
7. `fix(frontend): remove internal shell chrome copy from user mode`
8. `fix(frontend): keep workbench diagnostics behind hud only`
9. `fix(frontend): sanitize capability home copy for user delivery`
10. `docs(stage2): record ux sanitization verification results`

## Verification Results
- `make verify.frontend.typecheck.strict`: PASS
  - command: `vue-tsc --noEmit -p tsconfig.strict.json`
- `make verify.frontend.build`: PASS
  - output bundle:
    - `dist/assets/index-CbSCV1LC.css` 33.71 kB (gzip 6.25 kB)
    - `dist/assets/index-DPS4-eVo.js` 302.46 kB (gzip 98.81 kB)
- `make verify.frontend.suggested_action.all`: PASS
  - guards:
    - contract/parser/runtime/import-boundary/usage/trace-export/top-k/since-filter/hud-export
    - cross-stack smoke
    - no-new-any guard (`total_any: 0`)
