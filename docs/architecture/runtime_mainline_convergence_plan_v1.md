# Runtime Mainline Convergence Plan v1

状态：Planning Baseline  
适用对象：平台内核重构、scene runtime 收敛、验证门禁设计

---

## 1. Objective

Make the following chain the dominant backend runtime path:

```text
intent
  -> UI Base Contract
  -> Scene Orchestrator
  -> Scene-ready Contract
  -> frontend
```

This plan does not start with module renaming. It starts with runtime normalization.

---

## 2. Current Gaps

### 2.1 Mixed output authority

- some flows still expose base-contract shaped output too directly
- not every scene is consistently normalized through `smart_scene`

### 2.2 Transitional compatibility paths

- historical fallback paths remain near `smart_core` entrypoints
- some compatibility branches blur whether `smart_core` or `smart_scene` owns final page structure

### 2.3 Verification is not yet runtime-mainline specific enough

- existing verify assets cover pieces of the chain
- but not every batch is explicitly gated by “did this flow really pass through scene orchestrator”

---

## 3. Target Runtime Chain

### 3.1 Target authority split

- `smart_core`
  - intent entry
  - base facts
  - permission / audit / transaction / bootstrap
- `smart_scene`
  - scene identity
  - layout assembly
  - block composition
  - scene-ready contract output
- frontend
  - render and interaction only

### 3.2 Non-goals

- no package rename in this batch
- no broad industry-module relocation in this batch
- no schema or ACL work in this batch

---

## 4. Phase 1

### 4.1 Audit runtime entrypoints

Identify which current entrypoints still:

- bypass `smart_scene`
- expose base-contract output directly
- rely on fallback scene assembly

Expected output:

- entrypoint inventory
- classification by mainline / transitional / violating

### 4.2 Select one representative slice

Choose one stable representative flow, preferably a low-risk scene that already has verify coverage.

Expected output:

- one named slice for first code convergence
- one before/after runtime trace

---

## 5. Phase 2

### 5.1 Converge the representative slice

Refactor one chosen flow so that:

- `smart_core` stops short at base facts
- `smart_scene` becomes the mandatory scene-ready assembly layer
- frontend consumes the normalized scene-ready output

### 5.2 Preserve fallback only as explicit transition policy

If fallback must remain temporarily:

- document it
- gate it
- assign an exit condition

---

## 6. Phase 3

### 6.1 Expand to additional scene families

Suggested order:

1. dashboard/cockpit representative slice
2. list/form representative slice
3. search/action representative slice

### 6.2 Normalize verification around the chain

Each migrated slice should answer:

- did intent routing enter through the correct core entrypoint
- did scene orchestration occur
- was scene-ready output produced
- did frontend consume that output without structural compensation

---

## 7. Verification Gates

The first implementation batch should not start without explicit gates for:

- runtime chain path assertion
- scene-ready contract assertion
- no direct frontend dependence on base-contract-only structure
- no industry logic pushed into `smart_core`

If existing verify commands already cover part of this, reuse them. Add missing gates only where evidence is weak.

---

## 8. First Batch Recommendation

Open the next execution batch as:

1. `runtime_entrypoint_inventory`
2. `representative_slice_selection`
3. `runtime_chain_verify_gap_audit`

Only after these three are complete should the first narrow code refactor slice begin.
