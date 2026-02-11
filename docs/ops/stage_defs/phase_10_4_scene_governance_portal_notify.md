# Phase 10.4 — Portal Governance Actions + Health API Hardening + Notification Loop

## Scope
- Portal can execute governance actions without Odoo backend console.
- `scene.health` adds mode/pagination/time-window contract controls.
- Auto-degrade emits notification loop with traceable evidence.

## Governance Intents
- `scene.governance.set_channel`
- `scene.governance.rollback`
- `scene.governance.pin_stable`
- `scene.governance.export_contract`

Contract requirements:
- `reason` is mandatory.
- Response includes `action`, `from_channel`, `to_channel`, `trace_id`.
- Governance/audit logs must be written.

## Health API v1
Intent: `scene.health`

Parameters:
- `mode=summary|full` (default `summary`)
- `limit` / `offset` (applies in `full`)
- `since` (ISO timestamp, used as detail window filter when timestamps are available)

Rules:
- `summary` mode does not return `details`.
- `full` mode returns paged `details`.
- Output keeps `summary`, `auto_degrade`, `last_updated_at`, `trace_id`.

## Auto-Degrade Notification Policy
Config keys:
- `sc.scene.auto_degrade.notify.enabled` (default `true`)
- `sc.scene.auto_degrade.notify.channels` (csv: `email`, `internal`, `webhook`)

Minimum implemented channels:
- `internal`: write `SCENE_AUTO_DEGRADE_NOTIFY` to `sc.audit.log`.
- `webhook`: reserved, writes placeholder audit event.
- `email`: best effort via `mail.mail` when user email is available.

Notification payload fields include:
- `trace_id`
- `reason_codes`
- `action_taken`
- `from_channel`
- `to_channel`
- `company_id`
- `suggestion`

## Verify Commands
- `make verify.portal.scene_governance_action_smoke.container`
- `make verify.portal.scene_health_pagination_smoke.container`
- `make verify.portal.scene_auto_degrade_notify_smoke.container`
- Strict evidence mode:
  - `make verify.portal.scene_governance_action_strict.container`
  - `make verify.portal.scene_auto_degrade_notify_strict.container`
  - `make verify.portal.scene_observability_strict.container`

## Gate Integration
Included in:
- `make verify.portal.ui.v0_8.semantic.container`

## Artifacts
- Governance action:
  - `artifacts/codex/portal-scene-governance-action-v10_4/<timestamp>/`
- Health pagination:
  - `artifacts/codex/portal-scene-health-pagination-v10_4/<timestamp>/`
- Auto-degrade notify:
  - `artifacts/codex/portal-scene-auto-degrade-notify-v10_4/<timestamp>/`
