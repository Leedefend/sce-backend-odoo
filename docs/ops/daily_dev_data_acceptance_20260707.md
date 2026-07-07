# Daily Dev Data Acceptance - 2026-07-07

## Scope

- Environment: daily development server `sc-root`
- Database: `sc_demo`
- Repository path: `/opt/sce/sce-backend-odoo`
- Compose project: `sc-backend-odoo-dev`

This record covers data-only remediation and verification. The remote daily
development repository has unrelated dirty frontend/mobile changes and was not
pulled, reset, or modified.

## Backup

Before data remediation, a database backup was created on the daily development
server:

- Path: `/opt/sce/backups/dev_data_fix_20260707T075549+0800`
- Dump: `sc_demo_before_p0_param_fix.dump`
- SHA256: `4423b4a80f1a4d0ff456ebaed2b05b4e4badb6e38e548fa6929d854bea44a124`

## Data Changes

1. Restored required platform runtime parameters for P0:
   - `sc.login.custom_enabled=1`
   - `sc.workbench.enabled=1`
   - `sc.workbench.default_action_xmlid=smart_construction_core.action_sc_project_workbench`
   - `sc.sidebar.overview_enabled=1`
   - `sc.sidebar.overview_menu_ids=265`
   - `sc.login.env=dev`

2. Restored missing minimum dictionary rows:
   - `doc_type`: 5 rows
   - `doc_subtype`: 1 row
   - `fee_type`: 8 rows
   - `tax_type`: 4 rows
   - `cost_item`: 3 rows

3. Reconciled one menu action drift against production:
   - XMLID: `smart_construction_core.menu_scbs55_user_acceptance_450_供货合同分析`
   - Before: `ir.actions.act_window,900` -> `sc.legacy.supplier.contract.pricing.fact`
   - After: `ir.actions.act_window,912` -> `sc.legacy.direct.acceptance.fact`

## Verification

- `make verify.baseline`: PASS
- `make verify.p0`: PASS
- `history_business_usable_probe.py`: PASS, `history_business_usable_ready`
- `formal_business_backfill_audit_probe.py`: PASS, `formal_business_backfill_ready`
- `non_demo_data_contamination_guard.py` in forced mode: PASS
- Containers: db, nginx, odoo, redis healthy

## Attachment State

Daily development attachment index volume:

- `sc_legacy_file_index`: 174,496 active rows
- `BASE_SYSTEM_FILE`: 125,213 rows
- `T_BILL_FILE`: 49,148 rows
- `online_old_scbsly:online_file_api`: 135 rows
- `ir_attachment legacy-file://`: 475,595 rows
- `ir_attachment legacy-file-id://`: 132,015 rows

Sample completeness audit:

- `sc_legacy_file_index` sample: 5,000 rows
- Local file OK: 4,995
- Missing local file: 5
- Missing examples are all `BASE_SYSTEM_FILE`
- `legacy-file://` sample: 5,000 rows
- Legacy URL local file OK: 5,000
- Legacy URL missing local file: 0

Additional attachment custody remediation:

- Added missing `binary_embedded=false` custody marker to 588,073 legacy URL
  attachments.
- Re-ran `history_attachment_custody_probe.py`: PASS,
  `history_attachment_custody_ready`, `gap_count=0`.
- Re-ran `make verify.p0`: PASS.

Production parity follow-up:

- Production had the same custody marker class of issue on 4 legacy URL
  attachments.
- Saved a pre-fix CSV snapshot inside the production DB container:
  `/tmp/prod_ir_attachment_marker_gap_20260707.csv`
- Snapshot SHA256:
  `9b803c6b6303cc6a9e20411e0ff07bfc4b2afb4114496f85ca08202a12bea3e9`
- Added `binary_embedded=false` marker to those 4 production rows.
- Re-ran production marker gap SQL: `0`.
- Re-ran production `history_attachment_custody_probe.py`: PASS,
  `history_attachment_custody_ready`, `gap_count=0`.

Process hardening:

- Added reusable marker backfill script:
  `scripts/migration/legacy_attachment_custody_marker_backfill.py`
- Added Make targets:
  - `legacy_attachment.custody_marker.backfill`
  - `legacy_attachment.custody_marker.backfill.prod`
  - `history.attachment.custody.probe.prod`
- Added runbook:
  `docs/ops/legacy_attachment_custody_marker_runbook.md`
- Verified the new script with dry-runs against daily development and
  production after remediation; both reported `candidate_count_before=0` and
  `updated_count=0`.

Targeted `BASE_SYSTEM_FILE` mirror attempt:

- Scope: first 5,000 `BASE_SYSTEM_FILE` rows.
- Already local OK: 4,995.
- Download failed: 5.
- Failure mode: old online source returned HTTP 500 for all 5 missing files.
- The same 5 files were not present on the production server local attachment
  roots, so they cannot be recovered by syncing from production.

Conclusion: daily development business data is usable after remediation. The
remaining known gap is physical file completeness for a small number of
`BASE_SYSTEM_FILE` entries whose old online source currently returns HTTP 500.
This is the same class of issue as the production attachment backfill track and
should be handled by the attachment mirror/backfill process or old-source
recovery, rather than by business data restructuring.
