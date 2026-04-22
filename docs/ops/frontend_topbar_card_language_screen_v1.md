# Frontend Topbar Card Language Screen v1

## Scope

This screen freezes the next bounded convergence batch after
`frontend_product_shell_interference_verify_v1.md`.

Target shared carriers only:

- `frontend/apps/web/src/layouts/AppShell.vue`
- `frontend/apps/web/src/components/template/LayoutShell.vue`

## Decision

The previous batches already reduced:

- inner list/form shell density
- shared sidebar interference

The main remaining visible gaps are now:

1. the top background / empty atmosphere above the work area
2. the final soft outer card-language around the work area

Therefore the next batch should stay on shared shell carriers and reduce only
those two traits.

## Layer Declaration

- Layer Target: `Frontend page-shell screen`
- Module: `top atmosphere and outer card language`
- Kernel or Scenario: `scenario`
- Reason: continue shrinking the remaining non-native shell feeling without
  reopening inner page-body structure or backend semantics.

## What Must Be Reduced

### AppShell

1. Top atmosphere
   - reduce empty top field on action / record routes
   - thin the remaining decorative headline space
   - keep navigation readability but remove editorial breathing room

2. Outer work-area framing
   - reduce remaining soft panel feeling around router host
   - avoid warm ambient space dominating above the table/form

### Template LayoutShell

1. Form outer card language
   - shrink final outer padding rhythm
   - help the form body feel flatter and more directly embedded in the work area

## Not In Scope

1. sidebar structure redesign
2. inner table/form body redesign
3. backend contract or route changes
4. task-detail bootstrap residual risk

## Acceptance For Next Batch

The next implementation batch should be accepted only if:

1. project list loses another visible slice of top empty atmosphere
2. project detail loses another visible slice of outer soft card framing
3. the shared shell remains stable and task-detail residual risk stays isolated

## Result

- screen status: `PASS`
- next task type: `implementation`
- next task suggestion:
  - `ITER-2026-04-19-FE-TOPBAR-CARD-LANGUAGE-IMPLEMENT`
