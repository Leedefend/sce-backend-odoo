# Product v0.2 Planning Skeleton

## Goal
- Expand beyond v0.1 first-pilot execution while preserving the stability and explainability proven in v0.1.

## v0.2 Primary Objectives
- introduce a controlled multi-task execution model
- introduce a controlled multi-role product model
- add one second business chain beyond project execution
- keep all expansion guard-first and contract-first

## Frozen Inputs From v0.1
- task truth remains `project.task.sc_state`
- v0.1 mainline must remain stable and available as compat mode
- no hidden heuristic logic may replace explicit semantic states

## Proposed v0.2 Boundary
- In scope:
  - multi-task design under an explicit queue model
  - multi-role acting/handoff model
  - payment as the second business chain
  - standardized pilot feedback governance
- Out of scope:
  - broad permission-system redesign
  - full parallel execution orchestration
  - cross-domain mega-dashboard redesign
  - uncontrolled surface expansion

## Proposed Workstreams
- workstream 1:
  - execution semantics
- workstream 2:
  - role and handoff semantics
- workstream 3:
  - payment-chain product path
- workstream 4:
  - pilot feedback and freeze governance

## Proposed Acceptance Signals
- multi-task model can be explained without ambiguity
- multi-role action ownership is explicit in product surfaces
- second business chain has one clear end-to-end operator story
- v0.1 compat path remains intact

## Risks
- P0:
  - v0.2 expansion accidentally breaks v0.1 stable path
- P1:
  - multi-task semantics become too complex before a simple queue model is proven
- P1:
  - roles are modeled as ACL-only rather than product behavior
- P2:
  - second chain selection drifts into broad ERP coverage instead of a focused story

## Recommended First Phase For v0.2
- v0.2-A:
  - semantic freeze for queue model + acting role + payment story
- v0.2-B:
  - minimal runtime implementation with compat guards
- v0.2-C:
  - trial-ready cross-role review and freeze
