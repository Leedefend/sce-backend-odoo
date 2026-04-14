# ITER-2026-04-13-1853 Report

## Summary

Frozen the full rebuild importer promotion standard and the practical promotion queue.

This batch was docs-only. No scripts, models, artifacts, database records, menus, manifests, or security files were changed.

## Architecture

- Layer Target: Migration Governance Standard
- Module: full rebuild importer promotion gate
- Module Ownership: `docs/migration_alignment`, `agent_ops`
- Kernel or Scenario: scenario
- Backend Sub-Layer: business-fact layer
- Reason: prevent one-off probes from being promoted into production rebuild importers without no-DB mode, identity, idempotency, audit, rollback, verification, and promotion gates

## Changed Files

- `agent_ops/tasks/ITER-2026-04-13-1853.yaml`
- `docs/migration_alignment/full_rebuild_importer_promotion_standard_v1.md`
- `docs/migration_alignment/full_rebuild_promotion_queue_v1.md`
- `agent_ops/reports/2026-04-13/report.ITER-2026-04-13-1853.md`
- `agent_ops/state/task_results/ITER-2026-04-13-1853.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decisions

- Full rebuild importers must pass the staged promotion ladder from `probe` to `repeatable-importer`.
- Every importer must support no-DB mode, slice mode, idempotent strategy, legacy identity, rebuild log, rollback strategy, verification step, and promotion gate.
- Name text is not a valid primary rebuild identity.
- Partner remains the first importer candidate.
- Contract remains blocked until partner and project anchors are ready.
- Attachment file entities are not on the critical path.

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-13-1853.yaml`: PASS
- `python3 -m json.tool agent_ops/state/task_results/ITER-2026-04-13-1853.json`: PASS
- `make verify.native.business_fact.static`: PASS

## Risk

Low. This is a governance/documentation batch only.

## Next Step

Use the standard to gate the next partner write-capable batch. The next write batch still requires explicit authorization because it would create real `res.partner` rows.
