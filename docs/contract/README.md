# Contract Catalog

Phase 11.1 introduces two machine-readable contract catalogs so the platform contract is visible and auditable without reading handlers manually.

## Outputs

- `docs/contract/exports/intent_catalog.json`
- `docs/contract/exports/scene_catalog.json`

## Generate

```bash
make contract.catalog.export
```

## Verify

```bash
make verify.contract.catalog
make verify.scene.contract.shape
make verify.contract.evidence
```

## Intent Catalog

`intent_catalog.json` is built from:

- handler declarations (`INTENT_TYPE`, `ALIASES`, idempotency window flag)
- test references in backend tests
- contract snapshot cases (`docs/contract/cases.yml`)
- snapshot payloads (`docs/contract/snapshots/*.json`)

Each intent entry includes:

- owner module/class
- aliases
- idempotency window signal
- request schema hints from `intent_params`
- response data schema hints from snapshot payloads
- observed `reason_code` set

When an intent has no explicit snapshot case, catalog export now provides one inferred example:

- `examples[0].inferred = true`
- source: `handler_params_scan` (from `params.get(...)`/`params[...]` usage)

## Scene Catalog

`scene_catalog.json` is built from:

- scene contract export file: `docs/contract/exports/scenes/stable/LATEST.json`

Each scene entry includes normalized sections:

- `identity`
- `access`
- `layout`
- `components`
- `target`
- `renderability`

This keeps scene orchestration structure visible for review and drift detection.

Catalog root now also includes renderability summary:

- `renderability.renderable_scene_count`
- `renderability.interaction_ready_scene_count`
- `renderability.renderable_ratio`
- `renderability.interaction_ready_ratio`

## Scene Shape Guard

`verify.scene.contract.shape` enforces that each scene entry contains five normalized sections:

- `identity`
- `access`
- `layout`
- `components`
- `target`

It writes a machine-readable report to:

- `artifacts/scene_contract_shape_guard.json`

## Phase 11.1 Evidence

`verify.contract.preflight` now emits a merged evidence summary:

- `artifacts/contract/phase11_1_contract_evidence.json`
- `artifacts/contract/phase11_1_contract_evidence.md`

Standalone export:

```bash
make contract.evidence.export
```
