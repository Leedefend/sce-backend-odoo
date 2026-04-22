# Frontend Product Shell Interference Screen v1

## Scope

This screen freezes the next bounded convergence batch after
`frontend_native_skeleton_convergence_verify_v1.md`.

Target shared carriers only:

- `frontend/apps/web/src/layouts/AppShell.vue`
- `frontend/apps/web/src/components/template/LayoutShell.vue`

Out of scope:

- `task-detail` bootstrap / loading residuals
- backend semantic or contract changes
- inner table/form block redesign

## Decision

The previous verify batch established:

- inner list/form carriers have already improved
- remaining native-perception gap is now dominated by shared product shell

Therefore the next batch should not continue polishing `ListPage` and
`ContractFormPage` internals first.

It should instead reduce shared product-shell interference for action/record
work surfaces.

## Layer Declaration

- Layer Target: `Frontend page-shell screen`
- Module: `shared product shell interference`
- Kernel or Scenario: `scenario`
- Reason: shrink the visual weight of sidebar/topbar/outer whitespace around
  list and form work areas without reopening backend or task-detail runtime.

## What Must Be Reduced

### AppShell

1. Sidebar presence on work surfaces
   - thinner visual mass
   - flatter container language
   - less prominent brand/search/nav chrome

2. Top page atmosphere
   - reduce remaining large padding and decorative shell feeling around
     action/record routes
   - keep navigation readability without reintroducing dashboard mood

3. Content outer spacing
   - list/form work surface should start earlier in the viewport
   - avoid product-shell whitespace dominating before content

### Template LayoutShell

1. Form outer padding
   - reduce top and lateral breathing room around form work surfaces
   - support action-and-fields-first reading order

2. Flow spacing
   - keep structure readable
   - avoid wide editorial spacing on ordinary record work

## What May Remain Custom

1. Brand identity and left rail may remain.
2. Token system may remain custom.
3. Navigation tree may remain grouped and scrollable.

These may stay only if they no longer dominate list/form first impression.

## Acceptance For Next Batch

The next implementation batch should be accepted only if:

1. project list reads more like a work area placed inside a product shell, not
   a product shell surrounding a card dashboard
2. project form enters title/action/field work earlier within the first screen
3. sidebar and outer whitespace feel visibly lighter on action/record routes
4. task-detail residual risk stays isolated and is not claimed as solved here

## Result

- screen status: `PASS`
- next task type: `implementation`
- next task suggestion:
  - `ITER-2026-04-19-FE-PRODUCT-SHELL-INTERFERENCE-IMPLEMENT`
