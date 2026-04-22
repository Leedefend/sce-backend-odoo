# Native Business-Fact Next-Stage Roadmap v1

## Current Baseline

- Seven-audit chain core objective achieved.
- Legacy auth strict gate fixed.
- Step-5/6 minimal ACL/rule closure completed.
- Minimal install-time dictionary seed materialized with visibility evidence.

## Stage-A (Low Risk, Priority)

1. Post-install entry smoke expansion (short-chain only)
   - Verify dictionary/project/task key entry actions remain available
   - Commands:
     - `make verify.scene.legacy_contract.guard`
     - `make verify.test_seed_dependency.guard`

2. Seed consistency evidence refresh
   - Reconfirm manifest/data presence and non-transactional boundaries
   - Commands:
   - `python3 agent_ops/scripts/validate_task.py <task.yaml>`

### Stage-A Progress

- Batch1 (`ITER-2026-04-06-1198`): PASS
  - `make verify.scene.legacy_contract.guard` PASS
  - `make verify.test_seed_dependency.guard` PASS
  - `make verify.scene.legacy_auth.smoke.semantic` PASS
- Batch2 (`ITER-2026-04-06-1199`): PASS
  - `make verify.scene.legacy_contract.guard` PASS
  - `make verify.test_seed_dependency.guard` PASS
  - `make verify.scene.legacy_auth.smoke.semantic` PASS
  - Entry click-path static evidence reinforced (dictionary action set)
- Batch3 (`ITER-2026-04-06-1200`): PASS
  - `make verify.scene.legacy_contract.guard` PASS
  - `make verify.test_seed_dependency.guard` PASS
  - `make verify.scene.legacy_auth.smoke.semantic` PASS
  - Broader key-entry evidence aggregated (dictionary + cost/budget + payment/settlement)

## Stage-B (Medium Risk, Controlled)

1. Extend non-transactional dictionary seed scope
   - Add only enum-like dictionary facts needed by native views
   - Keep financial transactions out of seed

2. Targeted regression matrix
   - Legacy contract guard
   - Seed dependency guard
   - Auth smoke semantic guard

### Stage-B Execute Progress

- Batch1 (`ITER-2026-04-06-1202`): PASS
  - Non-transactional dictionary seed expanded (status/stage/task/payment/settlement/contract categories)
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-06-1202.yaml` PASS
  - `make verify.scene.legacy_contract.guard` PASS
  - `make verify.test_seed_dependency.guard` PASS
  - `make verify.scene.legacy_auth.smoke.semantic` PASS
  - Evidence: `docs/audit/native/native_stage_b_batch1_evidence_v1.md`

- Batch2 (`ITER-2026-04-06-1203`): PASS
  - Targeted regression matrix re-run completed
  - `make verify.scene.legacy_contract.guard` PASS
  - `make verify.test_seed_dependency.guard` PASS
  - `make verify.scene.legacy_auth.smoke.semantic` PASS
  - Visibility evidence refreshed: `docs/audit/native/native_stage_b_batch2_regression_evidence_v1.md`

- Batch3 (`ITER-2026-04-07-1204`): PASS
  - Strict-mode fallback policy evidence refreshed
  - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1204.yaml` PASS
  - `make verify.scene.legacy_contract.guard` PASS
  - `make verify.test_seed_dependency.guard` PASS
  - `make verify.scene.legacy_auth.smoke.semantic` PASS
  - Evidence: `docs/audit/native/native_stage_b_batch3_strict_mode_evidence_v1.md`

### Stage-B Pre-Screen Progress

- Pre-screen (`ITER-2026-04-06-1201`): PASS
  - Boundary and gate set defined in:
    - `docs/audit/native/native_stage_b_prescreen_boundary_v1.md`

## Stage-C (High Risk, On-Demand)

1. ACL/rule expansion beyond current minimal closure
   - Requires dedicated high-risk contract
   - Single-batch verification and rollback required

2. Additional seed materialization touching manifest boundaries
   - Requires explicit narrow-exception alignment before execution

