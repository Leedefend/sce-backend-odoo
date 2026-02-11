# Scene Observability Strict Troubleshooting

This guide explains common failures when running strict scene observability checks.

## Quick Commands
- Preflight (non-blocking):  
  `make verify.portal.scene_observability_preflight_smoke.container DB_NAME=sc_demo`
- Preflight (strict):  
  `make verify.portal.scene_observability_preflight.container DB_NAME=sc_demo`
- Full strict aggregate:  
  `make verify.portal.scene_observability_strict.container DB_NAME=sc_demo`

## Common Failure Patterns

### `governance log model unavailable: sc.scene.governance.log, sc.audit.log`
- Meaning: strict mode requires governance/audit evidence models but neither can be queried.
- Action:
  1. Run strict preflight to confirm model availability.
  2. Check module install/upgrade status for scene governance/audit dependencies.
  3. Re-run strict aggregate after dependencies are available.

### `notify audit model unavailable: sc.audit.log`
- Meaning: strict notify evidence is required but `sc.audit.log` is unavailable.
- Action:
  1. Verify strict preflight output (`preflight.log`) under artifacts.
  2. Fix audit model availability.
  3. Re-run `verify.portal.scene_auto_degrade_notify_strict.container`.

## Artifact Paths
- Preflight:  
  `artifacts/codex/portal-scene-observability-preflight-v10_4/<timestamp>/`
- Governance action:  
  `artifacts/codex/portal-scene-governance-action-v10_4/<timestamp>/`
- Auto-degrade notify:  
  `artifacts/codex/portal-scene-auto-degrade-notify-v10_4/<timestamp>/`

## Reading Preflight Report
- File: `preflight.log`
- Key fields:
  - `required_any.governance`: acceptable governance evidence models
  - `required_any.notify`: acceptable notify evidence models
  - `governance.available` / `notify.available`: models available in current env
  - `governance.missing` / `notify.missing`: missing models in current env

## Readiness Report
- Generate:
  - `make verify.portal.scene_observability_preflight.report`
- Output:
  - `artifacts/scene_observability_preflight_readiness.latest.json`
- Key fields:
  - `readiness.strict_ready`
  - `readiness.strict_failure_reasons`
