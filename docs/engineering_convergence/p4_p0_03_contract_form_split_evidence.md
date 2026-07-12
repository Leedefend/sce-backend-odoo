# P4-P0-03 Contract Form Split Evidence

Date: 2026-07-12
Branch: `topic/p4-p0-03-contract-form-split`
Tracked issue: `#1029`

## Scope

This first P4-P0-03 slice starts decomposing `frontend/apps/web/src/pages/ContractFormPage.vue` without changing product behavior.

Extracted responsibilities:

- Shared contract form types and constants moved to `frontend/apps/web/src/pages/contractForm/types.ts`.
- Action-contract parsing helpers and action-response navigation normalization moved to `frontend/apps/web/src/pages/contractForm/actionContract.ts`.
- Generic contract record helpers moved to `frontend/apps/web/src/pages/contractForm/recordUtils.ts`.
- Field, relation-display, date-input, input-type, view-label, and UI-error helpers moved to `frontend/apps/web/src/pages/contractForm/fieldUtils.ts`.
- Access-policy normalization moved to `frontend/apps/web/src/pages/contractForm/accessPolicy.ts`.
- Relation descriptor parsing, model/order lookup, create/inline-create rules, option-match rules, dynamic-domain dependency detection, blocked-domain checks, relation-search dialog/column normalization, and relation search read-field assembly moved to `frontend/apps/web/src/pages/contractForm/relationDescriptor.ts`.
- One2many subview policy helpers, create-label rules, primary/row label helpers, row-state labels, draft summary, inline command building, column value normalization, input/display helpers, required-value checks, and runtime line-patch labels moved to `frontend/apps/web/src/pages/contractForm/one2manyUtils.ts`.
- Workflow action-row normalization, transition aliases, and evidence-gate row parsing moved to `frontend/apps/web/src/pages/contractForm/workflowContract.ts`.
- Form UI labels, native chatter labels, activity field labels, attachment labels, and native-layout type lookup moved to `frontend/apps/web/src/pages/contractForm/uiLabels.ts`.
- Form-configuration operation-log formatting, internal-field detection, field-group title normalization, field-size labels, config page label normalization, low-code layout column inference, readable-group detection, group-title collection, and runtime group shell merging moved to `frontend/apps/web/src/pages/contractForm/formConfigHelpers.ts`.
- Native-layout node type detection, field-info extraction, field-descriptor merging, field/subview lookup, modifier evaluation, widget metadata, button labels, field/favorite collection, section-title collection, column normalization, node counting, and badge-field collection moved to `frontend/apps/web/src/pages/contractForm/nativeLayoutUtils.ts`.
- Required-value checks, comparable-value normalization, numeric parsing, route-default normalization, and navigation URL normalization moved to `frontend/apps/web/src/pages/contractForm/valueUtils.ts`.
- Workflow phase statusbar normalization moved to `frontend/apps/web/src/pages/contractForm/workflowContract.ts`.
- The Web Contract V2 frontend architecture guard is now part of the local `make ci` gate through `verify.unified_page_contract.v2.web_architecture`.
- P0 split-plan file growth is now locked by `docs/engineering_convergence/complexity_baseline_lock.json` and `scripts/ci/enforce_complexity_baseline_lock.py`.

The route component remains the orchestration shell and still owns runtime state, navigation, persistence, and user interaction flow.

## Line Count

| File | Before | After |
| --- | ---: | ---: |
| `frontend/apps/web/src/pages/ContractFormPage.vue` | 13762 | 12253 |

## Boundary Decision

- Backend contracts remain the source of truth for fields, actions, permissions, and Odoo-native structure.
- The frontend extraction only names and consumes already-provided contract data.
- No frontend fallback menu, permission, action, or form policy was introduced.
- No data migration, backend endpoint change, or visual redesign is included in this slice.
- Existing `groups_xmlids` usage in `ContractFormPage.vue` is locked at 3 occurrences by `scripts/verify/web_contract_v2_frontend_architecture_guard.py`; the next cleanup must reduce this count by moving the remaining entitlement decisions fully behind backend contracts.
- `ContractFormPage.vue` is line-count locked at 12253 lines. Future work must continue extracting or modifying existing owned modules instead of adding new responsibilities to the route component.

## Verification

Local verification completed:

- `python3 scripts/verify/web_contract_v2_frontend_architecture_guard.py`
- `python3 scripts/ci/enforce_complexity_baseline_lock.py`
- `scripts/dev/pnpm_exec.sh -C frontend/apps/web lint:src`
- `scripts/dev/pnpm_exec.sh -C frontend/apps/web typecheck:strict`
- `scripts/dev/pnpm_exec.sh -C frontend/apps/web build`
- `make ci`

Remote verification completed:

- GitHub Actions `v1.1 quality gate`: run `29192606652`, passed on commit `bc4f270bc`.
- GitHub Actions `v1.1 quality gate`: run `29192995214`, passed on commit `11c9be05f`.
- GitHub Actions `v1.1 quality gate`: run `29193447131`, passed on commit `cc958066b`.

## Rollback

Rollback is code-only:

1. Revert this slice commit.
2. Restore the prior inline type/helper definitions in `ContractFormPage.vue`.
3. No database, attachment, menu, or contract migration is required.
