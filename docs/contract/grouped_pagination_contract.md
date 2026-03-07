# Grouped Pagination Contract

This document defines the grouped pagination contract exposed by `api.data(list)` when `group_by` is provided.

## Scope

- intent: `api.data`
- op: `list`
- grouped payload keys: `group_summary`, `grouped_rows`
- routing state key: `group_page` (per-group offset map)
- routing state key: `group_fp` (grouped query fingerprint for window staleness guard)
- routing state key: `group_wid` (grouped window identity for window staleness guard)
- routing state key: `group_wdg` (grouped window digest for window content staleness guard)
- routing state key: `group_wik` (grouped unified window identity key for staleness guard)
- request key: `group_page_size` (optional; explicit grouped page size)
- request key: `group_limit` (optional; max grouped entries returned)
- request key: `group_offset` (optional; grouped entries offset)
- request key: `need_group_total` (optional; ask backend to return total grouped entries count)

## Group Summary Fields

Each entry in `group_summary` may provide:

- `group_key`: stable identity key for `(field, value)` pair
- `field`: grouped field name
- `value`: grouped value
- `label`: grouped display label
- `count`: total rows in group
- `domain`: group-specific domain

## Grouped Row Fields

Each entry in `grouped_rows` must provide:

- `group_key`: stable identity key for per-group paging state
- `field`: grouped field name
- `value`: grouped value
- `label`: grouped display label
- `count`: total rows in group
- `domain`: group-specific domain
- `sample_rows`: paged sample records
- `page_requested_size`: requested page size from client (`group_page_size` / fallback sample limit)
- `page_applied_size`: effective backend page size actually used
- `page_requested_offset`: requested offset from route/client state
- `page_applied_offset`: backend-normalized offset after clamp/snap
- `page_max_offset`: max valid offset for current group/page size
- `page_clamped`: whether requested offset was clamped/snap-normalized by backend
- `page_offset`: normalized offset (`floor(offset/page_limit)*page_limit`)
- `page_limit`: effective page size
- `page_size`: explicit page size alias (equal to `page_limit`, recommended for new clients)
- `page_current`: 1-based page index
- `page_total`: total pages (`max(1, ceil(count/page_limit))`)
- `page_range_start`: 1-based inclusive range start
- `page_range_end`: inclusive range end
- `page_window.start`: inclusive range start (aggregated view)
- `page_window.end`: inclusive range end (aggregated view)
- `page_has_prev`: whether previous page exists
- `page_has_next`: whether next page exists

## Compatibility Rules

1. `page_window` is additive and does not replace `page_range_start/page_range_end`.
2. Frontend should prefer `page_window` when present; fallback to legacy range fields otherwise.
3. `group_key` must be stable for a given `(field, value)` pair to preserve route paging restoration.
4. `page_has_prev/page_has_next` are authoritative backend semantics; frontend should avoid recomputing when these flags exist.
5. For grouped window navigation, frontend should prefer `next_group_offset/prev_group_offset` over local offset arithmetic when present.
6. `group_wid` is route-local state. When it mismatches backend `group_paging.window_id` under non-zero `group_offset`, frontend must reset grouped window state to first window.
7. `group_wdg` is route-local state. When it mismatches backend `group_paging.window_digest` under non-zero `group_offset`, frontend must reset grouped window state to first window.
8. Frontend should prefer `window_identity` when present; fallback to flat fields (`window_id/query_fingerprint/window_digest/window_key`) for compatibility.
9. `window_identity.version/algo` define digest protocol. Clients should treat unknown versions as non-authoritative and fallback to tolerant comparison.
10. `group_wik` is route-local state. When it mismatches backend `group_paging.window_identity.key` under non-zero `group_offset`, frontend must reset grouped window state to first window.

## Group Paging Summary

`api.data(list)` may include top-level `group_paging`:

- `group_by_field`: resolved primary grouped field
- `group_limit`: effective grouped result limit
- `group_offset`: effective grouped result offset
- `group_count`: grouped entries returned
- `group_total`: grouped entries total count (only when `need_group_total=true`)
- `has_more`: whether there are more grouped entries after current window
- `next_group_offset`: next grouped window offset (when `has_more=true`)
- `prev_group_offset`: previous grouped window offset (when current offset > 0)
- `window_start`: 1-based grouped window start index (0 when window empty)
- `window_end`: 1-based grouped window end index (0 when window empty)
- `window_id`: backend window identity for current grouped window
- `query_fingerprint`: normalized grouped query fingerprint
- `window_digest`: digest of current grouped window content (`group_key/count` projection)
- `window_key`: flat alias of `window_identity.key` for compatibility
- `window_identity`: normalized object form `{window_id, query_fingerprint, window_digest, version, algo, key, window_start, window_end, prev_group_offset, next_group_offset, has_more, group_offset, group_limit, group_count, group_total?}`
- `page_size`: effective grouped page size
- `has_group_page_offsets`: whether request carried per-group offset map

## Verification Hooks

- smoke signature: `scripts/verify/baselines/fe_tree_grouped_signature.json`
- smoke runner: `scripts/verify/fe_tree_view_smoke.js`
- runtime guard: `scripts/verify/grouped_rows_runtime_guard.py`
- semantic guards:
  - `scripts/verify/grouped_pagination_semantic_guard.py`
  - `scripts/verify/grouped_pagination_semantic_drift_guard.py`
- evidence export: `scripts/contract/export_evidence.py`

## Drift Diagnostics

When grouped behavior drifts across backend/frontend/evidence, follow this order:

1. `python3 scripts/verify/grouped_pagination_semantic_guard.py`
2. `python3 scripts/verify/grouped_contract_consistency_guard.py`
3. `python3 scripts/verify/grouped_drift_summary_guard.py`
4. `python3 scripts/verify/grouped_drift_summary_schema_guard.py`
5. `python3 scripts/verify/grouped_drift_summary_baseline_guard.py`
6. `python3 scripts/verify/grouped_governance_brief_guard.py`
7. `python3 scripts/verify/grouped_governance_brief_schema_guard.py`
8. `python3 scripts/verify/grouped_governance_brief_baseline_guard.py`
9. `python3 scripts/verify/grouped_governance_policy_matrix.py`
10. `python3 scripts/verify/grouped_governance_policy_matrix_schema_guard.py`
11. `python3 scripts/verify/grouped_governance_trend_consistency_guard.py`
12. `python3 scripts/verify/grouped_governance_trend_consistency_schema_guard.py`
13. `python3 scripts/verify/grouped_governance_trend_consistency_baseline_guard.py`
14. `python3 scripts/contract/export_evidence.py`
15. `python3 scripts/verify/contract_evidence_schema_guard.py`
16. `python3 scripts/verify/contract_evidence_guard.py`

Drift summary guard emits artifacts for audit:

- `artifacts/grouped_drift_summary_guard.json`
- `artifacts/grouped_drift_summary_guard.md`
- `artifacts/grouped_governance_brief_guard.json`
- `artifacts/grouped_governance_brief_guard.md`
- `artifacts/grouped_governance_policy_matrix.json`
- `artifacts/grouped_governance_policy_matrix.md`
- `artifacts/grouped_governance_trend_consistency_guard.json`
- `artifacts/grouped_governance_trend_consistency_guard.md`

If only e2e snapshot mismatches, re-run:

```bash
E2E_GROUPED_SNAPSHOT_UPDATE=1 make verify.e2e.contract
```

Then inspect the generated baseline diff before committing.
