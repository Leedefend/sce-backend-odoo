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

## Scene Catalog

`scene_catalog.json` is built from:

- scene contract export file: `docs/contract/exports/scenes/stable/LATEST.json`

Each scene entry includes normalized sections:

- `identity`
- `access`
- `layout`
- `components`
- `target`

This keeps scene orchestration structure visible for review and drift detection.

## Scene Shape Guard

`verify.scene.contract.shape` enforces that each scene entry contains five normalized sections:

- `identity`
- `access`
- `layout`
- `components`
- `target`

It writes a machine-readable report to:

- `artifacts/scene_contract_shape_guard.json`
