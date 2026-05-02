# Unified Semantic Page Contract Lite - Adapter Source Coverage Batch 3

Date: 2026-05-01
Status: Phase 1 source coverage expansion

## 1. Boundary

Layer Target: Contract Governance / Backend Semantic Adapter Coverage

Module:

- `addons/smart_core/core/unified_page_contract_lite_adapter.py`
- `docs/architecture/unified_page_contract_lite/fixtures`
- `docs/architecture/unified_page_contract_lite/snapshots`
- `scripts/verify/unified_page_contract_lite_adapter_guard.py`
- `Makefile`

Reason:

Batch-2 proved a single form source and onchange patch can be converted to Lite. Batch-3 expands static coverage to list/tree, search, and relation access-policy status without connecting the adapter to runtime delivery.

## 2. Added Coverage

### Tree/List Source

Fixture:

```text
docs/architecture/unified_page_contract_lite/fixtures/project_tree_semantic_source_v1.json
```

Snapshot:

```text
docs/architecture/unified_page_contract_lite/snapshots/project_tree_lite_adapter_snapshot_v1.json
```

Coverage:

- `viewType=tree`
- columns mapped to widget list
- readonly profile
- disabled relation field from `access_policy.degraded_fields`
- enabled and disabled record actions

### Search Source

Fixture:

```text
docs/architecture/unified_page_contract_lite/fixtures/project_search_semantic_source_v1.json
```

Snapshot:

```text
docs/architecture/unified_page_contract_lite/snapshots/project_search_lite_adapter_snapshot_v1.json
```

Coverage:

- `viewType=search`
- search fields mapped to Lite widgets
- filter actions as server-dispatched action declarations
- quick filter data in `dictData`

### Adapter Guard

`scripts/verify/unified_page_contract_lite_adapter_guard.py` now supports multiple contract cases through repeated `--contract-case SOURCE SNAPSHOT`.

## 3. Schema Update

Lite schema now includes `search` in `pageInfo.viewType` and `layoutContract.layoutType`.

This is a coverage correction, not a top-level contract change. The Lite top-level remains fixed:

```text
pageInfo / layoutContract / statusContract / actionContract / dataContract / meta
```

## 4. Still Not Done

- No `ui.contract` runtime connection.
- No `login` or `system.init` change.
- No frontend runtime change.
- No `runtimeContract`.
- No component registry, capabilities, selector status, dependency graph, realtime, collaboration, or AI orchestration.

## 5. Next Batch

Recommended next batch:

```text
Lite Phase 1 / Batch-4 - Adapter Governance Hardening
```

Focus:

- stronger adapter guard for ID stability
- explicit no-public-intent-touch guard
- source coverage report counters
- patch status/data separation checks

Do not connect runtime delivery until the adapter guard reports stable multi-source coverage.
