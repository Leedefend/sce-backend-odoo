# Payment Ledger Isolation Authority Screen v1

## Trigger
- Stage-gate blocker from `ITER-2026-04-07-1272`:
  - `native_business_fact_isolation_anchor_verify`
  - missing anchor: `payment.ledger.company_id`

## Why current lane cannot implement directly
- Repository stop condition marks `*payment*` paths as high risk.
- Current lane allows native fact verification and docs, but forbids direct payment-model edits unless dedicated high-risk authority batch is established.

## Required implementation objective (next batch)
- Objective type: dedicated high-risk payment isolation anchor recovery.
- Scope: additive business-fact anchor supply only.
- Non-goals:
  - no payment金额语义变更
  - no审批流语义变更
  - no ACL/record-rule file edits in same batch

## Proposed allowlist for implementation batch
- `addons/smart_construction_core/models/core/payment_ledger.py`
- `addons/smart_construction_core/models/core/payment_request.py` (only if related/compute anchor wiring required)
- `scripts/verify/native_business_fact_isolation_anchor_verify.py` (if assertion needs updated model mapping details)
- `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1274.md`
- `agent_ops/state/task_results/ITER-2026-04-07-1274.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Mandatory guardrails for implementation batch
- Additive only: introduce `company_id` anchor without removing existing fields.
- Cross-model consistency: ensure `payment.ledger.project_id -> project.project.company_id` derivation is deterministic.
- Backward safety: existing records should obtain consistent company value (related/compute default strategy) without data loss.
- Verification in same batch:
  - `make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`
  - gate must pass `native_business_fact_isolation_anchor_verify`.

## Risk statement
- High-risk due payment-path touch.
- Must remain semantics-preserving at business-fact layer.
- If any sign of payment financial semantics drift appears, batch must stop immediately.
