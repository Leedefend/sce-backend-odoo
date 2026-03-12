# Workbench Purpose and Model (v1)

## 1. Page Mission

The workbench is not a navigation page and not a debug dashboard. Its single mission is:

- Tell users what to do first within 10 seconds.
- Make risks and weekly impact visible within 30 seconds.
- Provide direct entry to execution scenes with one click.

One-line definition: **Workbench = Action Entry + Risk Alerts + Status Overview**.

## 2. Information Priority (above the fold)

### P0 (must be above the fold)

- Today Actions: pending approvals/confirmations/follow-ups with direct scene entry.
- System Alerts: only high-priority risks, no generic advisory noise.

### P1 (visible on first screen, lower weight than P0)

- Portfolio Status: four key operational metrics and progress summary for quick judgment.

### P2 (deprioritized)

- Quick Entries: "next step" navigation, not primary focus.
- Core Focus (role summary): supporting information area, not primary.
- Debug fields: visible only in HUD/dev mode.

## 3. Action Prioritization Rules

Actions are ranked by:

- Risk severity (high first)
- Time urgency (due soon/overdue first)
- Impact scope (financial/project impact first)

When data is limited, action templates may be used as fallback, but every item must remain executable (navigable).

## 4. Scope Constraints for This Iteration

- No ACL/permission/baseline rule changes.
- No changes to scene registry/governance/delivery core mechanisms.
- No contract-envelope refactor; orchestration and semantics only.
- Keep the verify main chain passing.

## 5. Product Acceptance Criteria

- First section on load must be "Today Actions".
- Risk alerts must be visible on first screen with user-readable wording.
- Users should understand what to do, why, and where to go without scrolling.
- No exposed debug terms like `result_summary` or `active_filters` in user view.

