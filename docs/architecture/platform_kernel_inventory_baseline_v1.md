# Platform Kernel Inventory Baseline v1

状态：Refactor Prep Inventory  
适用对象：平台内核重构规划、任务拆解、边界审计

---

## 1. Purpose

This document turns the architecture baseline into a concrete inventory of current platform-kernel assets.

It is intentionally compact. Its job is not to restate every file in the repo, but to identify:

- current `smart_core` kernel assets
- current `smart_scene` orchestration assets
- overlap risk between platform and industry responsibilities
- first extraction target candidates for backend kernel refactor

---

## 2. smart_core

### 2.1 Current role

`smart_core` is the current platform-kernel anchor. It already carries the majority of cross-domain runtime responsibilities:

- intent entrypoints
- contract handlers
- frontend API and system bootstrap
- app config engine
- registry and delivery-oriented runtime support

### 2.2 Representative assets

- controllers
  - `controllers/intent_dispatcher.py`
  - `controllers/enhanced_intent_dispatcher.py`
  - `controllers/frontend_api.py`
- handlers
  - `handlers/system_init.py`
  - `handlers/ui_contract.py`
  - `handlers/load_contract.py`
  - `handlers/load_metadata.py`
  - `handlers/load_view.py`
- app config engine
  - `app_config_engine/services/contract_service.py`
  - `app_config_engine/services/assemblers/page_assembler.py`
  - `app_config_engine/services/dispatchers/*`

### 2.3 Current kernel strengths

- already owns platform-facing intent and contract entrypoints
- already has config-driven runtime assembly assets
- already sits at the right side of the platform vs industry boundary

### 2.4 Current kernel risks

- mixed ownership between contract runtime, system bootstrap, and transitional API surfaces
- some historical compatibility paths still sit near core entrypoints
- platform abstractions are present, but not yet fully normalized into a clean kernel package structure

---

## 3. smart_scene

### 3.1 Current role

`smart_scene` is the current scene orchestration runtime. It is the bridge between platform facts and scene-ready output.

### 3.2 Representative assets

- `core/scene_resolver.py`
- `core/structure_mapper.py`
- `core/layout_orchestrator.py`
- `core/capability_injector.py`
- `core/scene_contract_builder.py`
- `core/scene_engine.py`

### 3.3 Current strengths

- already has a minimal scene engine chain
- already encodes the right runtime direction from base facts to scene-ready contract
- already provides a clean place to centralize scene composition instead of pushing structure logic into frontend or domain modules

### 3.4 Current risks

- not all scene outputs are fully normalized through the same runtime path
- some flows still rely on fallback or transitional output paths
- provider and contract-guard coverage is still narrower than the long-term target

---

## 4. overlap risk

The main overlap risk is not “missing architecture”. It is mixed ownership.

### 4.1 overlap risk: platform vs industry

Potential failure mode:

- generic runtime logic leaks into industry modules
- industry semantics leak back into `smart_core`

Current guard:

- `boundary_platform_vs_construction.md`
- five-layer boundary rules
- extension-registration pattern

### 4.2 overlap risk: contract vs scene

Potential failure mode:

- `smart_core` returns page-ready structure directly
- `smart_scene` becomes optional instead of being the scene-ready runtime

Current guard:

- intent-runtime to scene-orchestrator integration plan
- scene engine adoption documents

### 4.3 overlap risk: frontend compensation

Potential failure mode:

- frontend compensates for backend structure gaps
- scene-ready contract loses authority

Current guard:

- frontend contract consumption rules
- native view reuse frontend spec

---

## 5. first extraction target

The backend kernel refactor should not start with renaming. It should start with extraction targets.

### 5.1 first extraction target: runtime mainline

Target:

- make `intent -> base contract -> scene orchestrator -> scene-ready contract` the dominant runtime path

Why first:

- it stabilizes output semantics
- it reduces ambiguity between `smart_core` and `smart_scene`

### 5.2 first extraction target: platform registry and policy surfaces

Target:

- isolate generic registry, provider, and policy-loading responsibilities from transitional business coupling

Why second:

- it reduces hidden platform/industry mixing
- it makes later package reshaping safer

### 5.3 first extraction target: common project kernel candidates

Target:

- identify project/task/stage/milestone/cockpit capabilities that should become reusable common-project assets rather than remaining implicit in industry modules

Why third:

- it creates the missing middle layer between platform kernel and industry package

---

## 6. Immediate Planning Output

Use this inventory to open the next batches in order:

1. `runtime_mainline_convergence`
2. `platform_registry_inventory`
3. `common_project_kernel_candidate_map`

These should remain doc-first or verify-first until a narrow code slice is selected.
