# ITER-2026-03-31-449

- status: pass
- summary: Restored the compatibility shim `post_init_hook` declaration so fresh `db.reset` now executes the CNY bootstrap hook automatically again.
- changed_files:
  - addons/smart_construction_bootstrap/__manifest__.py
- verification:
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-449.yaml` PASS
  - `make db.reset DB=sc_odoo` PASS
  - `make verify.platform_baseline DB_NAME=sc_odoo` PASS
- risk:
  - high-risk manifest recovery batch
  - scoped only to shim hook reattachment for fresh-db currency init
- rollback:
  - git restore addons/smart_construction_bootstrap/__manifest__.py
- next:
  - resume the non-demo install line from `446`
