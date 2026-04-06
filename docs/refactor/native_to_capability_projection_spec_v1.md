# Native To Capability Projection Spec v1

## 1. Purpose

Define a single architecture path to project Odoo native truth surfaces into the
platform capability registry without replacing native facts.

## 2. Layered Model

### 2.1 Native Truth Layer

- Source of truth objects:
  - `ir.ui.menu`
  - `ir.actions.*`
  - `ir.model`
  - `ir.ui.view`
  - ACL and record-rule facts
- Responsibility: declare what exists, not capability governance.

### 2.2 Parse / Resolve Layer

- Resolve native object semantics into normalized technical rows.
- Includes menu/action/model/view resolvers and permission resolver.
- Responsibility: interpretation only, no runtime orchestration ownership.

### 2.3 Capability Registry Layer

- Accept normalized rows via controlled projection.
- Convert to registry schema:
  - `identity`
  - `ownership`
  - `binding`
  - `permission`
  - `release`
  - `lifecycle`
  - `runtime`
  - `audit`
- Responsibility: capability governance and ownership control.

### 2.4 Intent / Contract Runtime Layer

- Execute runtime actions through intent contracts and orchestration.
- Capability points to runtime intents through binding.

### 2.5 Exposure Layer

- App/Nav/Workspace/Frontend consume projections only.
- Must not directly interpret raw native objects.

## 3. Canonical Pipeline

```text
Native Object
  -> Resolver / Parser
  -> Native Normalized Row
  -> Capability Projection Row
  -> Capability Registry Core
  -> Capability -> Intent Binding
  -> Contract / Orchestration Runtime
  -> App / Nav / Workspace / Frontend
```

## 4. Projection Principles

- Projection-in, not copy-rebuild.
- Native facts remain owned by native models.
- Capability registry owns governance semantics only.
- Projection rows must include `source_kind=native_projection`.
- Platform module (`smart_core`) is owner for projected native capabilities.

## 5. Native Capability Families (v1)

- `native_menu_entry`
- `native_window_action`
- `native_server_action` (reserved for next phase)
- `native_report_action` (reserved for next phase)
- `native_model_access` (reserved for next phase)

## 6. Phase Plan

- Phase-1: menu + act_window projection.
- Phase-2: model access projection and permission matrix.
- Phase-3: server action / report / view binding projection.

## 7. Non-Goals

- No replacement of Odoo native object ownership.
- No direct frontend special-case based on model internals.
- No intent key equals capability key hard-coupling.

