### Problem and Goal

Local and CI validation must not diverge.

### Scope

Maintain `make ci`, `make test.unit`, `make test.odoo.integration`, `make test.contract`, `make test.e2e`, and `make test.all`.

### Non-Scope

Making every existing guard mandatory on PR.

### Acceptance Criteria

- `make ci` passes locally.
- CI calls `make ci`.
- Slow gates remain available through explicit targets.

---
Source: `docs/engineering_convergence/github_issue_seed_v1.1.md`
