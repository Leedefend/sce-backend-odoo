# LC-PRO-01 unified low-code workbench verification

## Scope and authority

- implementation baseline: `da240df9b98cf24a48f51f9dc83e4e2f1cae9b71`
- branch: `feature/low-code-unified-workbench-v1`
- formal entry: `/admin/business-config`
- business configuration authority remains `smart_core.group_smart_core_business_config_admin`
- platform authority remains `smart_core.group_smart_core_admin`
- no ACL, record rule, contract schema, publish/rollback backend semantic, approval state machine, ordinary-user navigation, or production data change is part of this implementation.

## Action 562 diagnosis

Action 562 is `construction.contract`, `tree,form`, but has no authoritative menu. A direct browser request to `/a/562` resolves to `NAVIGATION_AUTHORITY_DENIED` in under ten seconds with no business data render. The previous acceptance waited for removed list selectors and treated this historical action as a formal runtime page, so its timeout was an audit error rather than a slow production list.

The formal contract-processing example is action 1002, menu 389, label `合同办理`. Browser acceptance now uses 1002/389 for the current-effective runtime path and retains 562 only as an explicit safe-denial regression.

## Product path

The formal information architecture is:

1. business page directory;
2. selected-page context;
3. form, list/search, analysis, menu, and approval configuration tabs;
4. local change inspection and explicit save;
5. read-only opening of the current effective page;
6. versions, rollback, coverage, snapshot, and delivery checks.

The context bar shows the business page, company, role, effective version and dirty state. Model names, action/view identifiers, role keys, intent/payload/boundary evidence and snapshot internals are confined to the collapsed developer tools.

Dedicated form/menu/approval routes preserve the page search, page type, configuration status, selected configuration tab, company/role scope and scroll position in their return contract.

## Safe current-effective opening

`打开当前生效页面` performs navigation only. It does not call any save, publish, set, create, write, rollback, bootstrap or apply intent. `检查当前修改` performs local draft validation and states explicitly that unpublished runtime preview is unavailable. It never publishes temporarily.

The `low_code_safe_open_acceptance.v1` report compares snapshot export and version payloads before and after opening action 1002. Its required assertions are:

- snapshot payload hash unchanged;
- contract count unchanged;
- version count and version payload unchanged;
- published status distribution unchanged;
- no write-like intent observed.

## Design-system and control inventory

The LC-AUDIT-01 baseline contained 136 raw controls and no Sc* use. The final inventory contains 40 classified semantic native controls (29 inputs, 10 selects and one textarea), zero raw product buttons and 108 Sc* component uses. Ninety-six baseline controls moved behind design-system ownership. The two existing inline styles did not increase and hard-coded colour count remains zero. The audit rejects unclassified controls, new hard-coded colors, inline styles and technical-language leakage.

The workbench adds reusable context and impact-confirmation components. Batch bootstrap, approval changes, contract rollback, menu save/hide/move, menu rollback and user-created menu deletion expose page, role, company, change summary, immediate-effect and rollback information before execution.

## Runtime and role acceptance

`low_code_workbench_product_acceptance.v1` freezes three identities:

- business configuration administrator (`wutao` fixture);
- platform administrator (`sc_fx_scene_admin` fixture);
- ordinary project member (`demo_role_project_a_member` fixture).

The first two enter according to existing authority and model ACL facts. The platform administrator is not granted construction-contract access merely for the test. The ordinary user is redirected to the formal access-denied page and receives no page directory, model, version or configuration-count facts.

The same report covers 1440×900, 1920×1080, 2560×1440, 768×1024 and 390×844, keyboard up/down page selection, one H1, zero document overflow, zero default technical-term hits, zero serious/critical axe findings, and zero unexpected console/page/request failures.

`low_code_workbench_fault_acceptance.v1` injects 400, 401, 409, 422, 500 and network failure. A 401 clears the session and returns to login. Other cases retain product context and recover through an authoritative reread. A backend 403 maps to the shared access-denied product state.

## Executable gates

- `verify.business_config.guard_inventory`
- `verify.business_config.unit`
- `verify.business_config.product_guard`
- `verify.business_config.config_workbench_operation_acceptance`
- `verify.business_config.safe_open_acceptance`
- `verify.business_config.workbench_product_acceptance`
- `verify.business_config.workbench_fault_acceptance`
- `verify.business_config.full_acceptance`

The inventory resolves included Make sources recursively, verifies each target has a real recipe/script owner, records scan/component/intent/assertion counts, and runs negative self-tests. `make -n` must expose the underlying commands; empty-success aggregate targets are rejected.

The final inventory executes across 12 included Make sources, 31 scanned files, 10 components, 30 intents and 147 assertions. Its negative self-test proves a deliberately empty target, an unregistered surface, a product-language violation and a boundary violation each fail rather than silently succeeding. The low-code unit aggregate executes 159 tests.

## Final acceptance evidence

- Safe current-effective opening: PASS; payload hash `a2ba7631730db902a664b8f2479ba76f45b64d758008829c870067c8d1321712`, 1,216 contracts and 27 versions unchanged, with zero write-like intents.
- LC-J01 through LC-J10: PASS; operation report records 64/64 assertions, 10/10 journeys, 19/19 actions and 9/9 screenshots.
- Product matrix: PASS for three authority identities and five viewports; axe critical/serious, document overflow, console errors, page errors and unexpected request failures are all zero.
- Failure recovery: PASS for 400, 401, 409, 422, 500 and network failure.
- Existing frontend journeys J02-J13: PASS in the current acceptance fixture, including company A-B-A isolation, project scope, My Work, payment creation/approval, record forms, dirty guard and 409 recovery.
- Navigation authority: PASS 70/70 (`finance=42`, `project_member=9`, `pm=14`, `owner=5`); action 876 and menu 606 remain denied.
- Frontend lint, strict typecheck, production build, generated-report freshness, `git diff --check` and `make ci.local.quick`: PASS.

## Complexity and containment

`BusinessConfigSurfaceView.vue` decreased from its 1,486-line locked baseline to 1,474 lines while navigation, product experience and impact-confirmation state moved into focused composables. New Vue files are 64 and 44 lines; new composables are 138, 128 and 36 lines. No new file exceeds 600 lines, and `ContractFormPage.vue`, `ListPage.vue`, ordinary navigation, backend schemas and permission files are unchanged.

## Known environment debt

The historical `sc_demo` database contains two user-visible showcase actions (1019 and 1020) without list/search configuration, so the pre-existing coverage gate rejects that mutable database. A clean frontend fixture does not contain the full tenant low-code configuration baseline, and legacy list-contract labels still have independent source-label mismatches. These conditions predate LC-PRO-01, are not hidden by reducing scan scope, and are not repaired by changing production data or ordinary navigation in this branch. The formal LC-PRO-01 gates use the frozen administrator fixture and keep these findings visible for environment remediation.

Final merge SHA, PR, CI, journey matrix and diff statistics are recorded in the PR closeout report after the single final full-CI run.
