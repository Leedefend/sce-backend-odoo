# SCEMS v1.0 Round 4 Workbench User-Centric Iteration Plan

## 1. Objective

This round focuses on a user-first convergence on top of `workspace_home_contract_builder`, moving the workbench from a “capability summary page” toward a true “business action hub”.

Within 10 seconds after entering the workbench, users should clearly know:

1. what to handle first today,
2. which risks are urgent,
3. whether business status is drifting.

## 2. Scope and Non-goals

Strictly out of scope:

- login flow and token/session mechanism,
- scene governance / delivery policy core mechanism,
- ACL baseline and role permission model,
- `page_orchestration_v1` as primary protocol.

Allowed in this round:

- semantic convergence in `workspace_home_contract_builder`,
- default visible section priorities and copy hierarchy,
- default visibility for debug/capability-heavy areas,
- minimal frontend consumption mapping for user-facing view.

## 3. Execution Batches

### Batch A: first-screen semantic convergence (current)

- prioritize `today_actions` and `risk` for action-first narrative,
- converge `group_overview` into “Common Functions”,
- hide noisy `scene_groups` and `filters` by default.

### Batch B: real business action chain calibration

- improve business-first ratio in `today_actions` and `risk.actions`,
- patch PM-visible factual data where needed,
- keep fallback as fallback (no pseudo business metrics).

### Batch C: observability and acceptance

- output workbench click-to-intent chain checklist,
- freeze 10-second / 30-second acceptance criteria,
- run minimal regression and record results.

## 4. Acceptance Criteria

- main user narrative keeps only `hero / today_focus / analysis / quick_entries`,
- no debug field or capability list noise in default user view,
- `today_actions` and `risk.actions` support one-hop navigation,
- existing verify mainline remains intact.

## 5. Minimal Regression

Recommended commands at round end:

- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.phase_next.evidence.bundle`
