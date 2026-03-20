# Delivery Seal Mode Master Plan v1

## Objective (Locked)

Shift delivery from "feature expansion" to "seal mode" until the product is trial-deliverable for construction enterprise customers.

Success is defined by four outcomes:
- Frontend gate fully green (`lint + typecheck:strict + build`).
- Scene/contract closure reaches strict release blocker level.
- Capability gap backlog reflects real risks (no empty/false-green governance).
- Delivery readiness evidence is one-page, auditable, reproducible.

## Hard Gaps (Must Close)

1. Frontend delivery mainline quality gap.
2. Scene Contract v1 / provider shape / scene_engine closure gap.
3. Governance truthfulness gap (green reports vs empty backlog).
4. Delivery evidence productization gap (playbook != scoreboard).

## Execution Priority

### P0 (This Week, Release Blockers)
- Clear frontend red-line lint/type errors in ActionView mainline and shell.
- Produce system-bound smoke evidence for key scenes in 9 delivery modules.
- Keep `docs/product/capability_gap_backlog_v1.md` as the single source of unresolved blockers.
- Treat contract strict schema, provider shape, and scene_engine migration as release blockers.

### P1 (Immediately After P0)
- Build one-page delivery readiness scoreboard.
- Standardize PM / Finance / Purchase / Executive journey acceptance scripts.
- Publish explicit in-scope/out-of-scope statement for search/sort/pagination/batch actions/approval actions.

### P2 (Post-GA Iteration)
- Continue scene_engine migration for broader scene set.
- Expand semantic closure for widget/x2many/chatter/kanban.
- Extend templates for multi-industry rollout.

## Non-Stop Iteration Policy

- Default policy is autonomous continuation without confirmation prompts.
- Stop-and-ask only for:
  - destructive actions,
  - out-of-allowlist operations,
  - missing critical environment/permission.
- Every iteration must end with:
  - updated backlog status,
  - updated context-switch log,
  - validation command results,
  - categorized commit.

## Standard Iteration Loop

1. Pick one blocker from backlog.
2. Record `Layer Target / Module / Reason`.
3. Implement minimal effective change.
4. Run strict verification chain.
5. Update evidence docs and context-switch log.
6. Commit in single-category scope.
7. Continue to next blocker.

## Mandatory Gates

- Frontend: `pnpm -C frontend gate`
- Backend scene readiness: `make verify.scene.delivery.readiness.role_company_matrix`
- No-action regression guard: `make verify.scene.no_action_scene.guard`

## Current Start Point

- `workspace.home` provider chain is already hardened to profile mainline.
- role+company strict readiness chain is already established.
- next direct focus: frontend blocker closure and delivery scoreboard hardening.

