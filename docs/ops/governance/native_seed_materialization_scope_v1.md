# Native Seed Materialization Scope v1

## Purpose

Define the minimal install-time seed materialization scope for native business-fact baseline,
without changing runtime business semantics.

## Candidate Scope (Minimal)

1. Enterprise base master-data skeleton (non-financial):
   - company basic carrier facts
   - department minimal hierarchy anchors
   - post dictionary baseline
2. Project-side non-transactional lookup dictionaries:
   - fixed enum-like dictionaries already consumed by native views
3. Seed ownership constraints:
   - no user-specific private facts
   - no runtime transaction records

## Excluded from This Scope

- payment/settlement/accounting transactional data
- ACL/rule structural changes
- frontend bootstrap data
- manifest dependency reordering

## Proposed Future High-Risk Execute Paths (if approved)

- `addons/smart_construction_custom/__manifest__.py`
- `addons/smart_construction_custom/data/**`

## Mandatory Gates for Future Execute Batch

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.test_seed_dependency.guard`
- `make verify.scene.legacy_contract.guard`

## Stop Rules for Future Execute Batch

- Any seed extending into transactional financial domain
- Any ACL/record-rule side-effect in same batch
- Any manifest dependency direction change beyond declared scope

## Decision

- Current batch stays screen-only.
- Next step should be a dedicated high-risk seed execute contract only after explicit approval.
