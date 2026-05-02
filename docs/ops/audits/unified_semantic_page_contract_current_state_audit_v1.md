# Unified Semantic Page Contract Current State Audit v1

Date: 2026-05-01
Branch: `codex/contract-system-audit`
HEAD: `3553fd90`
Scope: current contract surfaces, Lite target alignment, governance steps

## 1. Audit Conclusion

结论：不通过直接进入实现。

当前仓库已经具备较多契约能力，但主线尚未收敛到 `Unified Semantic Page Contract Lite`。现状不是“缺契约”，而是“契约族过多、出口未统一、治理顺序需要重排”。

本阶段应停止继续扩展 runtime-heavy `UnifiedPageContract v2+`，转为先治理现有契约现状：

```text
Odoo Native Layer
    ↓
Semantic Adapter Layer
    ↓
Unified Semantic Page Contract Lite
    ↓
Thin Frontend Contract Renderer
```

## 2. Current Contract Inventory

| Contract Surface | Current Assets | Status | Lite Alignment |
|---|---|---|---|
| `ui.contract` native delivery | `addons/smart_core/handlers/ui_contract.py` | Existing, governed, but still returns legacy/native shapes | Source input, not final Lite output |
| `native_view` projection | `addons/smart_core/core/native_view_contract_projection.py` | Existing primary-view projection helper | Useful adapter input |
| `semantic_page` | `docs/architecture/native_view_contract/semantic_page_contract_shape_v1.*`, `docs/contract/snapshots/native_view/*.json` | Guarded, 27 snapshots pass | Strongest current semantic basis |
| `page_orchestration_v1` | `addons/smart_core/core/page_contracts_builder.py` and related bridges | Existing orchestration surface | Compat/source input only |
| `scene_contract_v1` | `addons/smart_core/core/scene_contract_builder.py`, `addons/smart_scene/*` | Existing scene surface | Compat/source input only |
| `api.onchange` | `addons/smart_core/handlers/api_onchange.py`, `frontend/apps/web/src/api/onchange.ts` | Existing patch/modifier/line patch schema | Needs mapping into Lite patch |
| x2many command semantics | `frontend/apps/web/src/app/x2manyCommands.ts`, onchange line patches | Existing and guarded | Needs backend-owned Lite patch shape |
| Frontend contract consumption | `frontend/apps/web/src/app/pageContract.ts`, `ContractFormPage.vue` | Existing but consumes mixed legacy surfaces | Needs thin Lite renderer boundary |
| `UnifiedPageContract v2+` | `docs/architecture/unified_page_contract_v2/*`, `addons/smart_core/core/unified_page_contract_v2_*.py` | Exploratory branch assets | Defer, do not continue as active mainline |
| `Unified Semantic Page Contract Lite` | `docs/architecture/unified_semantic_page_contract_lite_design.md`, `docs/architecture/unified_page_contract_lite/*` | New baseline exists and guard passes | Active target |

## 3. Verification Evidence

Passed:

```text
make verify.unified_page_contract.lite
make verify.native_view.semantic_page
make verify.frontend.onchange_contract_schema.guard
make verify.frontend.onchange_roundtrip.guard
make verify.frontend.x2many_command_semantic.guard
```

Notes:

- `verify.unified_page_contract.lite` confirms the Lite shape forbids `runtimeContract`, `componentRegistry`, `capabilities`, `dependencyGraph`, selector status, streaming, subscriptions, and DSL-like action fields.
- `verify.native_view.semantic_page` confirms 27 native view semantic snapshots pass current shape/schema guards.
- Onchange and x2many guards confirm current roundtrip primitives exist, but they are not yet normalized as Lite `statusPatch/dataPatch/layoutPatch`.

## 4.达标项

- Lite target shape has been defined with six top-level keys only:
  `pageInfo`, `layoutContract`, `statusContract`, `actionContract`, `dataContract`, `meta`.
- Native view semantic page already has a governed baseline and snapshots.
- Form/tree/search/kanban semantic coverage has existing audit docs and guards.
- Modifiers parsing exists in the Odoo view parser and supports `readonly/required/invisible/domain` normalization primitives.
- `api.onchange` already returns patch, modifiers patch, warnings, applied fields, and line patches.
- x2many command conversion has frontend guard coverage.
- `ui.contract` already blocks native frontend delivery for some native surfaces unless internal source modes are used.

## 5.未达项

- [S1][canonical-output] No production assembler currently emits the Lite top-level contract as the canonical page output.
- [S1][semantic-adapter] Existing semantic assets are scattered across `native_view`, `semantic_page`, `page_orchestration_v1`, `scene_contract_v1`, and `ui.contract`; no single adapter maps them into Lite.
- [S1][status-contract] ACL, record rule, modifiers, action gating, and render profile are not yet unified into Lite `statusContract.widgetStatus/buttonStatus`.
- [S1][action-contract] Current action surfaces include richer semantics and mixed action schemas; Lite requires event declaration only with backend dispatch.
- [S1][patch-protocol] `api.onchange` patch exists, but no canonical mapping to Lite patch keys exists yet.
- [S1][frontend-boundary] Frontend currently consumes multiple legacy contract surfaces and contains compatibility selection logic; Lite renderer boundary is not yet isolated.
- [S2][v2-assets] Runtime-heavy v2+ files remain in the working tree and may confuse the active direction unless explicitly marked as deferred/reference-only.

