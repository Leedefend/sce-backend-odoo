# Product Native Alignment Gate Rules v1

## Goal
- Make native alignment enforceable before new business-slice code lands.

## Gate Rules

### Rule 1: No shadow project-domain scene family
- Forbidden:
  - `project.payment.*`
  - `project.contract.*`
  - `project.cost.*`
- Reason:
  - these names indicate project-scoped business scene duplication instead of native reuse

### Rule 2: Orchestration must deep-link to native scene
- Required:
  - project-side next action points to a native finance / contract / cost scene anchor
- Forbidden:
  - project-side handlers that own finance / contract / cost record creation lifecycle

### Rule 3: Frontend stays generic
- Forbidden:
  - frontend special branches that render custom payment / contract / cost record blocks for a new shadow scene family
- Allowed:
  - generic blocker copy and deep-link action consumption

### Rule 4: Verify must validate corrected direction
- New smoke or guards must validate:
  - native handoff
  - mapping declaration
  - absence of shadow intent family

### Rule 5: Risk findings block implementation approval
- If guard finds shadow-intent files in the current change set:
  - implementation is blocked
  - only redesign / documentation / cleanup work may proceed

## Executable Guard
- command:
  - `python3 scripts/verify/product_native_alignment_guard.py`
- Make target:
  - `make verify.product.native_alignment_guard`

## Current Expected Outcome
- With the current uncommitted payment draft, the guard should report findings and block strict approval.
