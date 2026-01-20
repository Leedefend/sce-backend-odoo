# Codex Rules v1.0

## Scope

- P0/P1/P2/P3 R&D collaboration rules and evidence delivery.
- Gate evidence requirements for tp08/p2/p3.
- Tag and release discipline.
- Scripted verification (preflight + policy checks).

## Non-scope

- Frontend execute_button envelope changes (unless phase explicitly requires).
- UI feature delivery.

## Branch & Commit Rules

- Every task must start on a feature branch; no direct changes on `main`.
- If a sprint requires a single commit, do not append commits; amend or restart branch.

## Database Policy (Hard Constraint)

Allowed DB names (default whitelist):
- sc_demo: gates/audit (tp08)
- sc_p2: P2 runtime/smoke
- sc_p3: P3 runtime/smoke

Forbidden:
- Creating new DB names per task (e.g. sc_xxx_random).

Allowed exceptions:
- Must be explicitly stated in task instructions.
- Must include DB name, reason, lifecycle, and cleanup command.

## Evidence Output (Mandatory)

Each delivery must include:
- branch + sha
- `git show --name-status -1`
- gate tail (tp08 / p2.smoke / p3.smoke / p3.audit as required)
- at least one shell/script verification output
- `git status` clean

## Generated Artifacts & Ignore Rules

- `docs/audit/*.csv` are generated; must be restored and never committed.
- If new scripts produce output, either write to `tmp/` or add to `.gitignore` and document in SOP.
