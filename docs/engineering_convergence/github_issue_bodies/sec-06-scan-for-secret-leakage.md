### Problem and Goal

The repository and CI must detect high-confidence secret leakage.

### Scope

Run `make security.secrets.scan` locally and in CI.

### Non-Scope

Full enterprise secret management redesign.

### Acceptance Criteria

- High-confidence token patterns fail the gate.
- False positives are reviewed before allowlisting.
- Current repository scan passes.

---
Source: `docs/engineering_convergence/github_issue_seed_v1.1.md`
