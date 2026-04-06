# Industry Shadow Bridge Execution Plan v1

## Scope

- objective: govern and dismantle industry-side pseudo-platform bridge ownership.
- mode: staged, contribution-first, platform-single-owner migration.
- baseline: keep main runtime chain stable while migrating ownership.

## Batch-0 Freeze Rules (Mandatory)

1. no new `smart_core_*` bridge function may be added in industry modules.
2. no new direct industry write to platform registry.
3. no new platform policy constants may be owned by industry modules.
4. migration must be staged: protocol first, owner migration second, cleanup last.

## Execution Sequence (High-Level)

1. governance freeze + inventory (`batch-0`)
2. intent handler registry single-owner migration (`batch-1`)
3. capability owner migration to platform core (`batch-2`)
4. scene bridge proxy removal (`batch-3`)
5. platform policy constants ownership migration (`batch-4`)
6. system.init extension protocol migration (`batch-5`)
7. workspace heavy payload startup decoupling (`batch-6`)
8. bridge naming cleanup and compatibility retire (`batch-7`)
9. verify guards + regression + migration report (`batch-8`)

## Guardrails

- migrate ownership before deleting compatibility layers.
- do not mix financial domains into low-risk batches.
- preserve runtime compatibility through contribution protocol adaptation.
- each batch must output verification evidence and rollback path.

## Batch-0 Deliverables

- `docs/refactor/industry_shadow_bridge_execution_plan_v1.md`
- `docs/refactor/industry_shadow_bridge_object_inventory_v1.md`

