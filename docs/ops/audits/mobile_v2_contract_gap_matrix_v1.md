# Mobile Unified Page Contract v2 Gap Matrix v1

Date: 2026-05-05
Branch: `codex/mobile-contract-sync-plan`
Scope: `frontend/apps/mobile/src/pages/contract/index.vue`

## Purpose

This matrix makes the mobile terminal v2 contract iteration track explicit.
It separates closed capabilities, remaining gaps, deferred scope, and the
verification gates used for each batch.

## Current Status

Mobile now consumes the platform `ui.contract.v2` contract directly for the
core render path. The branch has moved from a read-only mobile contract page
to a compact v2 renderer that can consume status, data, action, runtime, trace,
relation, and onchange patch surfaces.

This is not yet a full native-grade form runtime. The remaining gaps are
mostly richer field controls, standard form command execution, domain-aware
option refresh, and real terminal acceptance.

## Closed Capability Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| v2 entrypoint | Closed | `ui.contract.v2` is the only terminal entry; guarded by `scripts/verify/unified_page_contract_v2_intent_guard.py`. |
| client trimming | Closed | mobile compact path keeps platform source authority and omits full source compat payload. |
| global status | Closed | mobile honors `globalStatus.pageVisible/pageAuth` and blocks unreadable pages. |
| container status | Closed | container visibility/disabled state is inherited through nested container walking. |
| widget status | Closed | `widgetStatus` drives field visible/readonly/required/disabled state. |
| button status | Closed | `buttonStatus` gates rendered command actions. |
| selector status | Closed | exact selector and `.*` prefix selector status are consumed and patch-mergeable. |
| inline data | Closed | `mainData`, `tableRows`, and `treeData` can hydrate mobile records. |
| primary dataSource | Closed | list/read requests use contract `dataSource`, fields, pagination, and trace context. |
| table/tree pagination alignment | Closed | inline data key and `pagination[dataKey]` stay aligned for load-more. |
| row data patch merge | Closed | table/tree/relation rows merge by id unless patch operation requests replace/full. |
| relationRows display | Closed | relation widgets render rows, summary fields, and row counts. |
| relationRows pagination | Closed | relation pagination hints and remote loading are supported. |
| relation line patches | Closed | `relationRows.line_patches` support create/update/remove-style row merge. |
| bounded relation row editing | Closed | relation rows can be added, edited, or removed through `line_patches`, and form save carries current relationRows. |
| dictData labels | Closed | `dictData` can map stored values to display labels. |
| statusPatch merge | Closed | global/container/widget/button/selector patch rows merge into current contract. |
| layout/runtime patch preservation | Closed | `layoutPatch` and `runtimePatch` preserve top-level contract sections. |
| action response patch | Closed | execute-button responses can apply `unified_page_patch_v2`. |
| action feedback | Closed | warnings, result messages, effect messages, and toast effects are surfaced. |
| durable warning feedback | Closed | response warnings are kept in a transient page-level warning stack near the header. |
| action refreshMode | Closed | `none`, `partial`, and `full` refresh modes are honored. |
| action target dependencies | Closed | `targetIds` and `dependencyGraph` can escalate partial refresh to full contract reload. |
| action targetScope refresh | Closed | `targetScope=dataSource` refreshes records and `targetScope=runtime/contract` refreshes the full contract. |
| meta/runtime observability | Closed | trace/request/etag/snapshot and runtime cache/retry policy are visible in the summary. |
| runtime retry policy | Closed | intent requests honor `runtimeContract.retryPolicy` for bounded retries on network, timeout, 408, 429, and 5xx failures. |
| H5 compile acceptance | Closed | `verify.unified_page_contract.v2.harmony_h5_compile_acceptance.host` builds the mobile H5 target and records artifacts. |
| trace propagation | Closed | data, relation, and execute-button follow-up requests carry trace/request/etag/snapshot context. |
| diagnostic errors | Closed | failures preserve `reason_code` and `trace_id` in visible error/toast text. |
| field onchange trigger | Closed | editable fields can trigger `api.onchange` with `include_v2_patch`. |
| submitPolicy debounce | Closed | `submitPolicy.debounceMs/debounce_ms` controls server-debounced onchange delay. |
| tracePolicy required | Closed | field onchange generates a mobile request id when trace is required and absent. |
| modifiers fallback | Closed | compatibility `data.modifiers_patch` maps to `statusPatch.widgetStatus`. |
| line_patches fallback | Closed | compatibility `data.line_patches` maps to `dataPatch.relationRows.line_patches`. |
| editable value type | Closed | number-like editable fields use numeric input and preserve numeric onchange values. |
| date/datetime controls | Closed | date fields use a date picker; datetime fields use paired date/time pickers and still trigger onchange. |
| compact boolean/selection controls | Closed | boolean fields render switch controls; selection fields render dictData-backed pickers. |
| remote selection option bootstrap | Closed | selection/radio fields can load contract-declared `dataSource` options into `dictData`. |
| local many2one picker | Closed | many2one/select.remote fields render a dictData-backed picker when local options are delivered. |
| remote many2one option bootstrap | Closed | many2one/select.remote fields can load contract-declared `dataSource` options into `dictData`. |
| remote many2one search | Closed | remote many2one fields expose a compact search box and send `search/query/name_search` to the option dataSource. |
| domain-aware field option refetch | Closed | onchange `modifiers_patch.domain/domain_raw` invalidates selection/many2one options and the next option request carries domain/context params. |
| standard form command dispatch | Closed | `form.save`, `form.validate`, and `record.delete` can dispatch through the intent runtime with trace, feedback, patch, and refresh handling. |
| non-executable action filtering | Closed | unsupported command actions are hidden instead of shown as broken buttons. |

