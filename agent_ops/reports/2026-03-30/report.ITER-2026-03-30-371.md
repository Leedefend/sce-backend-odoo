# ITER-2026-03-30-371 Report

## Summary

- Cleaned one clear boundary violation in the industry core module:
  - moved the dormant demo business-facts file `cost_domain_demo.xml`
  - out of `smart_construction_core`
  - into the already loaded demo dataset file `smart_construction_demo/data/base/cost_demo.xml`
- Removed the orphan demo file from the core module.

## Changed Files

- `addons/smart_construction_core/data/cost_domain_demo.xml`
- `addons/smart_construction_demo/data/base/cost_demo.xml`
- `agent_ops/tasks/ITER-2026-03-30-371.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-371.md`
- `agent_ops/state/task_results/ITER-2026-03-30-371.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-371.yaml` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_demo DB_NAME=sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Boundary Judgment

This batch intentionally did **not** move every file under `smart_construction_core/data`.

Files such as these remain in core because they are runtime baseline/configuration facts rather than demo business facts:

- `project_stage_data.xml`
- `project_stage_requirement_items.xml`
- `project_next_action_rules.xml`
- `sc_capability_group_seed.xml`
- `sc_subscription_default.xml`
- `sequence.xml`
- `sc_extension_params.xml`
- `sc_extension_runtime_sync.xml`
- `sc_cap_config_admin_user.xml`

The file moved in this batch was different:

- `cost_domain_demo.xml`
  - was not loaded by the core manifest
  - contained only demo partners / demo project / demo WBS / demo budget / demo ledger / demo progress records
  - therefore belonged in `smart_construction_demo`

## Risk Analysis

- Risk stayed low.
- No manifest, security, model, or frontend files were touched.
- The demo facts were merged into an already loaded demo file, so no new manifest entry was needed.

## Rollback

- `git restore addons/smart_construction_core/data/cost_domain_demo.xml`
- `git restore addons/smart_construction_demo/data/base/cost_demo.xml`
- `git restore agent_ops/tasks/ITER-2026-03-30-371.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-371.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-371.json`

## Next Suggestion

- Open one audit batch that classifies the remaining `smart_construction_core/data/*.xml` files into:
  - runtime baseline/config
  - domain dictionary/taxonomy
  - still-misplaced demo facts
- Use that audit to drive the next cleanup batch, instead of assuming every `data` file should leave core.
