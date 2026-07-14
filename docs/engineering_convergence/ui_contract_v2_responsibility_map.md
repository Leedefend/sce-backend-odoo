# UI Contract V2 Responsibility Map

Date: 2026-07-14
Owner: Platform owner
Target file: `addons/smart_core/handlers/ui_contract_v2.py`
Current size: 3,518 lines
Phase: Stage 3 form layout governance helper split

## Purpose

`ui_contract_v2.py` is the unified page contract v2 projection entrypoint. It
adapts `ui.contract` output, applies platform and owner extension projections,
assembles v2 contracts, trims delivery shape for the client, and returns an
`IntentExecutionResult`.

It must remain a projection surface. It may read Odoo metadata and records to
build contracts, but it must not become the source of business truth, backend
permission truth, persistence rules, or industry-owned policy.

## Public Entry Points

| Entry point | Responsibility | Boundary |
| --- | --- | --- |
| `UiContractV2Handler.handle` | Main v2 contract orchestration for `ui.contract` and `scene_contract_v1`. | May call `UiContractHandler`, assembler, extension hooks, and read-side injectors. |
| `UiContractV2Handler.source_authority_contract` | Publishes source-authority metadata for v2 output. | Pure metadata. |
| `_safe_eval_action_value` | Safely parses action domain/context values. | Pure parsing fallback; no env access. |
| `_allowed_models_from_hook` | Reads extension hook allowlists for collaboration attachments. | Hook read only. |
| `_standard_chatter_actions` | Builds default chatter action descriptors. | Pure descriptor builder. |

## Responsibility Bands

| Band | Current responsibility | Extraction direction |
| --- | --- | --- |
| Source contract orchestration | Parameter normalization, `UiContractHandler` invocation, entry contract resolution, v2 assembly, extension hook sequencing, trimming, and envelope creation. | Keep in handler until transaction map is complete. |
| V2 contract mutation helpers | Set container tree, widget status, data meta, governance patch, and content replacement. | Small pure helper module. |
| Policy projection | Delete/surface/list profile projection, source authority envelopes, field status projection, native widget visibility. | Projection helper module with no ORM access. |
| Business config form layout | Business config group movement, form layout governance, relation entry policy injection, business category form policy, form structure contract creation. | Split only after tests cover form policy and configured group order. |
| List and kanban projection | Legacy visible labels, business list profile merge, kanban field merge, action-scoped visible columns, SCBS55 legacy overrides. | Read-side list projection module; keep action/view ORM boundaries explicit. |
| Collaboration and header actions | Chatter/attachment contract, standard submit button, file hook allowlists. | Collaboration projection module; hook reads allowed, no writes. |
| Record and view hydration | Record snapshot read, attachment display values, native group column extraction from `ir.ui.view` XML. | Read-side hydration module with strict field-count limits and tests. |
| Scene contract projection | Scene contract source loading and scene v2 assembly path. | Scene projection helper once scene behavior tests exist. |
| Request adapters | Payload/header parsing, trim limits, ui.contract params, result envelope, error result. | Pure request adapter module. |

## Current Side-Effect Boundaries

These functions are read-side or integration boundaries and should not be moved
as a batch:

| Boundary | Reason |
| --- | --- |
| `handle` | Orchestrates projection env creation, `UiContractHandler`, extension hooks, assembler, trimming, and final result envelope. |
| `_resolve_entry_contract` | May perform a second `UiContractHandler` read to resolve menu entries into model contracts. |
| `_inject_action_window_contract` | Reads `ir.actions.act_window`, safely parses action domain/context, and merges action metadata into the source contract. |
| `_inject_current_form_settings_action` | Delegates to `PageAssembler` for current form settings action projection. |
| `_inject_business_category_form_policy` | Reads action context, delegates to `PageAssembler`, applies contract governance, relation-entry hooks, and form-structure injection. |
| `_merge_user_list_preference_columns` | Reads `sc.user.view.preference` for user list column preferences. |
| `_form_structure_governance` | Reads `ui.business.config.contract` view orchestration contracts and composes governance metadata. |
| `_merge_business_list_profile` | Reads business config contracts and action/view-specific list configuration. |
| `_action_scoped_visible_list_columns` | Reads `ir.actions.act_window` and parses tree/list view XML. |
| `_scbs55_legacy_visible_list_override` | Reads SCBS55 legacy priority menu plans to project old-system visible fields. |
| `_inject_record_business_category_context` | Reads the target record business category and merges request context. |
| `_hydrate_record_snapshot` | Reads selected target record fields for form snapshots. |
| `_hydrate_attachment_display_values` | Reads `ir.attachment` display values for attachment fields. |
| `_inject_native_group_layout_columns` | Reads `ir.ui.view` XML and transfers native group column metadata. |
| `_scene_contract_source` | Reads scenes through `load_scenes_from_db_or_fallback`. |

