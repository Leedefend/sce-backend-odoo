# Phase 16-E: v0.1 Stability Baseline

## Objective
- stabilize the new baseline before reopening any business expansion
- include the project-creation mainline in the same frozen verification chain

## Delivered
- defined a stable split between:
  - navigation/native-form scene: `projects.intake`
  - business creation truth: `project.initiation.enter`
- extracted shared frontend constants for project creation identifiers
- added `product_project_creation_mainline_guard`
- added aggregate gate:
  - `make verify.product.v0_1_stability_baseline`

## Scope Rule
- this batch does not expand business capability
- this batch only freezes the current v0.1 mainline under the latest architecture constraints

## Reopen Condition
- new business slice may be considered only after:
  - `verify.product.v0_1_stability_baseline` passes
  - architecture guards remain green
  - native alignment policy remains green
