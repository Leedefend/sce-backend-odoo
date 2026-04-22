# Scene Governance Baseline Snapshot v1

## Purpose

This document freezes the current governed scene-governance export set as the
baseline snapshot for later drift and parity guards.

The baseline is not a new source of truth. It is the comparison anchor for:

- export consistency checks
- baseline drift checks
- guard/export parity checks
- release-gate review of scene-governance changes

## Baseline Assets

The following files are frozen as `baseline_v1`:

- `docs/architecture/scene-governance/assets/scene_authority_matrix_baseline_v1.csv`
- `docs/architecture/scene-governance/assets/scene_family_inventory_baseline_v1.csv`
- `docs/architecture/scene-governance/assets/menu_scene_mapping_baseline_v1.csv`
- `docs/architecture/scene-governance/assets/provider_completeness_baseline_v1.csv`
- `docs/architecture/scene-governance/assets/high_priority_family_user_flow_closure_baseline_v1.csv`

## Baseline Scope

This baseline snapshot reflects the stabilized governance perimeter where the
following seven families are already synchronized to `guarded_ready` in the
high-priority family summary:

- `projects`
- `finance_center`
- `tasks`
- `contracts`
- `payment_approval`
- `payment_entry`
- `enterprise_bootstrap`

## Usage Rules

- future export-drift checks must compare current exports against this baseline
- future parity checks must explain any intentional divergence from this baseline
- baseline updates are allowed only through a dedicated baseline-refresh task
- ordinary feature or runtime tasks must not silently rewrite baseline assets
