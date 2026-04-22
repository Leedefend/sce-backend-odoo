# Semantic Route Repair J v1

## Goal

Repair `verify.portal.semantic_route` to validate the current scene registry
runtime semantics rather than the removed legacy `scenesCore` module.

## Scope

- `scripts/verify/fe_semantic_route_smoke.js`

## Fixed Architecture Declaration

- Layer Target: Verification surface repair
- Module: semantic route verifier
- Module Ownership: scripts/verify
- Kernel or Scenario: scenario
- Reason: live verification was blocked by a stale verifier importing a removed
  frontend config module

## Implemented Changes

- semantic-route smoke now validates the current `sceneRegistry.ts` runtime
  source instead of importing the removed `config/scenesCore.js`
- the verifier now checks the active semantic-route guarantees that matter for
  the current boundary:
  - native `/a` `/f` `/r` route prefixes are normalized back to `/s/:sceneKey`
  - `my_work.workspace` keeps its explicit `/my-work` route override
  - unified home scene keys and routes remain frozen in the runtime source

## Result

- `verify.portal.semantic_route` is executable again against the current repo
  shape
- the verification surface now follows the live scene registry runtime instead
  of an obsolete static scene list
