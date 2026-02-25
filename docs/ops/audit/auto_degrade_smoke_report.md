# Auto Degrade Smoke Report

- status: PASS
- triggered: true
- action_taken: `rollback_pinned`
- scene_channel: `stable`
- scene_contract_ref: `stable/PINNED.json`
- has_injected_error: false

## Checks
- system_init_ok: PASS
- auto_degrade_payload_present: PASS
- critical_injection_detectable: PASS
- stable_channel_when_triggered: PASS
- stable_ref_when_triggered: PASS
- action_taken_when_triggered: PASS
