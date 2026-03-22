# Phase 16-B: Native Alignment & Orchestration Correction

## Objective
- Correct the v0.2 expansion direction so future business slices reuse native Odoo/business carriers instead of building new project-scoped business implementations.

## Delivered
- native mapping for `payment / contract / cost`
- reusable native orchestration template
- current workspace risk scan
- second business-chain re-decision
- executable native alignment guard and Make target
- execution scene orchestration carrier pilot
- five-layer workspace audit and correction baseline

## Core Decisions
- `project.payment.*`, `project.contract.*`, `project.cost.*` are now treated as forbidden shadow scene families
- project side may orchestrate and deep-link, but must not become the finance / contract / cost system of record
- `cost` replaces `payment` as the preferred next chain under the corrected policy
- `ProjectExecutionService` is reduced to truth-facing block provider responsibility
- `ProjectExecutionSceneOrchestrator` is the pilot carrier for entry assembly and runtime block envelope
- frontend must consume scene contract fields such as `scene_key`, `scene_label`, and `state_fallback_text`, not branch on concrete enter intents

## Current Risk Status
- shadow payment draft is removed from the implementation path
- remaining architecture risk is concentrated in older dashboard / plan services that still assemble scene payloads inside domain services
