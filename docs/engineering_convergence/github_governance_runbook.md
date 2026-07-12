# GitHub Governance Runbook for v1.1

Milestone: `v1.1 Engineering Convergence`

This runbook is the remote execution checklist for Phase 0 and Phase 1. It is required because repository state must be auditable outside local code changes.

## Required Repository Settings

### Branch Protection

Protect `main` with these rules:

- Require a pull request before merging.
- Require at least one approving review.
- Require CODEOWNERS review when owned files change.
- Require status checks to pass before merging.
- Require the `v1.1 quality gate / quality_gate` workflow check on the
  dedicated self-hosted CI runner.
- Require branches to be up to date before merging.
- Block force pushes.
- Block branch deletion.
- Restrict direct pushes to release administrators only, preferably nobody.

The dedicated CI runner is `ci-1-95-2-123` on server `1.95.2.123` with labels
`self-hosted`, `huawei`, `ubuntu22`, `ci`, and `docker`. Heavy Docker/Odoo
stage workflows must target this runner class.

### Milestone

Create milestone:

- Title: `v1.1 Engineering Convergence`
- Duration: 6 weeks from kickoff date.
- Exit condition: all P0 issues closed, quality gate mandatory, core evidence linked.

### Labels

Create or normalize these labels:

- `priority:P0`, `priority:P1`, `priority:P2`
- `area:backend`, `area:frontend`, `area:contract`, `area:devops`, `area:security`, `area:data`, `area:docs`
- `type:bug`, `type:refactor`, `type:test`, `type:governance`
- `status:ready`, `status:in-progress`, `status:blocked`, `status:verification`
- `risk:data`, `risk:security`, `risk:release`, `risk:performance`
- `evidence:required`

## Creation Commands

Run after `gh auth login` with repository admin permission:

```bash
gh milestone create "v1.1 Engineering Convergence" \
  --description "6-week engineering convergence, production validation, and pilot-readiness milestone."

while read -r label color description; do
  gh label create "$label" --color "$color" --description "$description" --force
done < docs/engineering_convergence/github_labels.tsv
```

Issue creation should use `docs/engineering_convergence/github_issue_seed_v1.1.md` as the source of truth.

## Evidence Rules

Every issue must contain:

- Problem and goal.
- Scope.
- Explicit non-scope.
- Implementation plan.
- Acceptance criteria.
- Test requirements.
- Data migration impact.
- Security and permission impact.
- Rollback plan.
- Delivery evidence.

Every PR must link one or more issues and include:

- Test command output or CI link.
- Migration notes.
- Rollback notes.
- Screenshots or traces when user-visible behavior changes.

## Review Identity Rule

`Leedefend` is the repository CODEOWNER for this convergence baseline. A CODEOWNER
approval only counts when the approving account is not the pull-request author.

For protected `main` changes:

- The PR author and required CODEOWNER reviewer must be different GitHub accounts.
- Commit author metadata does not change the PR author and does not satisfy review separation.
- Automation or collaborators may prepare and open PRs, but `Leedefend` remains the required owner reviewer unless CODEOWNERS is intentionally changed in a separate governance PR.
- If a PR was opened by `Leedefend`, it can still run CI and collect evidence, but it cannot satisfy the required `Leedefend` approval by self-review. Reopen or recreate it from a non-owner author account when strict branch protection is being exercised.

## Phase 0 Exit Checklist

- `release_scope_v1.1.md` approved.
- `engineering_risk_ledger.md` reviewed.
- `baseline_report_v1.1.md` filled with runtime evidence.
- Milestone exists.
- Labels exist.
- Seed issues created or explicitly deferred.
- Branch protection enabled on `main`.
- `make ci` passes locally and in GitHub Actions.
