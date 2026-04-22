# Cross-Scene Summary Surface Screen V1

## Problem

`ProjectManagementDashboardView.vue` is used as a container for multiple
project-adjacent scenes, including:

- `project.dashboard`
- `cost.tracking`
- `payment`

The current frontend still builds `summaryRows` by branching on
`currentSceneKey`, which means the summary surface is not yet owned by backend
scene contracts.

## Current Scene Entry Mapping

Frontend currently maps scene keys to intents:

- `project.dashboard` -> `project.dashboard.enter`
- `cost.tracking` -> `cost.tracking.enter`
- `payment` -> `payment.enter`

So the same page container is consuming three different scene entry payloads.

## Current Backend Supply By Scene

### `project.dashboard`

Entry handler:

- `addons/smart_construction_core/handlers/project_dashboard_enter.py`

Current backend supply already includes:

- `project_context`
- `summary`
- `state_explain`
- `metrics_explain`
- `flow_map`
- `completion`

Observation:

- this scene already has the richest scene-ready semantic envelope
- what is still missing is one direct `summary_rows` surface so frontend does
  not compose the summary card itself

### `cost.tracking`

Entry handler:

- `addons/smart_construction_core/handlers/cost_tracking_enter.py`

Entry orchestrator:

- `addons/smart_core/orchestration/cost_tracking_contract_orchestrator.py`

Service facts:

- `addons/smart_construction_core/services/cost_tracking_service.py`
  already builds a `summary` object including fields such as:
  - `move_count`
  - `draft_move_count`
  - `cost_total_amount`
  - `draft_cost_amount`
  - `currency_name`

Observation:

- cost tracking already has a scene-specific summary fact surface
- the frontend branch is re-mapping this summary into display rows locally

### `payment`

Entry handler:

- `addons/smart_construction_core/handlers/payment_slice_enter.py`

Entry orchestrator:

- `addons/smart_core/orchestration/payment_slice_contract_orchestrator.py`

Service facts:

- `addons/smart_construction_core/services/payment_slice_service.py`
  already builds a `summary` object including fields such as:
  - `payment_record_count`
  - `payment_total_amount`
  - `draft_payment_amount`
  - `executed_payment_record_count`
  - `executed_payment_amount`
  - `currency_name`

Observation:

- payment already has a scene-specific summary fact surface
- the frontend branch is again reassembling display rows locally

## Classification

### This is not a transport problem

All three scene identities already reach their own backend entry handlers.

So the missing piece is not:

- scene identity transport

### This is not primarily a business-fact absence problem

All three scene services already emit underlying summary facts.

So the missing piece is not:

- inability to know the underlying numbers or labels

### This is a scene-orchestration projection gap

What is missing is one consistent scene-owned display projection, for example:

- `summary_rows`

where each scene can emit rows in the format needed by the container.

Required owner:

- `scene-orchestration layer`

Meaning:

- each scene keeps its own business facts
- each scene also becomes responsible for projecting those facts into a uniform
  summary-row contract for the shared container

## Recommended Contract Shape

Add one optional additive field to scene entry payloads:

```json
{
  "summary_rows": [
    {
      "key": "stage_label",
      "label": "项目执行阶段",
      "value": "在建",
      "copy": "主流程位置"
    }
  ]
}
```

Required row fields:

- `key`
- `label`
- `value`

Optional row fields:

- `copy`
- `unit`
- `tone`

## Recommended Implementation Path

### Step 1: project dashboard

Add `summary_rows` in project dashboard service/handler based on existing:

- `project_context`
- `summary`
- `metrics_explain`

This is the highest-value scene because it currently contains the heaviest
semantic assembly in frontend.

### Step 2: cost tracking

Add `summary_rows` projection in cost tracking entry supply using the existing
cost tracking summary facts.

### Step 3: payment

Add `summary_rows` projection in payment entry supply using the existing
payment summary facts.

### Step 4: frontend container

Update `ProjectManagementDashboardView.vue` to:

- consume `entry.summary_rows` when present
- remove scene-key summary branches once all three scenes provide the field

## Final Decision

Cross-scene summary removal should be implemented through one unified additive
contract surface:

- `summary_rows`

The backend already owns the raw summary facts for `project.dashboard`,
`cost.tracking`, and `payment`.

The remaining gap is to let each scene project those facts into one shared
summary-row surface so the frontend container can stop assembling them locally.