## 6. Blockers Before Implementation

- [S0][mainline-freeze] Must freeze `Unified Semantic Page Contract Lite` as current active target before adding new backend/frontend implementation.
  Impact: without freeze, subsequent work may continue expanding v2+ runtime concepts.
  Recommendation: add a governance guard that blocks active Lite examples from accepting runtime-heavy fields.

- [S0][adapter-boundary] Must define the first adapter input/output contract.
  Impact: without adapter boundary, implementation may hard-code mappings in handlers or frontend.
  Recommendation: create a pure backend adapter that maps existing native contract payloads into Lite contract examples/snapshots first.

## 7. Governance Steps

### Step 1 - Freeze Active Target

Goal: make Lite the only current-stage canonical target.

Actions:

- Keep `docs/architecture/unified_semantic_page_contract_lite_design.md` as active direction doc.
- Keep `docs/architecture/unified_page_contract_lite/unified_page_contract_lite.schema.json` as active schema.
- Mark v2+ as exploratory/deferred in implementation plan and avoid new runtime-heavy batches.

Exit criteria:

- `make verify.unified_page_contract.lite` passes.
- No active Lite schema/example contains `runtimeContract`, `componentRegistry`, `capabilities`, `dependencyGraph`, selector status, streaming, subscription, or DSL action fields.

### Step 2 - Build Semantic Adapter Inventory

Goal: list exact source fields that can feed Lite.

Actions:

- Map `native_view/semantic_page` zones and blocks to `layoutContract.containerList/widgetList`.
- Map field modifiers, permission verdicts, action gating, ACL, and record rule outcomes to `statusContract`.
- Map header buttons, field onchange triggers, save/cancel, x2many row actions to `actionContract.actionRuleList`.
- Map record values, relation rows, and dictionaries to `dataContract`.

Exit criteria:

- A mapping table exists for form/tree/x2many/search at minimum.
- Each mapping declares source, target, owner, and confidence.

### Step 3 - Add Pure Backend Lite Adapter

Goal: create a deterministic backend adapter without touching frontend runtime.

Actions:

- Add a pure module under `addons/smart_core/core` for Lite assembly from existing native contract payloads.
- Start with form and tree snapshots only.
- Emit snapshots under `docs/architecture/unified_page_contract_lite/snapshots/`.

Exit criteria:

- Guard validates generated Lite snapshots.
- Adapter has no ORM write behavior and no frontend dependency.

### Step 4 - Normalize Patch Mapping

Goal: map existing onchange response into Lite patch.

Actions:

- Convert `patch` into `dataPatch`.
- Convert `modifiers_patch` into `statusPatch`.
- Convert `line_patches` into relation-scoped `dataPatch` entries.
- Allow only `replace` and `merge`.

Exit criteria:

- Onchange guard still passes.
- New Lite patch guard validates example patches.

### Step 5 - Thin Frontend Boundary

Goal: prevent frontend from continuing to own semantic compatibility.

Actions:

- Introduce a small Lite consumer boundary: ContractStore, PatchMerge, Renderer, ActionDispatcher.
- Keep existing mixed legacy consumer behind compatibility only.
- Do not add business inference or runtime kernel behavior.

Exit criteria:

- Frontend can render one Lite form snapshot without reading `scene_contract_v1` or `page_orchestration_v1`.
- Existing frontend quick guards still pass.

## 8. Stop Conditions

Stop the batch if any of the following happens:

- A new runtime layer, scheduler, hydration, dependency DAG, CRDT, streaming, or AI orchestration requirement enters Phase 1.
- ActionContract starts carrying executable business logic, condition branches, loops, JSON logic, or workflow DSL.
- Frontend begins inferring permissions, readonly, required, visible, workflow state, or business linkage.
- A mapping requires changing `login -> system.init -> ui.contract` startup semantics.
- A guard fails and the fix would cross from backend adapter into frontend runtime in the same batch.

## 9. Recommended Next Batch

Batch name: `Lite Phase 1 / Batch-1 - Semantic Adapter Mapping Inventory`

Layer Target: Contract Governance / Semantic Adapter

Module:

- `docs/architecture/unified_page_contract_lite/`
- `docs/ops/audits/`
- read-only references under `addons/smart_core`

Reason:

- The current risk is not implementation difficulty; it is uncontrolled contract convergence. The next batch should produce the exact source-to-Lite mapping table before writing adapter code.

Do:

- Audit form/tree/x2many/onchange/permissions sources.
- Produce a mapping matrix and sample target snapshots.
- Keep the runtime thin and backend semantics authoritative.

Do not:

- Implement frontend renderer.
- Add runtimeContract.
- Continue v2+ runtime-heavy batches.
- Add component registry, selector status, dependency graph, realtime, collaboration, or AI orchestration.
