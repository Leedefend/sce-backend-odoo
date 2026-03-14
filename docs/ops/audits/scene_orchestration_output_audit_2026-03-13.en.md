# Scene Orchestration Output Audit (2026-03-13)

## Scope
- Goal: validate whether **scene orchestration output contracts** are production-ready before frontend iteration.
- Excluded: frontend rendering implementation details.
- Evidence basis: repository `verify.*` guards and generated artifacts.

## Executed Checks
- `make verify.page_orchestration.target_completion.guard`
- `make verify.page_contract.orchestration_schema.guard`
- `make verify.page_contract.action_schema_semantics.guard`
- `make verify.page_contract.data_source_semantics.guard`
- `make verify.orchestration.semantics_registry.guard`
- `make verify.workspace_home.orchestration_schema.guard`
- `make verify.workspace_home.sections_schema.guard`
- `make verify.workspace_home.provider_split.guard`
- `make verify.scene.schema`
- `make verify.scene.capability.matrix.schema.guard`
- `make verify.scene.contract.semantic.v2.guard`
- `make verify.scene.contract.shape`
- `make verify.runtime.surface.dashboard.report`
- `make verify.runtime.surface.dashboard.schema.guard`

## Summary
- Result: **NOT READY (Fail)** — do not switch to frontend iteration yet.
- Passed: 11 checks
- Failed: 2 checks (blocking)

## Passed Checks (key)
1. `verify.page_contract.orchestration_schema.guard` ✅
2. `verify.page_contract.action_schema_semantics.guard` ✅
3. `verify.page_contract.data_source_semantics.guard` ✅
4. `verify.orchestration.semantics_registry.guard` ✅
5. `verify.workspace_home.sections_schema.guard` ✅
6. `verify.workspace_home.provider_split.guard` ✅
7. `verify.scene.schema` ✅
8. `verify.scene.capability.matrix.schema.guard` ✅
9. `verify.scene.contract.semantic.v2.guard` ✅
10. `verify.scene.contract.shape` ✅
11. `verify.runtime.surface.dashboard.schema.guard` ✅

## Failed Checks (blocking)
### A. `verify.page_orchestration.target_completion.guard` ❌
Errors:
- `workspace_home_contract_builder.py missing token: "page_orchestration_v1": _build_page_orchestration_v1(role_code)`
- `workspace_home_contract_builder.py missing token: "page_orchestration": _build_page_orchestration(role_code)`
- `HomeView.vue missing token: return hasV1 && isDashboard && zones.length > 0;`

Interpretation:
- The guard still sees orchestration completion-chain gaps.

### B. `verify.workspace_home.orchestration_schema.guard` ❌
Errors:
- `pm/finance/owner: zones[3].blocks[0].payload unexpected keys for block_type=entry_grid: max_items`
- `zone priority order should vary across pm/finance/owner for heterogeneous same-page layout`

Interpretation:
- `entry_grid` payload shape is not aligned with orchestration semantics registry.
- Role-heterogeneous zone ordering policy is not satisfied.

## Additional Observation
- `verify.contract.evidence` can currently be blocked by baseline freeze guard; this is a release-governance issue and separate from orchestration output readiness.

## Exit Criteria Before Frontend Switch
1. `verify.page_orchestration.target_completion.guard` passes.
2. `verify.workspace_home.orchestration_schema.guard` passes.
3. Re-run and pass:
   - `make verify.scene.schema`
   - `make verify.scene.contract.semantic.v2.guard`
   - `make verify.runtime.surface.dashboard.schema.guard`

## Next Backend Actions
1. Align `workspace_home_contract_builder` keys/shape with completion-guard expectations (`page_orchestration_v1` + legacy alias behavior).
2. Remove or formally register `entry_grid.payload.max_items` and synchronize semantics guard.
3. Implement explicit heterogeneous zone-priority strategy across PM/Finance/Owner.

