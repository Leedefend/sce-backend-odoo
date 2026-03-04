# Grouped Pagination Contract

This document defines the grouped pagination contract exposed by `api.data(list)` when `group_by` is provided.

## Scope

- intent: `api.data`
- op: `list`
- grouped payload keys: `group_summary`, `grouped_rows`
- routing state key: `group_page` (per-group offset map)

## Grouped Row Fields

Each entry in `grouped_rows` must provide:

- `group_key`: stable identity key for per-group paging state
- `field`: grouped field name
- `value`: grouped value
- `label`: grouped display label
- `count`: total rows in group
- `domain`: group-specific domain
- `sample_rows`: paged sample records
- `page_offset`: normalized offset (`floor(offset/page_limit)*page_limit`)
- `page_limit`: effective page size
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

## Verification Hooks

- smoke signature: `scripts/verify/baselines/fe_tree_grouped_signature.json`
- smoke runner: `scripts/verify/fe_tree_view_smoke.js`
- runtime guard: `scripts/verify/grouped_rows_runtime_guard.py`
- semantic guards:
  - `scripts/verify/grouped_pagination_semantic_guard.py`
  - `scripts/verify/grouped_pagination_semantic_drift_guard.py`
- evidence export: `scripts/contract/export_evidence.py`
