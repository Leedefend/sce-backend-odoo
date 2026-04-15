# Codex Iteration Artifact Governance v1

Status: Active governance runbook

## Objective

Keep the repository focused on long-lived assets:

- Product assets: code, configuration, stable migration scripts, verification scripts, formal models, frontend pages, and formal API contracts.
- Governance assets: frozen architecture rules, allowlists, baselines, runbooks, and small phase acceptance summaries.
- Reproducible assets: files required to rebuild an environment, replay migrations, or enforce verification gates.

High-frequency execution evidence must stay outside normal Git review unless it is promoted into a frozen stage artifact.

## Default Rules

Commit by default:

- `addons/**`
- `frontend/**`
- `scripts/migration/**`
- `scripts/verify/**`
- `Makefile`
- `.github/**`
- `docker/**`
- `docs/architecture/**`
- `docs/runbooks/**`
- `docs/migration_strategy/**`
- `docs/product/**`
- frozen migration policies and frozen validation summaries

Do not commit by default:

- `agent_ops/reports/**`
- `agent_ops/state/task_results/**`
- per-iteration `agent_ops/tasks/ITER-*.yaml`
- `artifacts/migration/*.json`
- `artifacts/migration/*.csv`
- `artifacts/migration/*.md`
- `logs/**`, `tmp/**`, `var/**`
- `.runtime_artifacts/**`, `.runtime_logs/**`, `.runtime_reports/**`
- root-level `TEMP_*.md`

Conditionally commit only after promotion:

- stage replay manifest baselines
- stage acceptance summaries
- Go/No-Go conclusions
- summary CSV or JSON baselines
- one-command rebuild entry documentation

Promotion requires a stable version, stage closure, low rewrite frequency, and clear reuse value after 30 days.

## Runtime Evidence Locations

Use local runtime directories for process evidence:

- `.runtime_artifacts/`
- `.runtime_logs/`
- `.runtime_reports/`

For larger or longer-lived evidence, use external storage such as:

- `/mnt/data/sc-runtime-evidence/`
- `/mnt/data/sc-migration-evidence/`

PR descriptions should reference the evidence path instead of committing the full evidence set.

## Frozen Areas

Frozen or baseline artifacts may be committed under:

- `docs/migration_alignment/frozen/`
- `docs/ops/releases/`
- `artifacts/baselines/`

These paths are reserved for phase outcomes, not per-iteration logs.

## Existing Tracked Noise Cleanup

Cleanup of already tracked process files must be a dedicated batch. Do not mix it with product or migration implementation.

Required sequence:

1. Audit tracked files under `agent_ops/reports`, `agent_ops/state/task_results`, `agent_ops/tasks/ITER-*.yaml`, and `artifacts/migration`.
2. Promote any durable conclusion into `docs/migration_alignment/frozen/`, `docs/ops/releases/`, or `artifacts/baselines/`.
3. Remove high-frequency files from the Git index with `git rm --cached`, preserving local files.
4. Verify ignore behavior and run the declared repository gates.

Do not rewrite history for this cleanup.

## PR Rule

Every PR should contain only:

- real code changes
- necessary formal documentation
- necessary verification or migration scripts
- promoted frozen or baseline evidence

Per-iteration reports, task result JSON, temporary CSV/JSON, and runtime logs belong in runtime evidence storage and should be summarized in the PR body.
