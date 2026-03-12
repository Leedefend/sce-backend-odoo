# Workbench Product Acceptance Checklist (v1)

## Goal

Validate that the workbench has moved from a "capability summary page" to an "action hub".

## A. Understandable in 10 seconds (above the fold)

- [ ] `today_focus` (Today Actions + System Alerts) is the first-priority area.
- [ ] Users can see "what to do first" (at least 3 actionable items) without scrolling.
- [ ] Action texts are business-oriented (approval/handling/follow-up), not technical fields.

## B. Executable in 30 seconds (action loop)

- [ ] Every today action has a valid navigation target (scene/route).
- [ ] Risk alerts provide at least one executable path (risk scene/handling page).
- [ ] Business actions are preferred; capability fallback appears only when business data is insufficient.

## C. Information structure convergence

- [ ] Main layout keeps only four zones: `hero` / `today_focus` / `analysis` / `quick_entries`.
- [ ] `hero` is demoted to supporting context and does not occupy action-first position.
- [ ] `analysis` shows business operational metrics, not platform capability counts.
- [ ] Platform capability counts are moved to `platform_metrics`/`diagnostics`.

## D. Protocol and compatibility

- [ ] `page_orchestration_v1` is the primary protocol.
- [ ] `page_orchestration` remains legacy-compatible and not primary.
- [ ] Contract includes `contract_protocol.primary=page_orchestration_v1`.

## E. Debug-field separation

- [ ] No debug terms like `result_summary/active_filters` in user main view.
- [ ] Debug/diagnostic info is contained in `diagnostics` or HUD channel.

## F. Regression chain

- [ ] `make verify.frontend.build`
- [ ] `make verify.frontend.typecheck.strict`
- [ ] `make verify.project.dashboard.contract`
- [ ] `make verify.phase_next.evidence.bundle`

