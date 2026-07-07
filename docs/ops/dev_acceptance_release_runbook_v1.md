# Dev Acceptance Release Runbook v1

## Scope

This runbook standardizes the dev acceptance release path for `sc_demo`.
It covers uploaded backup validation, running-service alignment, frontend static
publication, and a minimal real-user acceptance probe.

It does not automate destructive database restore. Restore remains an
operator-supervised step because it replaces the running acceptance database and
filestore.

## Layer Target / Module / Reason

- Layer Target: Ops / Release
- Module: dev acceptance release flow (`sc_demo`)
- Reason: make the upload-to-acceptance path repeatable and verifiable.

## Inputs

- Backup directory containing:
  - `SHA256SUMS`
  - `<db>_<timestamp>.dump`
  - `<db>_filestore_<timestamp>.tgz`
- Target DB: `sc_demo`
- Dev env file: `.env.dev`
- Public dev URL: `http://<host>:18081/` unless nginx is deliberately rebound.

## Required Sequence

1. Validate the uploaded backup package:

   ```bash
   ACCEPTANCE_BACKUP_DIR=/tmp/20260512T125816 \
   ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
   make verify.dev.acceptance.release
   ```

2. If restore is required, perform it only after explicit operator approval.
   Use the container-native restore path and keep DB and filestore paired from
   the same uploaded package.

3. Rebuild the served frontend static bundle for the target DB:

   ```bash
   ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
   make verify.frontend.build
   ```

4. Run the publication acceptance probe:

   ```bash
   ACCEPTANCE_BACKUP_DIR=/tmp/20260512T125816 \
   ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \
   ACCEPTANCE_LOGIN=wutao ACCEPTANCE_PASSWORD='<password>' \
   ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
   make release.dev.acceptance.publish
   ```

   On the daily development runtime server, use the stricter topology-locked
   entrypoint instead:

   ```bash
   ACCEPTANCE_BACKUP_DIR=/tmp/20260512T125816 \
   ACCEPTANCE_BASE_URL=http://127.0.0.1:18081 \
   ACCEPTANCE_LOGIN=wutao ACCEPTANCE_PASSWORD='<password>' \
   ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo \
   make release.daily_dev.acceptance.publish
   ```

   This target first runs `env.matrix.check` and
   `verify.daily_dev.runtime_repo.clean`, so the acceptance publication cannot
   run from the wrong server directory or a dirty runtime repository.
   It also runs `verify.daily_dev.acceptance.env.guard`, which rejects anything
   other than `ENV=dev`, `ENV_FILE=.env.dev`, `DB_NAME=sc_demo`, and
   `ACCEPTANCE_BASE_URL=http://127.0.0.1:18081`.

## Acceptance Criteria

- `SHA256SUMS` passes.
- `pg_restore -l` identifies the expected DB name.
- Filestore archive contains the expected DB directory prefix.
- `/` serves the latest `frontend/apps/web/dist/index.html`.
- The served `index-*.js` contains `sc_demo` and its default app env is `dev`.
  Historical or guard-list tokens such as `sc_prod_sim` may still exist in the
  bundle, but they must not be the default runtime target.
- `/api/v1/intent?db=sc_demo` returns `204` for `OPTIONS` and `405` for `GET`.
- Optional real-user probe can authenticate and run `system.init`.

## Evidence

The probe writes:

```text
artifacts/backend/dev_acceptance_release_probe.json
```

Keep this artifact with the release evidence. It records backup validation,
frontend publication checks, API checks, and optional login/system.init results.

## Rollback

- Frontend rollback: rebuild `frontend/apps/web/dist` using the previous
  intended `ENV`, `DB_NAME`, `VITE_APP_ENV`, and `VITE_ODOO_DB`.
- Database rollback: restore the prior database dump and matching filestore
  package as a pair.
- Proxy rollback: restore the previous nginx port/DB-lock configuration and
  verify `/api/` plus `/websocket` carry the intended DB lock headers.

## Stop Conditions

- Backup checksum fails.
- Dump DB name does not match the target DB.
- Filestore archive is missing or does not contain the target DB prefix.
- Served frontend bundle defaults to the wrong app env or runtime DB.
- `system.init` fails for the named acceptance user.
