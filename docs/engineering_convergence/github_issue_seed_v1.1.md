# v1.1 GitHub Issue Seed

Milestone: `v1.1 Engineering Convergence`

Use these issues to bootstrap the milestone. Each issue must be created under the milestone and assigned before execution.

## EPIC: v1.1 engineering convergence, production validation, and pilot readiness

Labels: `type:governance`, `priority:P0`, `evidence:required`

### Problem and Goal

The project needs a controlled 6-week convergence path before real construction project pilot usage.

### Scope

Coordinate Phase 0 through Phase 6: scope freeze, GitHub governance, quality gates, test layering, E2E business-chain validation, architecture governance, security, performance, disaster recovery, and pilot readiness.

### Non-Scope

Unapproved large product features and speculative UI redesigns.

### Acceptance Criteria

- All child issues are linked to this epic.
- P0 issues are closed before pilot.
- Required evidence exists for every phase exit.
- Main branch changes only land through PR and quality gate.

## P0-01 Freeze v1.1 Functional Scope

Labels: `type:governance`, `area:docs`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

Feature scope must be frozen to stop uncontrolled expansion during convergence.

### Scope

Approve `docs/engineering_convergence/release_scope_v1.1.md` and classify every item as included, excluded, or deferred.

### Non-Scope

New unapproved product features.

### Acceptance Criteria

- Scope file is reviewed by product and technical owner.
- Deferred items have explicit follow-up handling.
- P0 definition is accepted by the team.

## P0-02 Establish GitHub Milestone and Labels

Labels: `type:governance`, `area:devops`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

Work must be traceable through a single milestone with normalized labels.

### Scope

Create milestone `v1.1 Engineering Convergence` and labels from `github_labels.tsv`.

### Non-Scope

Issue cleanup and branch protection, tracked separately.

### Acceptance Criteria

- Milestone exists in GitHub.
- Required labels exist and match the runbook.
- Evidence link or screenshot is attached.

## P0-03 Clean Existing Issues

Labels: `type:governance`, `area:docs`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

Existing issues must be deduplicated and converted into executable work.

### Scope

Close test-only issues, merge duplicates, classify valid work by priority, area, owner, and acceptance criteria.

### Non-Scope

Implementing the issue contents.

### Acceptance Criteria

- Every open issue has milestone, labels, owner, priority, and acceptance criteria.
- Duplicate issues are linked before closing.
- Invalid test issues are closed.

## P0-04 Establish Engineering Risk Ledger

Labels: `type:governance`, `area:docs`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

Critical risks must be visible, owned, and reviewed during convergence.

### Scope

Maintain `engineering_risk_ledger.md`.

### Non-Scope

Resolving every listed risk in this issue.

### Acceptance Criteria

- Every risk has severity, owner, deadline, mitigation, and evidence.
- P0/P1 risks have follow-up issues.

## P0-05 Fix Current Mainline Baseline

Labels: `type:governance`, `area:devops`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

The team needs one trusted baseline for release and rollback.

### Scope

Fill `baseline_report_v1.1.md` with commit, DB, module, artifact, image, filestore, and known-issue evidence.

### Non-Scope

Production upgrade execution.

### Acceptance Criteria

- Baseline report is complete.
- Tag is created only after branch protection and issue governance are active.
- Known P0/P1 issues are linked.

## P0-06 Establish Change Admission Rules

Labels: `type:governance`, `area:devops`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

Main branch must reject uncontrolled changes.

### Scope

Apply PR template, issue templates, CODEOWNERS, branch protection, and required quality checks.

### Non-Scope

Team staffing changes.

### Acceptance Criteria

- `main` direct push is blocked.
- PR review is required.
- Required checks include the v1.1 quality gate.
- CODEOWNERS review is enforced.

## P1-01 Establish Unified CI Workflow

Labels: `type:governance`, `area:devops`, `type:test`, `priority:P0`, `risk:release`, `evidence:required`

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

## P1-02 Configure Branch Protection

Labels: `type:governance`, `area:devops`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

Protected branch policy must be enforced by GitHub.

### Scope

Configure the `main` branch protection settings listed in `github_governance_runbook.md`.

### Non-Scope

Repository permission redesign beyond `main`.

### Acceptance Criteria

- Direct push to `main` is blocked.
- Required checks and review rules are active.
- Evidence screenshot or settings export is attached.

## P1-03 Normalize PR and Issue Templates

Labels: `type:governance`, `area:docs`, `priority:P1`, `evidence:required`

### Problem and Goal

PRs and issues must collect enough evidence for release decisions.

### Scope

Use `.github/pull_request_template.md` and `.github/ISSUE_TEMPLATE/*`.

### Non-Scope

Historical issue rewriting beyond P0/P1 cleanup.

### Acceptance Criteria

- New PRs require issue link, scope, tests, migration, permissions, rollback, and evidence.
- Blank issues are disabled.

## P1-04 Establish Commit Convention

Labels: `type:governance`, `area:docs`, `priority:P1`, `evidence:required`

### Problem and Goal

Commit history must support release audit and rollback.

### Scope

Document `feat/fix/refactor/test/docs/chore` convention and require concise scope.

### Non-Scope

Rewriting existing history.

### Acceptance Criteria

- Convention is documented.
- PR template asks for change category.

## P1-05 Establish CODEOWNERS Review

Labels: `type:governance`, `area:devops`, `priority:P1`, `evidence:required`

### Problem and Goal

Domain-sensitive files need explicit reviewers.

### Scope

Maintain `.github/CODEOWNERS`.

### Non-Scope

Final team assignment beyond current repository owner placeholder.

### Acceptance Criteria

- Core, frontend, devops, smart_core, construction domains, and migration tooling have owners.
- GitHub enforces CODEOWNERS review.

## P1-06 Establish Unified Local Quality Entry

Labels: `type:test`, `area:devops`, `priority:P0`, `risk:release`, `evidence:required`

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

## P1-07 Establish CI Failure Taxonomy

Labels: `type:governance`, `type:test`, `area:docs`, `priority:P1`, `evidence:required`

### Problem and Goal

CI failures must be classified consistently to avoid masking real defects.

### Scope

Maintain `ci_failure_taxonomy.md`.

### Non-Scope

Resolving every flaky test.

### Acceptance Criteria

- Failure categories include code defect, environment issue, flaky test, and data issue.
- Every CI failure gets one category before closure.

## P2-01 Inventory Existing Validation Assets

Labels: `type:test`, `area:devops`, `priority:P0`, `risk:release`, `evidence:required`

### Problem and Goal

The project needs a complete map of validation scripts before restructuring tests.

### Scope

Maintain `test_inventory.csv` with script path, purpose, layer, runtime class, owner, and status.

### Non-Scope

Deleting or rewriting all tests.

### Acceptance Criteria

- All known CI, guard, audit, E2E, and contract scripts are classified.
- Duplicates and stale scripts are marked for follow-up.

## SEC-06 Scan for Secret Leakage

Labels: `type:test`, `area:security`, `priority:P0`, `risk:security`, `evidence:required`

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
