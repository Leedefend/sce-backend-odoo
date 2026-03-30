# ITER-2026-03-30-264

## Summary
- Fixed the install-order-sensitive project list action by removing explicit view refs from the early-loaded action file.
- Verified that `make demo.reset DB=sc_demo` now succeeds.
- Re-ran the full rebuild chain and confirmed `make dev.rebuild.full DB=sc_demo` succeeds and restarts frontend hot reload on `http://127.0.0.1:5174/`.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-264.yaml`
- `addons/smart_construction_core/actions/project_list_actions.xml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-264.yaml`
- PASS: `CODEX_MODE=main make demo.reset DB=sc_demo`
- PASS: `CODEX_MODE=main make dev.rebuild.full DB=sc_demo`

## Risk
- Low to medium.
- The fix is minimal and limited to install-time XML references.
- Runtime behavior remains driven by later-loaded view definitions and action overrides.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-264.yaml`
- `git restore addons/smart_construction_core/actions/project_list_actions.xml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next Suggestion
- Continue product usability iteration on the rebuilt environment, using `http://127.0.0.1:5174/` as the stable frontend dev URL.