## Remaining Gap Matrix

| Gap ID | Priority | Status | Description | Next Batch Candidate |
| --- | --- | --- | --- | --- |
| M2-G01 | P1 | Closed | `modifiers_patch.domain/domain_raw` can invalidate and refetch remote selection and many2one options through contract-declared option dataSources. | Monitor backend option dataSource coverage in terminal acceptance. |
| M2-G02 | P1 | Closed | `boolean`, `selection`, local dict-backed `many2one`, remote option bootstrap, domain-aware refetch, and remote many2one search now have compact controls. | Monitor large-dataset terminal acceptance and tune search request shape if backend requires it. |
| M2-G03 | P1 | Closed | `date` and `datetime` fields now use terminal-safe picker controls instead of plain text input. | Monitor terminal acceptance and add timezone-specific handling only if backend values require it. |
| M2-G04 | P1 | Closed | standard v2 actions `form.save`, `form.validate`, and `record.delete` now have a bounded mobile intent dispatch path; full native-grade Odoo form semantics remain deferred. | Monitor backend intent compatibility and add terminal acceptance coverage. |
| M2-G05 | P2 | Closed | warnings are surfaced via toast and retained in a transient page-level warning stack near the header. | Monitor terminal acceptance and tune duration/copy if needed. |
| M2-G06 | P2 | Closed | relation rows now support bounded add/edit/remove through a compact mobile editor that writes v2 `line_patches`; form save carries current relationRows. | Monitor business workflows and expand field-specific controls only where relation schemas require them. |
| M2-G07 | P2 | Closed | `targetScope=dataSource/runtime/contract` now has specialized mobile refresh behavior in addition to refreshMode and target dependency handling. | Monitor backend targetScope usage in terminal acceptance. |
| M2-G08 | P2 | Closed | runtime retry policy is now executed by the mobile intent request layer; offline/cache semantics remain deferred. | Monitor terminal acceptance and add offline/cache behavior only when product scope requires it. |
| M2-G09 | P0 before release | Partial | H5 compile acceptance is now executable and artifacted; real device or mini-program runtime acceptance is still pending. | Add real device, mini-program, or browser runtime screenshot acceptance before release. |
| M2-G10 | P2 | Open | accessibility and dense mobile layout behavior have not had visual regression coverage. | Add Playwright/mobile screenshot checks for representative contracts. |

## Deferred Scope

The following items are intentionally not claimed closed:

- full native-grade Odoo form save/delete/validate semantics;
- advanced typeahead ranking/highlighting for large remote datasets;
- real device, mini-program, or browser runtime screenshot acceptance;
- offline/cache semantics from `runtimeContract`.

## Iteration Order

Recommended next sequence:

1. `M2-G10`: improve visual proof.
2. `M2-G09`: add real device, mini-program, or browser runtime screenshot acceptance when the post-close acceptance window opens.

## Verification Gates

Every implementation batch on this branch should continue to run:

```bash
python3 scripts/verify/unified_page_contract_v2_intent_guard.py
python3 -m py_compile scripts/verify/unified_page_contract_v2_intent_guard.py
pnpm -C frontend/apps/mobile typecheck
git diff --check
make verify.unified_page_contract.v2
make verify.docs.all
```

Documentation-only batches may skip mobile typecheck when no frontend file is
changed, but should still run `git diff --check` and `make verify.docs.all`.
