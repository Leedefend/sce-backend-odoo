# Scene Orchestration Carrier Spec v1

## Goal
- Define a stable carrier for product scene assembly under the five-layer architecture.

## Responsibilities

### Domain Service
- owns:
  - model resolution
  - business truth read model
  - business block provider output
  - guard and consistency results
- forbidden:
  - scene title
  - runtime fetch hint assembly
  - frontend fallback copy structure

### Scene Orchestration Carrier
- owns:
  - scene entry contract
  - runtime block envelope
  - block list / suggested action / runtime fetch hints
  - scene-level copy such as `scene_label` and `state_fallback_text`
- forbidden:
  - creating new business truth
  - bypassing native/business carriers

### Frontend
- owns:
  - generic contract rendering
  - refresh / action / feedback interaction
- forbidden:
  - branching on concrete `project.*.enter`
  - deriving product structure from scene names

## Pilot
- `execution` is the first carrier pilot
- `ProjectExecutionService` becomes truth-facing provider
- `ProjectExecutionSceneOrchestrator` becomes scene assembly carrier

## Entry Shape
- `scene_key`
- `scene_label`
- `state_fallback_text`
- `title`
- `summary`
- `blocks`
- `suggested_action`
- `runtime_fetch_hints`
