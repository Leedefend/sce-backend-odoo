# Product Scene Orchestration Native Template v1

## Purpose
- Provide one reusable template for future business-chain expansion.
- Force every slice to start from native carrier reuse instead of custom project-scoped implementation.

## Template

### 1. Native Carrier
- `native_model`
- `native_views`
- `native_actions`
- `native_state_source`

### 2. Entry Anchor
- `entry_scene_key`
- `entry_intent`
- `required_context`
- `role_scope`

Rule:
- entry must open or deep-link to an existing native scene or an orchestration shell that clearly delegates to it.

### 3. Orchestration Layer
- allowed:
  - entry summary
  - blocker explanation
  - next action hint
  - project-to-native context forwarding
- forbidden:
  - new business truth model
  - new shadow lifecycle
  - duplicate list/detail runtime blocks for native records unless used only as lightweight summary

### 4. Frontend Consumption
- frontend consumes:
  - scene contract
  - suggested actions
  - blocker reasons
- frontend must not infer:
  - native model semantics
  - business state transitions
  - record creation policy

### 5. Verify Chain
- required checks:
  - native mapping declared
  - no `project.<domain>.*` shadow intent family introduced
  - entry target points to native scene family
  - frontend only consumes declared orchestration contract

## Standard Decision Questions
- What is the native system of record?
- Which native scene already exists?
- Why is orchestration needed?
- What will explicitly remain native?
- What custom implementation is forbidden in this slice?

## Example Posture
- Good:
  - `project.execution.next_actions` links to `finance.payment_requests` with `project_id`
- Bad:
  - create `project.payment.enter`, `project.payment.block.fetch`, `project.payment.ensure_single`
  - recreate finance list/detail/product state inside project runtime blocks
