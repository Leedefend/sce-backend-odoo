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

## Batch D: Semantic Convergence for Project Ledger and Project List

### Goal

Align `projects.ledger` and `projects.list` with cockpit semantics:

- unified status semantics (localized labels + consistent completion detection),
- unified amount semantics (contract amount first + friendly `万/亿` format),
- unified field priority (`name/status/owner/amount/write_date`).

### Changes

1. Added list profile presets for `projects.list` and `projects.ledger`:
   - `name`, `stage_id`, `user_id`, `dashboard_invoice_amount`, `write_date`.

2. Refactored ledger overview strip:
   - running project count (non-completed states),
   - warning project count (`danger/warning`),
   - completed project count (same completion semantics),
   - contract amount summary (fallback to project scale when amount is absent).

3. Refactored `projects.list` summary strip:
   - warning/completed detection aligned with ledger,
   - amount summary uses the same amount formatting semantics.

### Compatibility

- No changes to `DynamicTable` core mechanism;
- No changes to backend contract envelope;
- Frontend expression and field-priority convergence only, preserving existing filter/sort/search behavior.

## Fixed Regression Add-on: Release Demo Seed Closure

Starting from this round, the following two commands are mandatory regression items:

1. `make demo.load.release DB_NAME=sc_demo`
2. `make verify.demo.release.seed DB_NAME=sc_demo`

Execution semantics for this round:

- `demo.load.release`: loads the complete release-grade demo seed set (business chain + cockpit-readable data).
- `verify.demo.release.seed`: verifies the key baseline (showroom coverage, non-empty contract/cost/finance for `project_id=20`, and complete release role users).
