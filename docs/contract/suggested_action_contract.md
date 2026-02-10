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
