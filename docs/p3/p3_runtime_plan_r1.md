# P3 Runtime R1 Plan (Bootstrap)

Goal: establish a runnable runtime skeleton for P3 reconciliation + audit query, wired into smoke.

## Scope

- Provide a minimal smoke runner (`p3.smoke`) and wrapper.
- Provide a placeholder Odoo shell script that reports PASS/FAIL.
- No runtime reconciliation logic implemented in this sprint.

## Non-Goals

- No UI changes.
- No data model changes.
- No audit query API implementation.

## Acceptance

- `make p3.smoke DB=sc_p3` runs and exits 0 with RESULT: PASS.
- `make ci.gate.tp08 DB=sc_demo` passes.
- Working tree clean after restoring `docs/audit` outputs.

## Commands

- `make p3.smoke DB=sc_p3`
- `make ci.gate.tp08 DB=sc_demo`