## Regression Checklist (Targeted)

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_contract.guard`
- `make verify.test_seed_dependency.guard`
- `make verify.scene.legacy_auth.smoke.semantic`

## Exit Criteria for Next Stage

- All Stage-A tasks PASS on short-chain verify.
- No new high-risk path touched without dedicated contract.
- Evidence docs updated for each checkpoint.

## Stage-B Closeout Checkpoint

- Closeout Batch (`ITER-2026-04-07-1205`): PASS
  - Stage-B acceptance summary published:
    - `docs/audit/native/native_stage_b_closeout_acceptance_summary_v1.md`
  - Closeout command set PASS:
    - `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1205.yaml`
    - `make verify.scene.legacy_contract.guard`
    - `make verify.test_seed_dependency.guard`
    - `make verify.scene.legacy_auth.smoke.semantic`

## Runtime Availability Evidence (Post Stage-B)

- Evidence Batch (`ITER-2026-04-07-1206`): PASS
  - strict default command exits non-zero when runtime unreachable
  - explicit fallback env enables local debug PASS behavior
  - evidence: `docs/audit/native/native_runtime_availability_evidence_v1.md`

- Listener Evidence Batch (`ITER-2026-04-07-1207`): PASS
  - listener signal observed on `*:8069`
  - direct tcp probe constrained by environment socket permission
  - evidence: `docs/audit/native/native_runtime_listener_reachability_evidence_v1.md`

- Permission Screen Batch (`ITER-2026-04-07-1208`): PASS
  - runtime probe blocker classified as environment capability constraint
  - recovery trigger defined for reachable-window verification
  - evidence: `docs/audit/native/native_runtime_probe_permission_screen_v1.md`

- Live Probe Batch (`ITER-2026-04-07-1209`): PASS
  - escalated live probe executed under strict default
  - observed `RemoteDisconnected` instead of 401/403
  - evidence: `docs/audit/native/native_live_auth_401_403_evidence_v1.md`

- Repair Lane Pre-Screen (`ITER-2026-04-07-1210`): PASS
  - bounded low-risk verify-helper scope defined
  - stop/entry criteria documented for runtime anomaly lane
  - evidence: `docs/audit/native/native_runtime_repair_lane_prescreen_v1.md`

- Repair Lane Batch1 (`ITER-2026-04-07-1211`): PASS
  - unreachable classification hardened for `RemoteDisconnected`
  - semantic verify extended to cover strict-fail/fallback-pass for remote disconnect
  - evidence: `docs/audit/native/native_runtime_repair_lane_batch1_evidence_v1.md`

- Repair Lane Batch2 (`ITER-2026-04-07-1212`): PASS
  - escalated live re-probe executed after helper hardening
  - runtime still returns transport-level `RemoteDisconnected` (not 401/403)
  - evidence: `docs/audit/native/native_runtime_repair_lane_batch2_live_probe_evidence_v1.md`

- Environment Repair Lane Screen (`ITER-2026-04-07-1213`): PASS
  - runtime anomaly classified as environment/service edge behavior
  - dedicated repair lane scope and exit signal defined
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_screen_v1.md`

- Environment Repair Lane Batch1 (`ITER-2026-04-07-1214`): PASS
  - reusable runtime probe utility added (`verify.scene.legacy_auth.runtime_probe`)
  - probe evidence can now be collected repeatedly with warning-mode output
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch1_probe_evidence_v1.md`

- Environment Repair Lane Batch2 (`ITER-2026-04-07-1215`): PASS
  - escalated 8069/8070 matrix sampling completed
  - observed divergence: `8069 -> RemoteDisconnected`, `8070 -> timeout`
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch2_matrix_evidence_v1.md`

- Environment Repair Lane Batch3 (`ITER-2026-04-07-1216`): PASS
  - 8070-focused root-cause evidence captured
  - listener snapshot suggests `8069` active while `8070` listener/forward path missing
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch3_8070_rootcause_evidence_v1.md`

- Environment Repair Lane Batch4 (`ITER-2026-04-07-1217`): PASS
  - no-env fallback port corrected from `8070` to `8069`
  - preserves explicit env/config precedence
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch4_fallback_port_fix_evidence_v1.md`

- Environment Repair Lane Batch5 (`ITER-2026-04-07-1218`): PASS
  - explicit 8070 source screened and confirmed (`Makefile ENV=dev -> .env.dev -> ODOO_PORT=8070`)
  - fallback ambiguity removed; next step is runtime readiness on configured port
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch5_8070_config_source_screen_v1.md`

- Environment Repair Lane Batch6 (`ITER-2026-04-07-1219`): PASS
  - dev explicit port aligned to `8069` (`.env.dev` updated)
  - runtime probe defaults now anchor on 8069 path
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch6_dev_port_alignment_evidence_v1.md`

- Environment Repair Lane Batch7 (`ITER-2026-04-07-1220`): PASS
  - 8069 service-chain evidence strengthened via direct handshake trace
  - observed connection accepted then closed (`RemoteDisconnected`)
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch7_8069_service_chain_evidence_v1.md`

- Environment Repair Lane Batch8 (`ITER-2026-04-07-1221`): PASS
  - process/entry diagnostics captured from compose ps and odoo logs
  - service snapshot inconsistency documented for next execute action
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch8_process_entry_diagnostics_v1.md`

- Environment Repair Lane Batch9 (`ITER-2026-04-07-1222`): PASS_WITH_RISK
  - `make odoo.recreate` blocked by `8069` bind conflict (port already allocated)
  - runtime restore objective remains unresolved pending port-owner resolution
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch9_odoo_recreate_reprobe_evidence_v1.md`

- Environment Repair Lane Batch10 (`ITER-2026-04-07-1223`): PASS
  - port-collision owner path screened (`odoo-paas-web` occupies `0.0.0.0:8069`)
  - remediation options defined for next execute batch
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch10_port_collision_owner_screen_v1.md`

- Environment Repair Lane Batch11 (`ITER-2026-04-07-1224`): PASS
  - external 8069 binder released and `odoo.recreate` succeeds
  - dev odoo now binds 8069; residual issue remains `RemoteDisconnected`
  - evidence: `docs/audit/native/native_runtime_environment_repair_lane_batch11_release_recreate_evidence_v1.md`
