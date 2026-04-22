# Core Extension Platform-Intent Keys Screen (ITER-2026-04-05-1063)

## Scope

- file: `addons/smart_construction_core/core_extension.py`
- key family: non-financial platform-style intents only (`app.*`, `usage.*`, `telemetry.*`)

## Extracted Keys

- `usage.track`
- `telemetry.track`
- `usage.report`
- `usage.export.csv`
- `app.catalog`
- `app.nav`
- `app.open`

## Ownership Observation

1. these keys are registered by `smart_construction_core.smart_core_register(registry)`.
2. they are loaded through smart_core extension hook execution, not native smart_core handler ownership.
3. semantics are platform/runtime flavored (catalog/nav/open + telemetry/usage), mixed into scenario extension registration surface.

## Boundary Assessment

- classification: **ownership residue present** (non-financial, medium risk).
- impact: boundary clarity and long-term ownership governance, not immediate runtime breakage.

## Next Suggested Batch

- dedicated `screen` batch to map each key to candidate owner layer and migration difficulty;
- then a bounded `implement` batch for non-financial key ownership realignment only (exclude `payment.*` and `settlement.*`).
