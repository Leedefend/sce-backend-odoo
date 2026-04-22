# Route Convergence Compatibility Bridge Screen v1

## Goal

Classify the bounded compatibility-route candidates collected by the scan into:

- true product-entry dependencies
- acceptable compatibility-shell internal bridges
- candidates that would require backend semantic supply before further
  frontend convergence is safe

This screen does not implement removal. It decides the next legal batch.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance screen
- Module: route convergence compatibility bridge
- Module Ownership: frontend route convergence proof boundary
- Kernel or Scenario: scenario
- Reason: the candidate set is frozen, so the next step is to classify the
  remaining route-form consumers before any bounded convergence implementation

## Screen Basis

This screen uses only:

- `route_convergence_compat_bridge_scan_v1.md`
- current bounded code state of the scanned frontend consumers

## Classification Result

### 1. Route registration surface is not the immediate implementation batch

Observed state:

- `/m`, `/a`, `/r`, `/f` are still registered in the router
- those route forms still serve as compatibility and diagnostic surfaces for
  already-entered flows

Classification:

- this set is a governance target, not the immediate implementation target
- removing or deprecating route registration directly would be premature before
  the remaining consumers are fully classified

Decision:

- do not open a router-registration removal batch yet

### 2. `ModelListPage` is a true product-entry dependency candidate

Observed state:

- `ModelListPage.vue` still redirects legacy list entry to `name: 'action'`

Classification:

- this is entry-adjacent behavior rather than an internal compatibility-shell
  mechanic
- it is therefore a valid next implementation candidate in a frontend
  convergence batch

Decision:

- keep `ModelListPage` in the next bounded implementation scope

### 3. `MenuView` fallback branches are still entry-adjacent but remain frontend-solvable

Observed state:

- `MenuView.vue` still falls back to `name: 'action'` when no scene location can
  be derived
- the same file already attempts scene-first resolution before using the action
  fallback

Classification:

- these branches are still close to product-entry behavior
- however, inside the current bounded state, they are still frontend-solvable
  because they already operate on scene-registry and carried route semantics

Decision:

- keep `MenuView` in the next bounded implementation scope
- treat it as a frontend bridge-convergence batch, not a backend semantic-supply
  batch

### 4. `ActionView` / `ContractFormPage` / `RecordView` / `ViewRelationalRenderer` are acceptable internal bridges for now

Observed state:

- these consumers use `name: 'model-form'`, `name: 'record'`, or bounded
  `name: 'action'` fallback while already inside compatibility-aware contract
  views

Classification:

- these are not the first product-entry authority surfaces anymore
- they currently behave as compatibility-shell internal route mechanics
- shrinking them further is lower priority than clearing entry-adjacent
  candidates

Decision:

- do not include them in the next immediate implementation batch
- leave them for a later convergence line after entry-adjacent routes are
  reduced

### 5. No backend semantic-supply batch is required for the immediate next step

Observed state:

- the remaining entry-adjacent candidates (`ModelListPage`, `MenuView`) already
  operate with current scene registry, carried query context, and scene-first
  normalization helpers

Classification:

- the immediate next reduction does not require new backend business facts
- it also does not require new scene orchestration semantics from the backend

Decision:

- the next legal batch remains frontend-only and bounded

## Final Decision

The next eligible low-risk batch is:

- a frontend-only bounded implementation line targeting `ModelListPage` and the
  entry-adjacent `MenuView` action fallbacks

The next batch must not:

- remove router route registrations
- touch internal bridge mechanics in `ActionView`, `ContractFormPage`,
  `RecordView`, or `ViewRelationalRenderer`
- claim full route-shape convergence after only the next bounded cleanup

## Frozen Next-Step Direction

Open the next bounded frontend implementation batch to reduce:

1. `ModelListPage` legacy redirect to `name: 'action'`
2. `MenuView` entry-adjacent fallback branches that still resolve to
   `name: 'action'` after scene-first attempts
