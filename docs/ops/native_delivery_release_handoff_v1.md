# Native Delivery Release & Handoff Mapping v1

## Purpose
- Map current native delivery acceptance evidence into:
  - release-note publication payload
  - customer acceptance handoff checklist

## Source of Truth
- Acceptance dossier: `docs/ops/native_delivery_acceptance_dossier_v1.md`
- Iteration evidence chain:
  - `1275` project organization fact closure
  - `1277` member-bound rule closure
  - `1278` non-member denial runtime proof
  - `1279` fixed real-user allow matrix
  - `1281` strict fixed outsider deny matrix

## Release Note Payload

### Scope Statement
- Native business-fact layer reaches delivery-ready status for:
  - runtime gate stability
  - project organization fact modeling
  - project-member access boundary binding
  - fixed-user runtime acceptance matrix

### User-Visible Outcomes
- Project can maintain key roles and member carrier natively.
- Core object visibility follows project-member facts.
- Strict outsider deny evidence is reproducible with seeded outsider account.

### Validation Summary
- Module upgrade and stage-gate checkpoints are pass.
- Runtime verify chain includes both allow and deny evidence.

## Customer Handoff Checklist
- Provide accepted runtime URL and DB context.
- Confirm real-role login set for owner/pm/finance.
- Confirm outsider account `outsider_seed` is available (password policy aligned).
- Run acceptance scripts in order:
  1. stage gate
  2. fixed-user matrix verify (strict outsider deny mode)
- Archive script output and attach to customer sign-off package.

## Handoff Decision Rule
- Mark handoff `READY` only when all following are true:
  - acceptance dossier is current
  - strict outsider deny matrix re-run passes in target env
  - no new blocker appears in delivery context log
