# ITER-2026-03-30-378 Report

## Summary

- Audited the ownership boundary of the subscription-governance assets centered
  on `sc.subscription.plan`.
- Confirmed that this is not an isolated seed-file problem: it is a compact
  core-local subsystem spanning models, default data, ACLs, admin menus, and
  ops APIs.
- Concluded that the subscription-governance assets should stay in
  `smart_construction_core` for now and only move under a dedicated future
  ownership objective.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-378.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-378.md`
- `agent_ops/state/task_results/ITER-2026-03-30-378.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-378.yaml` -> PASS

## Fact Chain

### Model Ownership

- `sc.subscription.plan`
- `sc.subscription`
- `sc.entitlement`
- `sc.usage.counter`

These models are all defined in:
- `addons/smart_construction_core/models/support/subscription.py`

### Default Data

- default subscription plans are seeded in:
  - `addons/smart_construction_core/data/sc_subscription_default.xml`

### UI / Menu Ownership

- subscription plan, subscription instance, entitlement, usage counter, and ops
  job views/actions/menus are all defined in:
  - `addons/smart_construction_core/views/support/subscription_views.xml`
- all these menus are bound under the core config-admin surface and gated by:
  - `smart_construction_core.group_sc_cap_config_admin`

### ACL Ownership

- `ir.model.access.csv` in core grants:
  - internal-user read on `sc.subscription.plan`
  - config-admin full admin on subscription-governance models

### Runtime / API Usage

- `addons/smart_construction_core/controllers/ops_controller.py` directly uses:
  - `sc.subscription.plan`
  - `sc.subscription`
  - `sc.entitlement`
  - `sc.usage.counter`
- the entitlement flow resolves effective feature flags and limits from the
  subscription plan data for company-scoped runtime behavior

## Ownership Result

### Stay In `smart_construction_core` For Now

- `sc_subscription_default.xml`
- the subscription-governance models and support views around it

Reason:
- the seed file is not independent; it belongs to a full core-local subsystem
- ownership is still coherent inside core:
  - models
  - ACLs
  - admin menus/actions
  - ops API usage
  - entitlement runtime resolution
- moving only the seed file would create split ownership without reducing real
  coupling

## Boundary Conclusion

- The previous core-data cleanup line is complete.
- Subscription governance is a separate product/governance subsystem, not an
  accidental residue from scene/bootstrap cleanup.
- If this subsystem is ever moved, it should be moved as a dedicated ownership
  design line, not by continuing the current piecemeal data migration pattern.

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No model, security, manifest, payment, settlement, account, or frontend files
  were modified.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-378.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-378.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-378.json`

## Next Suggestion

- Do not continue the current ownership-migration chain into subscription by
  default.
- Only reopen this area under a dedicated `subscription governance` objective
  that is allowed to decide model, menu, ACL, and runtime ownership together.
