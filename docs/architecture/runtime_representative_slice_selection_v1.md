# Runtime Representative Slice Selection v1

状态：Execution Decision  
适用对象：第一条 runtime mainline 收敛代码批次

---

## 1. Candidate Set

Based on the runtime entrypoint inventory, the candidate set is:

1. `system.init`
2. `load_contract`
3. project/workspace dashboard orchestration

---

## 2. Selected Slice

### Selected Slice

`system.init`

---

## 3. Why This Slice

### 3.1 Strongest governance surface

`system.init` already has the clearest architecture and verification trail around runtime bootstrap, layering, and startup payload shape.

### 3.2 Lowest fallback ambiguity

Compared with dashboard/workspace orchestration, `system.init` has fewer scene-specific fallback branches to untangle before proving the runtime-mainline path.

### 3.3 Better first-step leverage

If `system.init` can be proven to stop at base facts and hand structured assembly authority to the correct downstream runtime stages, that gives the next slices a clearer reference model.

---

## 4. Why Not the Others First

### 4.1 Why not `load_contract` first

- high value, but still closer to compatibility-path cleanup
- likely better as the second slice after the startup/runtime authority split is clearer

### 4.2 Why not dashboard/workspace orchestration first

- highest demonstration value
- but also higher fallback ambiguity and more transition-era bridge logic
- better taken after the runtime-mainline authority model is proven once in a simpler governance-heavy slice

---

## 5. Risks

### Risks

- `system.init` may still conceal compatibility-era payload mixing
- verification assets may prove startup shape, but not every internal handoff in the target chain
- proving startup/runtime authority does not automatically solve page-specific scene assembly

---

## 6. Verification Entry Points

### Verification Entry Points

- `make verify.system_init.startup_layer_contract`
- `make verify.system_init.minimal_surface`
- `make verify.system_init.snapshot_equivalence`
- `make verify.system_init.runtime_context.stability`

These should be treated as the initial verification baseline for the first narrow implementation batch.

---

## 7. Next Batch

Open the next implementation-prep task as:

- `system_init_runtime_trace_inventory`

Its objective should be:

- trace current `system.init` handoff points
- identify where base facts end
- identify where scene/runtime assembly begins
- mark any fallback or mixed-authority zones that must be contained in the first code slice
