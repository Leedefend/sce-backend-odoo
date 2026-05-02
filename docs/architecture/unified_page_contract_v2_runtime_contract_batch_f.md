# Unified Page Contract v2+ RuntimeContract Batch-F

Date: 2026-05-01
Status: Batch-F implementation note

## Layer Target

Contract Governance / RuntimeContract Protocol

## Module

- `addons/smart_core/core/unified_page_contract_v2_runtime.py`
- `docs/architecture/unified_page_contract_v2/fixtures/runtime_contract_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/runtime_contract_snapshot_v1.json`
- `scripts/verify/unified_page_contract_v2_runtime_guard.py`
- `docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json`
- `Makefile`

## Reason

The frontend runtime needs a control plane for patch strategy, cache, retry, hydration, virtualization, trace, snapshot, complexity budget, and AI suggestion policy. This must be standardized without turning the contract into an executable DSL VM.

## Runtime Boundary

`RuntimeContract` may contain:

- `patchStrategy`
- `cachePolicy`
- `optimistic`
- `lazyContainer`
- `virtualization`
- `retryPolicy`
- `renderStrategy`
- `hydration`
- `patchOperations`
- `tracePolicy`
- `complexityBudget`
- `aiEnvelope`

It must not contain:

- scripts
- functions
- eval
- expressions
- JSON logic
- BPMN/workflow VM instructions
- loops
- component code
- permission or business rule execution

## Cross-Contract Guard

The runtime guard checks:

- fixed six-operation patch registry
- `meta.etag/snapshotId/traceId/requestId`
- `dependencyGraph` contains edge lists only
- `componentRegistry` exists for adapter resolution
- `selectorStatus` rows are selector-addressable
- AI envelope is suggestion-only and non-executable
- complexity budget is computable from layout/action/status/data size

## Upgrade Assessment

No Odoo model field, view, security, data XML, cron, or manifest dependency is added.

Result:

- `-u smart_core`: not required for this batch.
- service restart: not required for static validation; required only if a live Odoo worker must import the new module without process reload.

## Verification

Primary restricted target:

```bash
make verify.unified_page_contract.v2
```

Runtime-only target:

```bash
make verify.unified_page_contract.v2.runtime
```

## Rollback

Revert:

- `addons/smart_core/core/unified_page_contract_v2_runtime.py`
- `scripts/verify/unified_page_contract_v2_runtime_guard.py`
- `docs/architecture/unified_page_contract_v2/fixtures/runtime_contract_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/runtime_contract_snapshot_v1.json`
- runtime schema optional field additions
- `Makefile` runtime target changes

No database rollback is required.
