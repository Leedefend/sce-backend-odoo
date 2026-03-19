# Codex Delivery Collaboration Protocol v1

## Purpose

Keep iteration speed high and context stable while continuously closing delivery blockers.

## Collaboration Rules (Persistent)

- Use autonomous continuation by default; do not pause for routine confirmations.
- Request confirmation only for risk/destructive/out-of-policy actions.
- Keep changes scoped and categorized by blocker type.
- Always include and persist:
  - `Layer Target`
  - `Module`
  - `Reason`

## Context-Switch Stability Rules

- Maintain a running context-switch log in `docs/ops/iterations/delivery_context_switch_log_v1.md`.
- On every switch, record:
  - last completed step,
  - current blocker key,
  - active branch/commit,
  - next exact command/gate.
- Resume must start from the last `Next Step` line in the log, not from memory.

## Output Contract Per Iteration

Each iteration handoff must include:
- blocker addressed,
- files changed,
- commands executed and pass/fail,
- commit id,
- next step.

## Quality Contract

- Frontend blocker work must end in `pnpm -C frontend gate` green.
- Scene/runtime blocker work must end in `make verify.scene.delivery.readiness.role_company_matrix` green.
- Governance blocker work must update backlog/doc evidence in same iteration.

## Escalation Conditions

Escalate immediately when:
- gate repeatedly fails due to environment breakage,
- required credentials/seed data are missing,
- baseline thresholds conflict with observed stable runtime reality.

