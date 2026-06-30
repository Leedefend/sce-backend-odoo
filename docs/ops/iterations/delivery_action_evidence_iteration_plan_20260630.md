# Delivery Action Evidence Iteration Plan 2026-06-30

## Objective

Turn the non-blocking "Known Limits" in `docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md`
into script-bound journey/action evidence after the low-code release closure PR.

This plan starts after PR `#858` because release-blocking low-code and delivery readiness gates are already
green. The next iteration should not reopen release blockers unless a live gate regresses.

## Baseline

- source PR: `https://github.com/Leedefend/sce-backend-odoo/pull/858`
- branch: `topic/lowcode-release-closure`
- latest release closure head at planning time: `f0631df5a`
- current scoreboard posture: strict `PASS`, restricted `PASS`
- current governance truth guard: `PASS`

## P0: Script-Bound Action Evidence

1. Project execution task action smoke
   - Status: done
   - Scope: `projects.dashboard`, `projects.execution`
   - Target: PM role can open task list/board, advance one safe task action, and refresh the scene without losing contract shape.
   - Evidence target: `make verify.delivery.project_task.action_smoke`, `artifacts/backend/project_task_action_smoke.json`, and the scoreboard row `Project task action smoke`.

2. Payment approval chain scoreboard integration
   - Status: done
   - Scope: `finance.payment_requests`, `finance.center`
   - Target: existing payment approval smoke result is written into the delivery readiness scoreboard evidence summary.
   - Evidence target: `artifacts/backend/payment_request_approval_chain_summary.json` and the scoreboard row `Payment approval chain smoke`.
   - Note: `payment_request_approval_field_consumer_audit` still reports deprecated field references in non-strict mode; this is not part of the action handoff smoke closure.

3. Purchase/material action replay
   - Status: done
   - Scope: `material.center`, `material.procurement`, `material.inbound`, `labor.request`, `equipment.request`, `subcontract.request`
   - Target: list/search/open action replay for采购/材料/租赁 entry scenes using stable demo seed data.
   - Evidence target: `make verify.delivery.material.action_replay`, `artifacts/backend/material_action_replay_smoke.json`, and the scoreboard row `Material action replay smoke`.

## P1: Read-Only and Ledger Evidence

1. Executive read-only acceptance
   - Status: done
   - Scope: `portal.dashboard`, `finance.operating_metrics`, `portal.capability_matrix`; `projects.dashboard_showcase` is recorded when the demo action is installed.
   - Target: executive role can see the read-only journey scenes, read operating metrics, and cannot create/write operating metric records.
   - Evidence target: `make verify.delivery.executive.readonly`, `artifacts/backend/executive_readonly_smoke.json`, and the scoreboard row `Executive readonly smoke`.

2. Treasury/settlement ledger snapshot
   - Status: done
   - Scope: `finance.payment_ledger`, `finance.treasury_ledger`, `finance.settlement_orders`
   - Target: ledger list/search/count snapshots are stable across refresh and company scope.
   - Evidence target: `make verify.delivery.ledger.snapshot`, `artifacts/backend/ledger_snapshot_smoke.json`, and the scoreboard row `Ledger snapshot smoke`.

3. Cost search and pagination smoke
   - Status: done
   - Scope: `cost.project_budget`, `cost.project_cost_ledger`, `cost.profit_compare`
   - Target: search, pagination, and detail open actions work under PM and finance roles.
   - Evidence target: `make verify.delivery.cost.search_pagination`, `artifacts/backend/cost_search_pagination_smoke.json`, and the scoreboard row `Cost search pagination smoke`.

## P2: Governance and Long-Run Proof

1. Quality/safety closure action proof
   - Scope: `quality.center`, `safety.center`
   - Status: done
   - Target: close one safe quality/safety loop in demo data and prove audit/photo evidence guardrails.
   - Evidence target: `make verify.delivery.quality_safety.closure`, `artifacts/backend/site_quality_safety_closure_audit.json`, and the scoreboard row `Quality safety closure smoke`.

2. Lifecycle audit export evidence
   - Scope: `portal.lifecycle`, `portal.capability_matrix`
   - Status: done
   - Target: lifecycle dashboard and capability matrix machine-readable export is produced and linked.
   - Evidence target: `make verify.delivery.lifecycle.audit_export`, `artifacts/backend/lifecycle_audit_export.json`, and the scoreboard row `Lifecycle audit export`.

3. Default scene semantic monitoring
   - Status: done
   - Scope: `default`
   - Target: keep placeholder/default semantics explicit and non-regressive.
   - Evidence target: `make verify.delivery.default_scene.semantic_monitor`, `artifacts/backend/default_scene_semantic_monitor.json`, and the scoreboard row `Default scene semantic monitor`.

## Exit Rules

- Do not mark a Known Limit closed unless a repeatable command produces an artifact.
- Each closed item must update both the artifact path and the scoreboard evidence row.
- If a smoke needs live browser access, provide a restricted API fallback and document the profile boundary.
