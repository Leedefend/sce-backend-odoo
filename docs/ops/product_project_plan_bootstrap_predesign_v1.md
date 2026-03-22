# Product Plan Bootstrap Predesign v1

## Scope
- Reserve only
- No full scene delivery in Phase 12-E

## Intent
- `project.plan_bootstrap.enter`

## Purpose
- Provide a contract-safe target for the next product scene after `project.dashboard`
- Let `dashboard -> plan` direction exist before the actual scene is implemented

## Current Contract
- success data:
  - `state`
  - `project_id`
  - `scene_key`
  - `reason_code`
  - `message`
  - `suggested_action`

## Current Status
- `state = planned`
- not used as the primary startup path
- exposed from `next_actions` runtime block only as a reserved direction

## Exit Condition
- Replace this reserve-only intent with a real `project.plan_bootstrap` scene delivery batch
