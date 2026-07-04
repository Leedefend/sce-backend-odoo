# v1.0 Iteration Round 1 Product Expression Checklist

## 1. Page Mode Clarity

- [x] `dashboard/workspace/list` are visually and structurally distinguishable
- [x] `project.management` clearly behaves as a dashboard
- [x] `projects.ledger` behaves as workspace-style ledger
- [x] `projects.list` / `task.center` / `risk.center` / `cost.project_boq` behave as list pages

## 2. First-Glance Readability

- [x] `project.management` shows KPI/risk/progress immediately
- [x] `projects.ledger` shows portfolio overview before cards
- [x] `projects.list` prioritizes name/status/owner/amount/update time

## 3. Risk Visibility

- [x] Dashboard risk block has higher visual priority
- [x] List/card abnormal records show light risk signals

## 4. List Productization

- [x] List pages no longer feel like raw DB browsers
- [x] Top info layer includes title/count/search/filter/sort
- [x] Batch action bar placement is consistent

## 5. Technical Value Exposure

- [x] No direct `draft`/`done`/`01_in_progress`/`No` on core pages
- [x] Amounts are shown with `万/亿`
- [x] Percentages are consistently `%`

## 6. Demo Readiness

- [x] Core six pages have readable demo data
- [x] Dashboard + risk/task/BOQ pages support storyline demo

## 7. Verify Chain Safety

- [x] `verify.project.dashboard.contract` remains intact
- [x] Frontend build/typecheck remains intact
- [x] Phase evidence bundle remains intact

## 8. Screenshot List Suggestion

1. `project.management` first-screen + risk close-up
2. `projects.ledger` overview strip + cards in one frame
3. `projects.list` key-column ordered list
4. `task.center` top layer + status column
5. `risk.center` status tones + risk signal
6. `cost.project_boq` amount readability

## 9. Closeout Result

- Status: `PASS`
- Date: `2026-07-05`
- Owner: `Codex`
- Evidence chain: `docs/product/workbench_product_acceptance_checklist_v1.en.md`, Phase 2 core scenario checklist, Phase 4 frontend stability report, Phase 5 verification/deployment report, UAT closeout checklist, Phase 6 post-launch review.
- Fixed guard: `make verify.release.round1.final_closeout.guard`
- Regression chain: `make verify.frontend.build`, `make verify.frontend.typecheck.strict`, `make verify.project.dashboard.contract`, `make verify.phase_next.evidence.bundle`
