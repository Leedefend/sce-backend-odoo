# Release Navigation Batch Plan

## Batch Information
- batch: `NAV-R1`
- layer_target: `Scene Navigation Contract / Frontend Navigation Consumption / Verify Governance`
- module: `addons/smart_core + addons/smart_construction_core + frontend/apps/web + scripts/verify + docs/ops/releases + docs/ops/iterations`
- reason: `将侧边栏导航纳入正式产品发布治理，修复“发布入口错误”和“导航过薄”问题，并建立独立验证门禁`

## Goal

Freeze and deliver a release-grade sidebar navigation surface for the current PM demo flow.

The navigation must let a user understand and enter the released product slices without relying on deep links or hidden routes.

## Scope

Allowed in this batch:
- define release navigation product contract
- define role-based sidebar entry surface for the PM demo role
- align scene nav contract output with release-ready slice entry points
- align frontend sidebar consumption with the release navigation contract
- add release navigation browser smoke and role-nav guards
- update release docs and iteration ledger

## Not In Scope

Do not do these in this batch:
- modify FR-1 to FR-5 business semantics
- redesign dashboard/plan/execution/cost/payment/settlement internals
- expand finance/contract/approval/reporting scope
- introduce ad hoc frontend-only menu hardcode without contract ownership
- reopen freeze scope of any finished slice

## Product Boundary

The release navigation is a product surface, not a cosmetic sidebar.

It must answer:
- what can this role enter now
- which entries are release-ready
- how the user reaches project lifecycle slices from the published shell

For the PM demo role, the minimum release navigation should expose stable, named entries for:
- project initiation
- project lifecycle / cockpit access
- my work

Project-context-only slices may still require a project to exist, but the sidebar must make that entry strategy explicit instead of hiding the capability.

## Implementation Steps

### Step 1
- operation: write navigation product contract and verification gap analysis
- change_scope: `docs/ops/releases + docs/ops/iterations`
- output: contract baseline, test-gap baseline, resume anchor

done_when:
- navigation batch scope is written
- the reason existing smoke missed the issue is documented

### Step 2
- operation: audit current scene nav contract, role surface, and sidebar consumption
- change_scope: `addons/smart_core + addons/smart_construction_core + frontend/apps/web`
- output: exact mismatch list between role surface, nav contract, and rendered sidebar

done_when:
- root cause is pinned to specific contract fields and render logic
- no implementation starts before the mismatch list is explicit

### Step 3
- operation: implement the minimal contract-side fix for release navigation exposure
- change_scope: `addons/smart_core + addons/smart_construction_core`
- output: navigation contract that exposes release-grade sidebar entries for the PM demo role

done_when:
- sidebar entries come from contract data
- no required release entry depends on hidden fallback/deep link behavior

### Step 4
- operation: implement the minimal frontend consumption alignment
- change_scope: `frontend/apps/web`
- output: sidebar rendering that reflects the release navigation contract without local business inference

done_when:
- clicking release entries lands on the intended product page
- sidebar no longer presents a misleading single-entry experience

### Step 5
- operation: add verification and release gate coverage
- change_scope: `scripts/verify + Makefile + docs/ops/releases`
- output: release navigation browser smoke, role-nav guard, docs entry

done_when:
- real sidebar-click navigation is covered by browser smoke
- role-nav baseline is enforced for the demo PM role

## Verification

- verify:
  - existing release gates for FR-1 to FR-5 must remain green
  - new release-nav guard must validate PM release entries
- snapshot:
  - browser smoke artifacts must capture sidebar-driven entry flow
- guard:
  - role/nav contract guard must assert required release entries
- smoke:
  - browser smoke must start from login and click the real sidebar

## Risks And Rollback

- risk: exposing too many scenes and turning release navigation into a raw scene dump
- rollback: revert nav contract shaping changes and keep docs baseline for the next batch

- risk: frontend starts hardcoding business entries outside contract ownership
- rollback: revert frontend-only mapping and move ownership back to nav contract

- risk: release navigation changes accidentally alter finished slice semantics
- rollback: keep slice-specific pages untouched and revert entry wiring only

## Stop Conditions

Stop the batch if:
- release navigation contract cannot be defined without reopening slice semantics
- sidebar exposure requires hidden business logic in frontend
- existing release gates regress
- a second goal appears, such as homepage redesign or dashboard redesign
