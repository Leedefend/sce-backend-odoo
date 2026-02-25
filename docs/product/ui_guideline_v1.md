# UI Guideline v1

## Product Surface
- Keep `system.init` envelope stable: `ok/data/meta`.
- Keep scene payload shape stable across bundles and tiers.
- Role homepage must expose:
  - one primary action area
  - one risk/alert area
  - one workload/approval area

## Navigation
- First-level nav must be task-oriented.
- Scene key naming must be semantic and stable.
- Bundle activation must not break existing nav keys.

## Role Home Defaults
- PM: project lifecycle and execution focus.
- Finance: payment approval and ledger focus.
- Executive: summary KPI and risk focus.
- Owner: owner dashboard and owner approvals.

## Stability Constraints
- No bundle may remove `user/nav/scenes/capabilities/intents` from `system.init`.
- UI shell must tolerate extra fields and missing optional fields.
- Contract version upgrades must follow additive-first strategy.
