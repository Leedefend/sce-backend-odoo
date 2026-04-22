# Project Dashboard Summary Contract Screen V1

## Problem

`ProjectManagementDashboardView.vue` still contains two kinds of frontend
semantic work that should not remain in the consumer:

- scene-key based summary assembly
- business vocabulary aliasing such as `execution_stage_label || stage_label`

Before implementing the next batch, we need to classify which missing pieces
belong to:

- business-fact supply
- scene-orchestration supply

## Current Backend Fact Chain

### `project.dashboard.enter` already supplies structured dashboard semantics

`addons/smart_construction_core/handlers/project_dashboard_enter.py` currently
attaches all of the following into the entry payload:

- `project_context`
- `state_explain`
- `metrics_explain`
- `flow_map`
- `completion`
- `facts`
- `fact_metrics`

This means the dashboard is not operating on a raw record response. It already
has a scene-ready payload shape.

### `project_context` already carries canonical business facts, plus aliases

`addons/smart_construction_core/services/project_context_contract.py` builds:

- canonical fields:
  - `execution_stage`
  - `execution_stage_label`
  - `milestone`
  - `milestone_label`
  - `project_condition`
- compatibility aliases:
  - `stage`
  - `stage_label`
  - `status`

Meaning:

- backend has already decided that `execution_stage*` and
  `project_condition` are the real business-facing carriers
- `stage*` and `status` still exist as compatibility aliases

### `state_explain` also carries canonical fields plus aliases

`addons/smart_construction_core/services/project_state_explain_service.py`
returns:

- canonical fields:
  - `execution_stage_label`
  - `execution_stage_explain`
  - `project_condition_explain`
- compatibility aliases:
  - `stage_label`
  - `stage_explain`
  - `status_explain`

`addons/smart_construction_core/services/project_dashboard_service.py` then
continues that compatibility pattern when building the dashboard payload.

Meaning:

- backend already owns the semantic source
- but the payload still exposes two parallel vocabularies

## Current Frontend Overreach

### Overreach 1: frontend still assembles scene-specific summary rows

`ProjectManagementDashboardView.vue` builds `summaryRows` by branching on:

- `currentSceneKey === "cost.tracking"`
- `currentSceneKey === "payment"`
- dashboard default

Each branch chooses:

- labels
- field mappings
- display formatting
- explanatory copy

Judgment:

- this is not a business-fact problem
- this is a missing scene-orchestration summary surface

Required owner:

- `scene-orchestration layer`

Required semantic supply:

- scene-ready summary row descriptors, for example:
  - `summary_rows[]`
  - each row containing `key / label / value / unit / explain`

### Overreach 2: frontend still chooses between canonical fields and aliases

Current frontend chains include:

- `execution_stage_label || stage_label || summary.stage_name`
- `project_condition || status`
- `execution_stage_explain || stage_explain`
- `project_condition_explain || status_explain`

Judgment:

- this is primarily a contract-clarity problem
- the frontend should not decide which vocabulary wins

Required owner:

- primary: `business-fact layer` for canonical field ownership
- secondary: `scene-orchestration layer` for scene-ready explain text

## Ownership Decision

### Business-fact layer owns canonical project facts

The business-fact layer should be treated as the owner of:

- `execution_stage`
- `execution_stage_label`
- `milestone`
- `milestone_label`
- `project_condition`

These are business truths or direct business-truth labels.

Decision:

- new frontend work must treat these as canonical
- alias fields should be considered compatibility-only and scheduled for
  consumer removal

### Scene-orchestration layer owns dashboard summary organization

The scene-orchestration layer should be treated as the owner of:

- dashboard summary row composition
- dashboard headline/subtitle semantic copy
- block captions when they carry scene meaning
- metric explanation rows

These are not raw business facts; they are scene-ready organization for one
specific dashboard experience.

Decision:

- frontend must stop hardcoding summary row sets by `currentSceneKey`
- backend should emit one explicit summary surface for the dashboard to render

## Gap Classification

### Gap A: duplicate business vocabulary still leaks to frontend

Observed in backend:

- `project_context` exposes both `execution_stage*` and `stage*`
- `project_context` exposes both `project_condition` and `status`
- `state_explain` exposes both `execution_stage_explain` and `stage_explain`
- `state_explain` exposes both `project_condition_explain` and `status_explain`

Classification:

- `business-fact layer cleanup`

Reason:

- canonical naming already exists
- the missing piece is stronger contract discipline, not new frontend logic

Recommended next step:

- document canonical dashboard/project-context field set
- make frontend consume canonical names first with a bounded alias deprecation
  plan

### Gap B: dashboard summary surface is missing

Observed in frontend:

- summary row layout is still handwritten in Vue

Classification:

- `scene-orchestration supply gap`

Reason:

- the scene already exposes `flow_map`, `metrics_explain`, `completion`
- but it does not expose a direct summary surface matching the rendered summary
  card

Recommended next step:

- add a backend-provided summary surface such as `summary_rows`
- migrate the dashboard to render that surface directly

### Gap C: fallback semantic copy is still split across frontend and backend

Observed:

- backend already provides explain surfaces
- frontend still adds scene/business fallback wording such as
  `查看当前项目阶段与里程碑`

Classification:

- `scene-orchestration supply gap`

Reason:

- meaningful dashboard copy should travel with the scene contract when it
  carries product semantics

Recommended next step:

- move scene-meaningful dashboard copy into backend scene payload
- keep only neutral technical placeholders in frontend

## Recommended Implementation Order

1. declare canonical dashboard/project-context fields:
   - `execution_stage*`
   - `milestone*`
   - `project_condition*`
2. add backend dashboard summary surface for rendered summary rows
3. switch frontend dashboard to canonical fields plus backend summary surface
4. remove frontend alias chains and `currentSceneKey` summary branching

## Final Decision

The dashboard problem is not one single bug.

It is two different backend supply gaps:

- canonical business vocabulary still coexists with compatibility aliases
- scene-ready summary organization is still missing

So the next implementation should be layered:

- first tighten canonical field ownership
- then add a backend summary surface
- then delete the frontend scene-key summary assembler
