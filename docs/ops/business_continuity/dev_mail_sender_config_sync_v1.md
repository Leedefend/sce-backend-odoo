# Dev Mail Sender Config Sync v1

## Purpose

Payment submit reached mail notification processing but failed because the
dev/demo runtime had no sender email facts.

This batch configures deterministic non-production sender values in `sc_demo`.

## Values

- `mail.default.from`: `noreply@smartconstruction.local`
- company email: `noreply@smartconstruction.local`
- `sc_fx_finance` email: `sc_fx_finance@smartconstruction.local`
- `sc_fx_finance` partner email: `sc_fx_finance@smartconstruction.local`

## Boundaries

This batch does not configure real production SMTP and does not change payment,
approval, funding, settlement, account, ACL, or frontend semantics.

## Evidence

The script writes:

- `artifacts/ops/dev_mail_sender_config_sync_result_v1.json`
- `artifacts/ops/dev_mail_sender_config_sync_rollback_v1.json`

## 2026-04-17 Execution

Write mode set:

- `mail.default.from`: `noreply@smartconstruction.local`
- company email count updated: 1
- `sc_fx_finance` email: `sc_fx_finance@smartconstruction.local`
- `sc_fx_finance` partner email: `sc_fx_finance@smartconstruction.local`

Post-check confirmed the values are stable and no further writes are needed.

Rollback-only payment submit verification passed:

- payment created by `sc_fx_finance`: yes
- payment submit result state: `submit`
- verification payment record was rolled back
