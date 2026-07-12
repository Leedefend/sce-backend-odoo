### Problem and Goal

Every PR must execute the same quality gate as local development.

### Scope

Use `.github/workflows/v1_1_quality_gate.yml` and `make ci`.

### Non-Scope

Full nightly E2E matrix.

### Acceptance Criteria

- Workflow runs on PR to `main`.
- Local `make ci` and GitHub CI execute the same gate.
- Failure output is visible in PR checks.

---
Source: `docs/engineering_convergence/github_issue_seed_v1.1.md`
