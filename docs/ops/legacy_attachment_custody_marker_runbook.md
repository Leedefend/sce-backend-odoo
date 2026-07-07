# Legacy Attachment Custody Marker Runbook

## Purpose

Legacy URL attachments must explicitly carry the custody boundary marker
`binary_embedded=false` in `ir.attachment.description`.

The marker means the new system preserves a durable legacy file reference through
`legacy-file://` or `legacy-file-id://`, while the binary bytes are not embedded
inside the Odoo database record.

## Detect

Non-production:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make history.attachment.custody.probe
```

Production read-only verification:

```bash
PROD_READONLY_VERIFY=1 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod make history.attachment.custody.probe.prod
```

The target decision is:

```text
history_attachment_custody_ready
```

If the probe reports `legacy_url_attachment_boundary_marker_gap`, run the
marker backfill.

## Backfill

Dry-run by limiting writes through the script environment:

```bash
LEGACY_ATTACHMENT_CUSTODY_MARKER_APPLY=0 \
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
make legacy_attachment.custody_marker.backfill
```

Apply in non-production:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
make legacy_attachment.custody_marker.backfill
```

Apply in production:

```bash
PROD_DANGER=1 \
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod \
make legacy_attachment.custody_marker.backfill.prod
```

Optional bounded batch:

```bash
LEGACY_ATTACHMENT_CUSTODY_MARKER_LIMIT=10000 \
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
make legacy_attachment.custody_marker.backfill
```

## Verify

Run the custody probe again. The marker gap count must return to zero and the
decision must be `history_attachment_custody_ready`.

The backfill is idempotent: once all legacy URL attachments have the marker,
subsequent runs report `candidate_count_before=0` and `updated_count=0`.
