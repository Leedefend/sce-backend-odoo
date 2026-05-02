# Unified Semantic Page Contract Lite

Date: 2026-05-01
Status: Direction correction / implementation baseline

## Core Principle

Contract deep, runtime thin, semantics strong, implementation light.

This track supersedes the runtime-heavy v2+ direction for the current stage. The v2+ exploratory assets remain useful as audit material, but the active delivery path is now **Unified Semantic Page Contract Lite**.

## Goal

Solve the current real problem:

- unify Odoo pages across Web, UniApp mini-program, and Harmony H5
- support complex ERP views: form, tree, x2many, popup, tab, gantt, workflow
- keep business semantics backend-owned
- support partial updates for onchange and x2many interaction
- enable industry orchestration without frontend business rules

## Architecture

```text
Odoo Native Layer
    ↓
Semantic Adapter Layer
    ↓
Unified Semantic Page Contract Lite
    ↓
Frontend Contract Renderer
```

The moat is the Odoo Semantic Adapter, not a runtime kernel.

## Top-Level Shape

```json
{
  "pageInfo": {},
  "layoutContract": {},
  "statusContract": {},
  "actionContract": {},
  "dataContract": {},
  "meta": {}
}
```

No `runtimeContract` in the active Lite protocol.

## PageInfo

Only page identity:

```json
{
  "pageId": "project.form",
  "sceneKey": "project.intake",
  "model": "project.project",
  "viewType": "form",
  "clientType": "web_pc",
  "contractVersion": "2.0.0"
}
```

## LayoutContract

Only structure:

```json
{
  "layoutType": "form",
  "containerList": []
}
```

No component registry and no capability protocol in Phase 1.

## StatusContract

Backend-owned status only:

```json
{
  "widgetStatus": [],
  "buttonStatus": []
}
```

The frontend must not infer visible, readonly, required, disabled, or action availability.

## ActionContract

Event declaration only:

```json
{
  "actionRuleList": []
}
```

The frontend dispatches `actionId`. The backend evaluates all business semantics and returns a patch.

Forbidden in ActionContract:

- chain action execution
- condition branches
- loops
- workflow VM
- JSON logic
- frontend business rules

## DataContract

Keep it simple:

```json
{
  "mainData": {},
  "relationData": {},
  "dictData": {}
}
```

No realtime datasource, streaming, consistency, subscription, or cache policy in Phase 1.

## Patch Protocol

```json
{
  "updateType": "partial",
  "statusPatch": {},
  "dataPatch": {},
  "layoutPatch": {}
}
```

Allowed patch operations:

- `replace`
- `merge`

## Phase Plan

### Phase 1

- Lite contract
- Odoo Semantic Adapter
- thin patch merge
- multi-terminal renderer

### Phase 2

- component registry
- selector status
- dependency graph

### Phase 3

- realtime
- collaboration
- AI orchestration

## Current Decision

Stop expanding runtime kernel, scheduler, hydration, virtualization, reactive DAG, CRDT, streaming runtime, and AI orchestration in the current stage.

Build the Odoo Semantic Runtime Layer first.
