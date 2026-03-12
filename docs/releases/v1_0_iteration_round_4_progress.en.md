# SCEMS v1.0 Round 4 Progress (Workbench User-Centric)

## Batch Goal (Batch B)

Focus on “business-first actions” and PM-visible data insufficiency, with fact-first diagnosis:

- confirm whether it is permission-related,
- confirm whether it is demo data assignment/ownership-related,
- then converge fallback involvement in `today_actions`.

## Fact Findings

From prod-sim `system.init` runtime checks:

- PM role mainly sees `project_actions` + `risk_actions`.
- Finance role additionally sees `payment_requests`, resulting in higher visible business rows.
- PM “data looks insufficient” is not a pure frontend rendering issue; it is a combined effect of role-visible scope and demo data assignment.

## Changes in This Batch

1. `today_actions` fallback convergence:
   - if business actions are `>=4`, only business actions are rendered;
   - capability fallback is used only when business actions are insufficient.

2. Added business visibility diagnosis:
   - new `diagnostics.business_visibility` output;
   - includes expected collections, missing expected keys, gap level, and likely cause;
   - supports fast triage: permission vs data ownership/assignment.

3. Hero status hint enhancement:
   - when business signal exists but visible collections are limited, show “check project ownership and demo data assignment” hint;
   - prevents users from misreading it as a system failure.

## Impact

- No changes to ACL, scene governance, delivery policy, or login flow.
- No changes to `page_orchestration_v1` primary protocol.
- Only semantic/diagnostic convergence in workbench expression layer.

## Next (Batch C)

- produce a workbench click-to-intent chain checklist;
- freeze 10-second / 30-second acceptance criteria;
- run minimal regression and provide login validation checkpoints.
