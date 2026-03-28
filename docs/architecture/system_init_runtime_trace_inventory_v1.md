# System Init Runtime Trace Inventory v1

状态：Implementation Prep Trace  
适用对象：第一条 `system.init` 收敛代码批次

---

## 1. Purpose

Trace the current `system.init` runtime path and identify:

- handoff points
- base facts boundary
- scene assembly boundary
- fallback zones
- first code slice boundary

---

## 2. Handoff Points

### Handoff Points

Current `system.init` path is anchored in:

- `addons/smart_core/handlers/system_init.py`

From the handler, the dominant handoff chain visibly includes:

- identity/user bootstrap
  - `SystemInitIdentityPayload`
- nav/input normalization
  - `SystemInitNavRequestBuilder`
- payload mode shaping
  - `SystemInitPayloadBuilder`
- runtime context packaging
  - `SystemInitRuntimeContext`
  - `SystemInitSurfaceContext`
- surface/meta assembly
  - `SystemInitSurfaceBuilder`
  - `SystemInitResponseMetaBuilder`
- scene/runtime bridges
  - `SceneRuntimeOrchestrator`
  - `build_scene_ready_contract_v1`
  - `build_scene_nav_contract`
  - provider-based scene loading helpers

---

## 3. Base Facts Boundary

### Base Facts Boundary

The most likely end of pure base facts is before the flow begins assembling scene-ready payload structures.

Practical boundary candidates:

- user identity and group facts
- nav request input normalization
- raw surface/runtime context preparation
- preload and response meta staging before scene-ready shaping

This means the first code batch should treat these as platform facts, not scene-owned output.

---

## 4. Scene Assembly Boundary

### Scene Assembly Boundary

The scene-assembly zone begins where `system.init` starts to:

- resolve scene channels
- load or merge scene contract data
- call scene runtime/orchestrator utilities
- construct `scene_ready_contract_v1`
- attach scene governance and nav contract payloads

This is the exact authority boundary the first implementation slice must clarify.

---

## 5. Fallback Zones

### Fallback Zones

Current fallback or mixed-authority risk appears around:

- provider-based scene loading and DB-or-fallback merges
- compatibility-era surface shaping in `system_init.py`
- startup payload minimization paths inside `SystemInitPayloadBuilder`
- any place where handler-level code both owns facts and directly shapes scene-ready payloads

These zones are not automatically wrong, but they are the places most likely to blur runtime ownership.

---

## 6. First Code Slice Boundary

### First Code Slice Boundary

The first code slice should stay narrow:

- in scope:
  - trace and isolate `system.init` handoff ownership
  - reduce mixed authority between handler-level fact collection and scene-ready assembly
  - make scene-ready construction responsibility more explicit
- out of scope:
  - broad package rename
  - industry-module relocation
  - unrelated `load_contract` cleanup

---

## 7. Recommended Next Implementation Batch

Open the next execution batch as:

- `system_init_handoff_authority_cleanup`

Its success condition should be:

- handler remains responsible for startup facts and orchestration entry
- scene/runtime-specific assembly authority is made more explicit and easier to verify
- existing `system.init` verification gates continue to pass
