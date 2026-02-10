# Suggested Action Contract

## Purpose

This document defines the frontend contract for `suggested_action` parsing and execution.

## Source Modules

- `frontend/apps/web/src/app/suggested_action/types.ts`
  - canonical action kind union and option types.
- `frontend/apps/web/src/app/suggested_action/parser.ts`
  - raw string normalization and parsing.
  - alias map and prefix-based parsing rules.
- `frontend/apps/web/src/app/suggested_action/presentation.ts`
  - label/hint mapping for each action kind.
- `frontend/apps/web/src/app/suggested_action/runtime.ts`
  - action execution and capability checks.

Compatibility entrypoint:
- `frontend/apps/web/src/app/suggestedAction.ts`

## Stability Rules

- Add new action kind in `types.ts` first.
- Add parser coverage (`parser.ts`) for canonical key and aliases.
- Add UI label and hint (`presentation.ts`).
- Add runtime executability and execution path (`runtime.ts`).
- Keep `suggestedAction.ts` exports backward-compatible.

## Observability

- `useSuggestedAction.run()` records execution events into frontend trace storage.
- Trace event type: `suggested_action`
- Captured fields:
  - `suggested_action_kind`
  - `suggested_action_raw`
  - `suggested_action_success`
- Filter/export APIs (`frontend/apps/web/src/services/trace.ts`):
  - `listSuggestedActionTraces({ kind?, success?, limit?, since_ts? })`
  - `exportSuggestedActionTraces({ kind?, success?, limit?, since_ts? })`
  - export payload includes:
    - `summary.total`
    - `summary.success_count`
    - `summary.failure_count`
    - `summary.top_k`
- HUD export actions:
  - `Export SA all`
  - `Export SA ok`
  - `Export SA fail`
  - `Export SA 1h`
  - `Export SA 24h`
  - top-k dynamic kind buttons (fallback defaults: `open_record`, `copy_trace`, `refresh`)
- HUD fields in `AppShell`:
  - `sa_kind`
  - `sa_success`
  - `sa_ts`

## Verification

Contract guard:

```bash
make verify.frontend.suggested_action.contract_guard
```

Parser guard:

```bash
make verify.frontend.suggested_action.parser_guard
```

Runtime guard:

```bash
make verify.frontend.suggested_action.runtime_guard
```

Import boundary guard:

```bash
make verify.frontend.suggested_action.import_boundary_guard
```

Usage guard:

```bash
make verify.frontend.suggested_action.usage_guard
```

Trace export guard:

```bash
make verify.frontend.suggested_action.trace_export_guard
```

Top-k guard:

```bash
make verify.frontend.suggested_action.topk_guard
```

Since filter guard:

```bash
make verify.frontend.suggested_action.since_filter_guard
```

HUD export guard:

```bash
make verify.frontend.suggested_action.hud_export_guard
```

Catalog export:

```bash
make verify.frontend.suggested_action.catalog
```

Catalog artifact:

- `artifacts/codex/suggested_action_catalog.json`

Frontend type safety:

```bash
make verify.frontend.typecheck.strict
```

One-command gate:

```bash
make verify.frontend.suggested_action.all
```
