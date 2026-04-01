# ITER-2026-03-31-447

- status: pass
- summary: Recovered `sc_odoo` platform baseline by using the existing baseline autofix path to restore company currency to `CNY`.
- changed_files:
  - runtime only
  - agent_ops/tasks/ITER-2026-03-31-447.yaml
  - agent_ops/reports/2026-03-31/report.ITER-2026-03-31-447.md
  - agent_ops/state/task_results/ITER-2026-03-31-447.json
  - docs/ops/iterations/delivery_context_switch_log_v1.md
- verification:
  - `BASELINE_AUTO_FIX=1 make verify.baseline DB_NAME=sc_odoo` PASS
  - `make verify.platform_baseline DB_NAME=sc_odoo` PASS
- risk:
  - this was a runtime-only recovery, not a durable bootstrap fix
  - durable root-cause repair was handled in `449`
- rollback:
  - rerun `make db.reset DB=sc_odoo`
- next:
  - resume the non-demo install line and verify whether the fresh chain still needs code repair