## Do Not Move Yet

Do not move these responsibilities before behavior coverage exists:

- the main `handle` transaction;
- `UiContractHandler` re-entry in `_resolve_entry_contract`;
- `PageAssembler` delegation in form settings and business category policy;
- action/window metadata injection;
- user preference merge;
- record snapshot hydration;
- view XML parsing;
- SCBS55 legacy-visible projection;
- scene contract source loading.

## Stage 1 Target

Stage 1 is complete:

- `ui_contract_v2_adapters.py` owns request/result adapters:
  `_params`, `_headers`, `_trim_limit_params`, `_ui_contract_params`,
  `_envelope`, `_err`;
- `ui_contract_v2_adapters.py` also owns pure value builders:
  `_safe_eval_action_value`, `_standard_chatter_actions`,
  `_v2_policy_projection_source_authority`, `_v2_policy_projection`;
- `ui_contract_v2.py` keeps compatibility methods and delegates to the adapter
  module;
- `handle`, `UiContractHandler`, `PageAssembler`, ORM reads, extension
  hooks, scene loading, and XML parsing in `ui_contract_v2.py`;
- `ui_contract_v2.py` is locked at `<=3731` lines for this stage.

## Stage 2 Target

Stage 2 is complete:

- `ui_contract_v2_projection.py` owns pure v2 mutation helpers:
  `_set_v2_container_tree`, `_set_v2_widget_status`, `_set_v2_data_meta`,
  `_replace_v2_contract_content`, and `_set_v2_governance_patch`;
- `ui_contract_v2_projection.py` also owns pure policy/status projection:
  `_project_v2_source_policies`, `_apply_field_policies_to_v2_status`, and
  `_ensure_native_layout_widget_status_visible`;
- `ui_contract_v2.py` keeps compatibility methods and delegates to the
  projection module;
- `ui_contract_v2.py` is locked at `<=3556` lines for this stage.

The extracted module must not import Odoo, read `env`, call extension hooks, or
infer backend permissions.

## Stage 3 Target

Stage 3 is complete:

- `ui_contract_v2_projection.py` also owns pure form layout governance helpers:
  `_form_layout_governance`, `_form_layout_governance_columns`,
  `_form_layout_columns_from_governance`,
  `_form_layout_group_visible_from_governance`, and
  `_apply_form_layout_governance_to_group`;
- `ui_contract_v2.py` keeps compatibility methods and delegates to the
  projection module;
- `ui_contract_v2.py` is locked at `<=3518` lines for this stage.

## Stage 4 Candidate

Before moving more code, add behavior coverage around business config form
group rewrites, list projection, and record hydration.

Do not move `_apply_business_config_form_groups_to_v2` yet; it rewrites the
container tree based on configured business groups and needs behavior coverage
for group order, hidden fields, and node preservation.

## Verification Gaps

Before moving transaction-heavy methods, add or confirm behavior coverage for:

- unsupported `source_type` errors;
- trim-limit validation errors;
- menu entry resolution through `_resolve_entry_contract`;
- action context/domain injection;
- business config form groups and field order;
- list column preference merge;
- SCBS55 legacy-visible list override;
- record snapshot hydration fallback;
- attachment display value hydration;
- native group column XML parsing;
- scene contract fallback behavior.

## Invariants

- `ui.contract` remains the upstream source for model/view/menu facts.
- `ui.contract.v2` remains projection-only and rebuildable.
- Extension hooks may enrich projections but must not become hidden writes.
- The frontend must not receive invented backend permission truth from this
  handler.
- Industry-specific business policy should stay behind extension hooks or owner
  modules.
- Every extraction must preserve request parameter aliases and response envelope
  semantics.
