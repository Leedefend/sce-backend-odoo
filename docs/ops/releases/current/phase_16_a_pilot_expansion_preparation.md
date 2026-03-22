# Phase 16-A Pilot Expansion Preparation

## 1. What Changed
- Goal:
  - prepare v0.2 expansion planning without changing v0.1 stable behavior
- Completed:
  - defined a design-only multi-task execution model for v0.2
  - defined a design-only multi-role product model for v0.2
  - evaluated `cost / contract / payment` as the second business-chain candidates and selected `payment`
  - standardized pilot feedback collection and decision rules
  - created the v0.2 planning skeleton
- Not completed:
  - no runtime implementation
  - no permission-system implementation

## 2. Impact Scope
- Modules:
  - `docs/ops`
  - `tmp`
- Startup chain:
  - No
- Contract:
  - No
- Public intent:
  - No rename, no new public intent

## 3. Risks
- P0:
  - none introduced to v0.1 runtime because this batch is planning-only
- P1:
  - future v0.2 work may over-expand into parallel execution before queue semantics are frozen
- P1:
  - future role work may confuse product role and ACL role if not kept separate
- P2:
  - second business chain selection could drift without re-checking actual pilot evidence

## 4. Verification
- Commands:
  - `git diff --check`
- Result:
  - PASS

## 5. Artifacts
- `docs/ops/product_v0_2_multi_task_execution_model.md`
- `docs/ops/product_v0_2_multi_role_model.md`
- `docs/ops/product_v0_2_second_business_chain_evaluation.md`
- `docs/ops/product_pilot_feedback_framework_v1.md`
- `docs/ops/product_v0_2_planning_skeleton.md`

## 6. Rollback
- Commit:
  - revert Phase 16-A commit(s)
- Method:
  - revert docs-only changes

## 7. Next Batch
- Goal:
  - freeze the first executable v0.2 semantic slice
- Preconditions:
  - accept payment as the next business chain
  - keep v0.1 compat path as a non-negotiable constraint
