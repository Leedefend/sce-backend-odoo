# P4-P0-03 Contract Form Split Evidence

Date: 2026-07-12
Branch: `topic/p4-p0-03-contract-form-split`
Tracked issue: `#1029`

## Scope

This first P4-P0-03 slice starts decomposing `frontend/apps/web/src/pages/ContractFormPage.vue` without changing product behavior.

Extracted responsibilities:

- Shared contract form types and constants moved to `frontend/apps/web/src/pages/contractForm/types.ts`.
- Action-contract parsing helpers moved to `frontend/apps/web/src/pages/contractForm/actionContract.ts`.
- Generic contract record helpers moved to `frontend/apps/web/src/pages/contractForm/recordUtils.ts`.
- Field, relation-display, date-input, view-label, and UI-error helpers moved to `frontend/apps/web/src/pages/contractForm/fieldUtils.ts`.
- Access-policy normalization moved to `frontend/apps/web/src/pages/contractForm/accessPolicy.ts`.
- Relation descriptor parsing and relation search read-field assembly moved to `frontend/apps/web/src/pages/contractForm/relationDescriptor.ts`.
- One2many column value normalization, input/display helpers, required-value checks, and runtime line-patch labels moved to `frontend/apps/web/src/pages/contractForm/one2manyUtils.ts`.
- Workflow action-row normalization, transition aliases, and evidence-gate row parsing moved to `frontend/apps/web/src/pages/contractForm/workflowContract.ts`.
- Form UI labels, native chatter labels, activity field labels, attachment labels, and native-layout type lookup moved to `frontend/apps/web/src/pages/contractForm/uiLabels.ts`.
- Form-configuration operation-log formatting, internal-field detection, and field-group title normalization moved to `frontend/apps/web/src/pages/contractForm/formConfigHelpers.ts`.
- Native-layout node type detection, column normalization, node counting, and badge-field collection moved to `frontend/apps/web/src/pages/contractForm/nativeLayoutUtils.ts`.

The route component remains the orchestration shell and still owns runtime state, navigation, persistence, and user interaction flow.

## Line Count

| File | Before | After |
| --- | ---: | ---: |
| `frontend/apps/web/src/pages/ContractFormPage.vue` | 13762 | 12904 |

## Boundary Decision

- Backend contracts remain the source of truth for fields, actions, permissions, and Odoo-native structure.
- The frontend extraction only names and consumes already-provided contract data.
- No frontend fallback menu, permission, action, or form policy was introduced.
- No data migration, backend endpoint change, or visual redesign is included in this slice.

## Verification

Local verification completed:

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
