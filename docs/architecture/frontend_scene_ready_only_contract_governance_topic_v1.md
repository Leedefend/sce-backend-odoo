# Frontend Scene-Ready Only Contract Governance Topic v1

Status: Governance Topic
Scope: frontend contract boundary, backend scene-ready semantic supply

## 1. Topic Purpose

This topic freezes a single system rule for the current convergence round:

- frontend must consume only scene-ready, scene-oriented contract results
- backend must translate native structures and native contracts into scene-ready
  output before anything becomes frontend-visible

This topic exists to end the current mixed mode where frontend partially
consumes scene semantics, partially consumes native structures, and partially
fills semantic gaps on its own.

## 2. Frozen Principle

The only legal frontend input for page rendering is:

`scene-ready contract`

This means:

- native view structure is backend input, not frontend contract
- ui_base_contract is backend input, not frontend contract
- parser/native intermediate semantics are backend internal translation assets,
  not frontend public semantics
- even when backend decides to reuse native structures directly, the delivered
  result must still be emitted as scene-ready semantics

## 3. Layer Decision

### 3.1 Backend Battlefield

This topic is primarily a backend semantic-supply battlefield.

Reason:

- current user-visible gaps are mostly caused by missing or incomplete
  scene-ready semantic supply
- frontend divergence appears when backend does not provide a complete
  scene-ready surface

### 3.2 Backend Sub-Layer Rule

The backend scheduler must explicitly decide one of the following before each
implementation batch:

- `business-fact layer`
- `scene-orchestration layer`

Default for this topic:

- native-to-scene translation belongs to `scene-orchestration layer`
- missing lifecycle/state truth belongs to `business-fact layer`

## 4. Mandatory Consumption Boundary

Frontend must not:

- render directly from native view payloads
- infer field ordering, toolbar ownership, or scene switching from model names
  or local maps
- infer business vocabulary when backend contract does not provide it
- keep private fallback labels or fallback structural rules for missing business
  semantics

Frontend may only:

- render declared scene-ready surfaces
- map scene-ready schema into store
- perform minimal non-business UI derivation that does not change semantics

## 5. Backend Translation Responsibility

Backend must supply complete scene-ready outputs for frontend-visible pages.

Required translation responsibility includes:

- list/form/kanban/workspace/ledger scene-ready surfaces
- action ownership surfaces
- search/filter/group/sort surfaces
- scene switch or sibling navigation surfaces when product requires them
- business terminology that is necessary for correct user-visible rendering
- explicit absence signals when semantics are not yet available

Backend must not:

- expose incomplete native payloads and expect frontend to fill the gap
- leak parser/native internal structures as public frontend contract
- use frontend-specific layout branching as a substitute for missing semantics

## 6. Iteration Strategy

This topic now follows:

`value-first execution with unchanged risk gates`

This means:

- batches are prioritized by user-visible closure value and convergence impact
- low-risk work is not automatically placed ahead of the main contradiction
- contract guard, allowlist, verification, and stop conditions remain mandatory
- each batch must still stay single-objective and architecturally explicit

The primary contradiction for this topic is:

- frontend is not yet a pure scene-ready contract consumer
- backend does not yet fully own native-to-scene translation responsibility

So iteration should prioritize batches that close this contradiction directly,
instead of spending cycles on peripheral safe optimizations first.

## 7. Value-First Workstream

Recommended execution order:

1. Freeze the public frontend boundary:
   define scene-ready as the only legal frontend-visible page contract family
2. Close the highest-value backend translation gaps:
   list/detail/action/switch/ownership semantics that currently force frontend
   guessing
3. Remove frontend local semantic inference:
   local maps, fallback labels, mixed ownership assembly, and native/intermediate
   contract dependency
4. Add gate coverage:
   detect new native/intermediate leakage and frontend semantic overreach

## 8. Closure Criteria

This topic is considered converged only when all of the following are true:

- frontend page rendering consumes scene-ready contract only
- frontend no longer depends on native/intermediate structure semantics
- scene-ready contract families are sufficient for list/form/detail/workspace
  rendering without frontend business guessing
- backend gap cases are reported as contract gaps instead of being hidden by
  frontend fallback logic

## 9. Immediate Next Step

Open a value-first topic control batch that:

- freezes the execution strategy change from low-risk-first to value-first
- identifies the highest-value closure family already visible from current
  evidence
- launches the next implementation-oriented batch directly against that family
  while keeping risk gates intact

## 10. One-Line Rule

Frontend is a scene-ready contract consumer only; any native structure reused by
the product must still be translated by backend into scene-ready semantics
before frontend consumption.
