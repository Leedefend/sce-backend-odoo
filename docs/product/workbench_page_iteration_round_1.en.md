# Workbench Page Iteration Plan (Round 1)

## Goal

- Evolve the landing workbench from mixed capability/debug exposure into a productized structure:
  action entry + system reminders + overall status + common functions.
- Keep Scene/Capability/Suggested Action mechanisms unchanged; optimize expression and information hierarchy only.

## Page Role

The workbench is a decision surface, not a static dashboard.

It must answer:

1. What to do today
2. What the system is warning about
3. What the overall status looks like

## Information Architecture (Round 1)

User mental order:

1. Today Actions
2. System Reminders
3. Overall Project Status
4. Common Functions

## Scope

- Adjust workbench block labels and ordering semantics.
- Rename “System Suggestions” to “System Reminders”.
- Rename “Business Analysis” to “Overall Project Status”.
- Rename “Capability Entry” to “Common Functions”.
- Remove debug-style `filters/result_summary/active_filters` accordion from user-facing surface.

## Out of Scope

- No scene registry/governance/delivery policy changes.
- No ACL/auth baseline changes.
- No contract envelope refactor.
- No Suggested Action protocol changes.

## Acceptance Criteria

- First screen emphasizes “Today Actions + System Reminders”.
- No technical summary fields appear in user-facing view.
- Overall status labels are business-readable.
- Common function entries remain available without dominating first-screen focus.

## Round 1 · Batch 2 (Implemented)

- Role focus blocks are front-loaded to: `today_actions`, `risk_alert_panel`, `metric_row_core`.
- Section order is aligned to “Today Actions -> System Reminders -> Core Metrics”.
- `ops` texts are business-oriented:
  - `Project Business Overview` -> `Overall Project Status`
  - `Cost Execution Rate` -> `Cost Control Rate`
  - `Payment Ratio` -> `Fund Payment Rate`
- Core metric labels are businessized (contract performance, output completion, cost control, fund payment), and technical navigation-count style metrics are removed.

## Round 1 · Batch 3 (Polish)

- Reduced first-screen cognitive load by shortening `hero.lead` and simplifying `product_tags`.
- Replaced technical `ds_hero` key dumps with labeled display rows (role, landing entry, update time, runtime status).
- Unified card rhythm and spacing:
  - larger zone/block spacing for breathing room
  - minimum heights for todo/alert/entry/metric/progress cards to reduce visual misalignment.

## Round 1 · Batch 4 (Model Alignment)

- Further aligned the page to Action -> Alert -> Status -> Capability:
  - increased `today_focus` zone priority and lowered `hero` zone priority;
  - moved system reminders into `today_focus` (risk reminders + supplemental advice).
- Removed technical-feeling fields from user-facing surface:
  - no direct `updated_at/status_notice/status_detail` style display;
  - `ds_hero` converted into simplified human-readable summary rows.
