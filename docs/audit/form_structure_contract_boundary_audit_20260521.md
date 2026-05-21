# Form Structure Contract Boundary Audit 2026-05-21

## Scope

This audit covers the v2 form-structure chain:

- backend parser and business fact source: native Odoo model, fields, views, and existing `ui.contract` payload
- governance: `ui.contract.v2` classification and field admission
- orchestration: `unified_page_contract_v2_assembler` layout grouping
- contract: top-level `formStructureContract`
- frontend: generic v2 renderer consumption

The target change is page-structure orchestration only. It must not create business facts, widen list fields, or expose platform/internal fields as user-facing form tasks.

## Boundary Contract

| Layer | Authority | Must Not Do |
| --- | --- | --- |
| Business fact/model view | Owns real fields, values, native visibility, and model semantics | Encode product layout policy |
| `ui.contract.v2` governance | Selects allowed form fields from governed form layout/field groups and assigns generic roles | Treat all model fields, `fields`, or broad `visible_fields` as user-facing form fields |
| Assembler | Reorders already-authorized fields into overview and task slots | Invent fields or discard native invisible/modifier rules |
| `formStructureContract` | Carries projection-only structure metadata | Become a business-fact source |
| Frontend renderer | Renders the contract generically | Add business-specific field decisions |

## Findings

### F1: Form structure leaked into list profile

Root cause: form-oriented fields were temporarily added to shared business operation priority/profile data, then tree/list projection consumed the same profile.

Impact: list column order and visible columns could drift while only form structure was being changed.

Status: fixed. Form field candidates are now only collected for `view_type == "form"`, and the list guard proves tree projection does not import form-only fields.

### F2: Field existence was treated as form visibility

Root cause: `fields`/`visible_fields` were treated as candidate authority. These are compatibility and data surfaces, not necessarily user-facing form layout authority.

Impact: hidden or non-task fields could enter `fieldRoles` and then be rendered by the structured form.

Status: fixed. Form structure now prefers native form layout and explicit field groups. `visible_fields` is fallback-only when no governed layout/group exists.

### F3: Orchestration discarded native invisibility

Root cause: assembler recreated bare field nodes from field names and dropped native `invisible`, `attrs`, and `modifiers`.

Impact: fields intentionally hidden by the native form could become visible through the structured layout.

Status: fixed. Assembler now reuses native field nodes and skips native-hidden fields.

### F4: Internal/platform field policy was incomplete

Root cause: governance filtering initially covered only technical and legacy-source fields. Project forms still admitted platform fields such as alias, access, dashboard, favorite, and source-origin style fields.

Impact: the structured form could show fields that are not part of the user's business task.

Status: tightened. Governance and runtime guard now reject common internal field families:

- `access_*`
- `alias_*`
- `allow_*`
- `dashboard_*`
- `favorite_*`
- `last_update_*`
- `privacy_*`
- `source_origin`
- `is_favorite`
- `task_properties`
- validation/source/legacy helper tokens, except explicitly allowed legacy display fields

### F5: Overview duplicates are not a boundary issue

Root cause: runtime guard treated any repeated field reference as an error. The structured form intentionally repeats a few key fields in the readonly overview and task sections.

Impact: duplicate warnings hid real boundary violations.

Status: fixed. Runtime guard allows one overview summary reference plus one task-slot reference, while still rejecting repeated fields inside task structure.

## Current Judgment

The user concern is valid. The original bug came from a boundary mistake: the orchestration path used field availability as if it were task visibility. The page-structure contract must be governed by an allowed form field set, not by all fields the backend can read.

The current implementation is closer to the intended split:

- facts remain in model/view/data contracts
- governance admits form fields and roles
- assembler only projects admitted fields
- runtime guard rejects internal field references
- frontend remains generic

Negative filtering alone is not accepted as the final product boundary. The current architecture rule is positive governance: `ui.contract.v2` may emit `formStructureContract` only when the source contract carries view-orchestration governance from `business_view_orchestration`. Without that governance source, v2 keeps the native form layout and does not perform structured form rearrangement.

The current implementation also stops form-structure preparation from widening `visible_fields`, appending synthetic `field_groups`, or producing list profiles on form requests. List profiles are list/tree responsibilities only.

## Verification

- `python3 addons/smart_core/tests/test_unified_page_contract_v2_runtime.py`
- `python3 addons/smart_core/tests/test_ui_contract_v2_boundaries.py`
- `make verify.unified_page_contract.v2`

Runtime Odoo sampling was attempted against `sc_demo`, but the local `odoo` service was not running at audit time.
