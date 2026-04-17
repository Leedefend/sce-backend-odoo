# Legacy Payment Approval Semantic Screen v1

## Scope
- Source: `LegacyDb.dbo.S_Execute_Approval` joined with setup step/template names.
- Target: rows that resolve to imported `payment.request` assets through migration manifests.
- Mode: read-only semantic screen; no Odoo business records are mutated.

## Counts
- Raw workflow rows: 163245
- Payment-target workflow rows: 60337
- Payment distinct targets: 23316
- Row semantics: `{"historical_approved": 7, "workflow_trace_with_actor_time": 60330}`
- Target semantics: `{"historical_approved": 7, "historical_pending_or_trace_only": 23309}`

## Safe Interpretation
- `f_SPZT in [1, 2, 3]` is treated as historical approval.
- Non-neutral `f_Back_YJLX` or rejected status values are treated as historical reject/back.
- `f_SPZT = 0` with neutral back type is not treated as approval; it remains pending/trace-only.

## Key Finding
Most payment-target rows are legacy workflow traces with `f_SPZT=0` and neutral back type. They prove workflow existence, not final approval.

## Next Decision
A future write batch may surface target-level `historical_approved` or `historical_pending_or_trace_only`, but should not convert trace-only rows into current workflow approval.

## Top Field Combinations
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=2 / targets=1 / step=董事长流程
- workflow_trace_with_actor_time / lane=receipt / status=0 / back=0 / rows=1 / targets=1 / step=财务部
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=财务总监流程
- workflow_trace_with_actor_time / lane=receipt / status=0 / back=0 / rows=1 / targets=1 / step=财务部
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=工程部
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=财务部
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=财务部
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=总经理
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=工程部
- workflow_trace_with_actor_time / lane=outflow_request / status=0 / back=0 / rows=1 / targets=1 / step=工程部
