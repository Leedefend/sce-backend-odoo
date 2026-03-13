# Agent Instructions

## Codex Execution Policy
- Always follow `docs/ops/codex_execution_allowlist.md` for all execution and validation steps.
- If a requested action falls outside the allowlist, stop and ask for confirmation before proceeding.

## Architecture Guard
- Always follow `ARCHITECTURE_GUARD.md` and `docs/architecture/ai_development_guard.md` before making code changes.
- For frontend page work, always follow `docs/architecture/native_view_reuse_frontend_spec_v1.md`.
- For every implementation task, explicitly identify `Layer Target`, `Module`, and `Reason` before coding.
