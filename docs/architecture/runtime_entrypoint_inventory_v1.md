# Runtime Entrypoint Inventory v1

状态：Execution Prep Inventory  
适用对象：runtime mainline 收敛、代表切片选择、验证门禁设计

---

## 1. Purpose

This inventory identifies current runtime entrypoints and classifies them by convergence status:

- `mainline`
- `transitional`
- `violating`

Classification is based on one question:

Does the flow clearly support the target chain

```text
intent
  -> UI Base Contract
  -> Scene Orchestrator
  -> Scene-ready Contract
  -> frontend
```

---

## 2. mainline

These entrypoints already align, or are clearly oriented, toward the target runtime chain.

### 2.1 `system.init`

- location:
  - `addons/smart_core/handlers/system_init.py`
- current status:
  - mainline-oriented
- reason:
  - owns runtime bootstrap
  - already participates in system-init layering and runtime context governance
  - is the strongest candidate for proving orchestrated startup output

### 2.2 `load_contract`

- location:
  - `addons/smart_core/handlers/load_contract.py`
- current status:
  - mainline-oriented
- reason:
  - is already treated as the primary contract path
  - is explicitly documented as the preferred path over `load_view`

### 2.3 `smart_scene.core.scene_engine`

- location:
  - `addons/smart_scene/core/scene_engine.py`
- current status:
  - mainline-oriented
- reason:
  - is the clearest scene-ready assembly anchor
  - already encodes resolver -> mapper -> layout -> contract chain

---

## 3. transitional

These entrypoints still participate in runtime behavior, but their ownership or output authority remains transitional.

### 3.1 `ui.contract`

- location:
  - `addons/smart_core/handlers/ui_contract.py`
  - `addons/smart_core/handlers/enhanced_ui_contract.py`
- current status:
  - transitional
- reason:
  - still sits close to contract-facing output authority
  - current handler already warns that native `ui.contract` delivery is disabled in favor of scene-ready output

### 3.2 `load_view`

- location:
  - `addons/smart_core/handlers/load_view.py`
- current status:
  - transitional
- reason:
  - explicitly acts as a compatibility proxy to `load_contract`
  - should remain compatibility-only, not a long-term runtime backbone

### 3.3 `frontend_api`

- location:
  - `addons/smart_core/controllers/frontend_api.py`
- current status:
  - transitional
- reason:
  - it is business-facing and runtime-relevant
  - but it still needs classification by which paths terminate at base facts versus scene-ready structures

### 3.4 dashboard/workspace orchestration bridges

- representative locations:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - `addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py`
- current status:
  - transitional
- reason:
  - these bridges already call into `smart_scene`
  - but still carry transition-era compatibility and fallback behavior near core runtime assembly

---

## 4. violating

No confirmed violating entrypoint is declared in this inventory yet.

That is intentional.

A path should only be labeled `violating` when one of the following is demonstrated:

- bypasses `smart_scene` while still claiming page-ready authority
- returns frontend-consumed structure that is not scene-ready governed
- pushes scene-assembly responsibility into frontend or industry logic

Current conclusion:

- suspected weak points exist
- but they still need targeted code-path evidence before being labeled violating

---

## 5. Best Representative Slice Candidates

### 5.1 `system.init`

- strongest governance surface
- already has verify coverage
- good candidate for startup-oriented runtime proof

### 5.2 `load_contract`

- strongest contract-path convergence candidate
- directly relevant to “primary path vs compatibility path” cleanup

### 5.3 project/workspace dashboard orchestration

- highest value for proving that `smart_scene` is the mandatory assembly layer
- likely the best slice for demonstrating scene-ready authority

---

## 6. Recommendation

Open the next task as `representative_slice_selection` and choose exactly one of:

1. `system.init`
2. `load_contract`
3. project/workspace dashboard orchestration

Selection rule:

- prefer the slice with existing verify coverage and the lowest fallback ambiguity
