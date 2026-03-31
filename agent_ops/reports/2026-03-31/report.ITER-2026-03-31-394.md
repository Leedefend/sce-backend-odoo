# ITER-2026-03-31-394 Report

## Summary

- Audited the exact fidelity gaps between the native `portal.dashboard`
  capability and the current custom `工作台`.
- Decomposed the gaps into entry, render, and delivery categories.
- Determined that the current gaps are concrete and explainable, not ambiguous.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-394.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-394.md`
- `agent_ops/state/task_results/ITER-2026-03-31-394.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-394.yaml` -> PASS

## Native Baseline

The native `portal.dashboard` capability is narrow and concrete:

- source:
  - `addons/smart_construction_core/services/portal_dashboard_service.py`
- shape:
  - fixed `entries` registry
- entry set:
  - `project_work`
  - `contract_work`
  - `cost_work`
  - `finance_work`
  - `capability_matrix`

Each native entry resolves from real `menu_xmlid + action_xmlid` facts and
ultimately targets either a native act-window URL or an act-url value.

## Custom Workbench Surface

The current custom `工作台` is implemented in:

- `frontend/apps/web/src/views/HomeView.vue`

Its effective behavior is broader than the native dashboard:

- entries are derived from `session.scenes`
- cards are further derived from `capabilityGroups`
- it also renders:
  - today actions
  - risk buckets / trend / source breakdown
  - metrics
  - enterprise enablement
  - advisory and navigation shortcuts

## Fidelity Gap Matrix

### 1. Entry Fidelity Gap

Status: `present`

#### Native

- fixed five-entry registry
- entry identity is explicit and stable

#### Custom

- entry pool is built from `session.scenes`, scene tiles, and capability groups
- visible entry set is broader than the five native dashboard entries

#### Decision

The custom workbench no longer preserves native dashboard entry fidelity.
It expands the entry surface beyond the native capability definition.

### 2. Render Fidelity Gap

Status: `present`

#### Native

- a compact entry list / dashboard-style fact contract
- simple resolved entries with allow/deny and target

#### Custom

- hero + risk + metrics + advice + recommendation + action deck composition
- multiple analytical and prioritization sections that do not exist in the
  native dashboard entry contract

#### Decision

The custom workbench does not render the native dashboard fact shape directly.
It renders a product-level workspace composition instead.

### 3. Delivery Logic Gap

Status: `present`

#### Native

- delivery logic is simple:
  - expose allowed entries
  - open the resolved native target

#### Custom

- delivery logic includes:
  - recommendation picking
  - risk-action mutation fallback
  - role landing resolution
  - advisory routing
  - enterprise enablement routing

#### Decision

The custom workbench no longer delivers the same capability logic as the native
dashboard. It adds higher-level product routing and prioritization logic on top
of the native capability layer.

## Overall Decision

`工作台` differs from native `portal.dashboard` in all three fidelity categories:

- entry fidelity
- render fidelity
- delivery fidelity

This means the current workbench is not a partial mismatch. It is a deliberate
expansion beyond the original native dashboard capability.

## Recommendation

Current recommendation: `accept_as_product_behavior`

Reason:

- the gap is explicit and coherent, not accidental drift caused by a broken
  parser
- other audited surfaces remain faithful, so there is no evidence of a
  repository-wide parsing failure
- repairing workbench back to native fidelity would be a product decision, not a
  small correctness fix

Only open a repair batch if the objective is explicitly:

- "restore workbench to native portal-dashboard fidelity"

That repair scope should then be limited to:

- entry set narrowing
- section/render narrowing
- removal of higher-level product routing from workbench

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No implementation files were modified.
- The only real risk is governance ambiguity if the repository keeps calling the
  current workbench a direct native dashboard rendering.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-394.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-394.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-394.json`

## Next Suggestion

- Treat the current workbench as an accepted product behavior unless the owner
  explicitly asks to restore native dashboard fidelity.
- If stricter fidelity is required later, open a dedicated repair batch only for
  workbench.
