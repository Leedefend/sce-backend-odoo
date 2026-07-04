# Workbench Product Acceptance Checklist (v1)

## Goal

Validate that the workbench has moved from a "capability summary page" to an "action hub".

## A. Understandable in 10 seconds (above the fold)

- [x] `today_focus` (Today Actions + System Alerts) is the first-priority area.
- [x] Users can see "what to do first" (at least 3 actionable items) without scrolling.
- [x] Action texts are business-oriented (approval/handling/follow-up), not technical fields.

## B. Executable in 30 seconds (action loop)

- [x] Every today action has a valid navigation target (scene/route).
- [x] Risk alerts provide at least one executable path (risk scene/handling page).
- [x] Business actions are preferred; capability fallback appears only when business data is insufficient.

## C. Information structure convergence

- [x] Main layout keeps only four zones: `hero` / `today_focus` / `analysis` / `quick_entries`.
- [x] `hero` is demoted to supporting context and does not occupy action-first position.
- [x] `analysis` shows business operational metrics, not platform capability counts.
- [x] Platform capability counts are moved to `platform_metrics`/`diagnostics`.

## D. Protocol and compatibility

- [x] `page_orchestration_v1` is the primary protocol.
- [x] `page_orchestration` remains legacy-compatible and not primary.
- [x] Contract includes `contract_protocol.primary=page_orchestration_v1`.

## E. Debug-field separation

- [x] No debug terms like `result_summary/active_filters` in user main view.
- [x] Debug/diagnostic info is contained in `diagnostics` or HUD channel.

## F. Regression chain

- [x] `make verify.frontend.build`
- [x] `make verify.frontend.typecheck.strict`
- [x] `make verify.project.dashboard.contract`
- [x] `make verify.phase_next.evidence.bundle`
