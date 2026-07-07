# Daily Dev Runtime Repository Policy v1

## Purpose

The daily development runtime repository is the deployable working tree for
`ENV=dev`, `.env.dev`, and `DB_NAME=sc_demo`. It must stay aligned with
`origin/main` so upgrades can be fast-forwarded and verified without preserving
ad hoc local state.

## Runtime Repository

- Path: `/opt/projects/repos/sce-backend-odoo`
- Required branch: `main`
- Required state: clean working tree, aligned with upstream
- Allowed operations: deploy, module upgrade, restart, read-only inspection
- Forbidden operations: exploratory edits, replay output generation, migration
  asset generation, long-running validation that writes into the repository

Before every upgrade or publish step, run:

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make verify.daily_dev.runtime_repo.clean
```

## Scratch Work

Temporary development, migration replay, attachment probes, and acceptance runs
must use a separate worktree or scratch directory, for example:

```bash
mkdir -p /opt/projects/scratch/worktrees
cd /opt/projects/repos/sce-backend-odoo
git worktree add /opt/projects/scratch/worktrees/<topic> main
cd /opt/projects/scratch/worktrees/<topic>
```

Generated outputs must stay outside the runtime repository, preferably under:

- `/opt/projects/artifacts`
- `/opt/projects/backups`
- `/opt/projects/scratch`

If a scratch result becomes product code, move it through the normal local
branch, review, validation, merge, and deploy flow. Do not apply scratch
changes directly to the runtime repository.

## Closeout Rule

If local state appears in the runtime repository, stop deployment and classify
it before proceeding:

- tracked code changes: archive to a named branch or move to a topic branch
- untracked artifacts: move to `/opt/projects/backups/<timestamp>/untracked`
- generated reports: keep outside runtime repo unless intentionally committed
- stale temporary refs: delete after archive/report is confirmed

The runtime repository can be upgraded only after the guard passes again.
