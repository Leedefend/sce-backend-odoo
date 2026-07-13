#!/usr/bin/env bash
set -euo pipefail

MILESTONE='v1.1 Engineering Convergence'

echo "[github-remote] preflight"
gh auth status
gh repo view --json nameWithOwner,viewerPermission
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

echo "[github-remote] milestone"
if gh api "repos/$REPO/milestones?state=all" --jq '.[].title' | grep -Fxq "$MILESTONE"; then
  echo "[github-remote] milestone exists: $MILESTONE"
else
  gh api --method POST "repos/$REPO/milestones" -f title="$MILESTONE" -f description='6-week engineering convergence, production validation, and pilot-readiness milestone.'
fi

echo "[github-remote] labels"
gh label create priority:P0 --color d73a4a --description 'Production blocker: data loss, permission bypass, deployment failure, or core flow unavailable.' --force
gh label create priority:P1 --color f28c28 --description 'Must fix before pilot or release candidate.' --force
gh label create priority:P2 --color fbca04 --description 'Important but can follow P0/P1 work.' --force
gh label create area:backend --color 1d76db --description 'Backend, Odoo model, service, controller, or migration work.' --force
gh label create area:frontend --color 5319e7 --description 'Web frontend, interaction, layout, or browser behavior.' --force
gh label create area:contract --color 006b75 --description 'API contract, schema, intent, or compatibility work.' --force
gh label create area:devops --color 0e8a16 --description 'CI, deployment, environment, backup, or release tooling.' --force
gh label create area:security --color b60205 --description 'Authorization, secrets, upload safety, dependency, or audit work.' --force
gh label create area:data --color 0052cc --description 'Data quality, migration, attachment, or restore work.' --force
gh label create area:docs --color 0075ca --description 'Documentation and governance evidence.' --force
gh label create type:bug --color d73a4a --description 'Defect or regression.' --force
gh label create type:refactor --color c5def5 --description 'Internal restructuring without intended behavior change.' --force
gh label create type:test --color 0e8a16 --description 'Test coverage, validation, or automation.' --force
gh label create type:governance --color 5319e7 --description 'Process, ownership, milestone, or release control.' --force
gh label create status:ready --color 0e8a16 --description 'Ready to implement.' --force
gh label create status:in-progress --color fbca04 --description 'Implementation is active.' --force
gh label create status:blocked --color d73a4a --description 'Blocked by dependency or decision.' --force
gh label create status:verification --color 5319e7 --description 'Implementation complete and waiting for evidence.' --force
gh label create risk:data --color b60205 --description 'Data integrity or migration risk.' --force
gh label create risk:security --color b60205 --description 'Permission, secret, upload, or audit risk.' --force
gh label create risk:release --color f28c28 --description 'Deployment, rollback, or operational risk.' --force
gh label create risk:performance --color fbca04 --description 'Latency, throughput, scale, or resource risk.' --force
gh label create evidence:required --color 5319e7 --description 'Must attach test, screenshot, log, trace, or report evidence.' --force

echo "[github-remote] seed issues"
if gh issue list --state all --search 'EPIC: v1.1 engineering convergence, production validation, and pilot readiness in:title' --json title --jq '.[].title' | grep -Fxq 'EPIC: v1.1 engineering convergence, production validation, and pilot readiness'; then
  echo '[github-remote] issue exists: EPIC: v1.1 engineering convergence, production validation, and pilot readiness'
else
  gh issue create --title 'EPIC: v1.1 engineering convergence, production validation, and pilot readiness' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/epic-v1-1-engineering-convergence-production-validation-and-pilot-readiness.md --label type:governance,priority:P0,evidence:required
fi
if gh issue list --state all --search 'P0-01 Freeze v1.1 Functional Scope in:title' --json title --jq '.[].title' | grep -Fxq 'P0-01 Freeze v1.1 Functional Scope'; then
  echo '[github-remote] issue exists: P0-01 Freeze v1.1 Functional Scope'
else
  gh issue create --title 'P0-01 Freeze v1.1 Functional Scope' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p0-01-freeze-v1-1-functional-scope.md --label type:governance,area:docs,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P0-02 Establish GitHub Milestone and Labels in:title' --json title --jq '.[].title' | grep -Fxq 'P0-02 Establish GitHub Milestone and Labels'; then
  echo '[github-remote] issue exists: P0-02 Establish GitHub Milestone and Labels'
else
  gh issue create --title 'P0-02 Establish GitHub Milestone and Labels' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p0-02-establish-github-milestone-and-labels.md --label type:governance,area:devops,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P0-03 Clean Existing Issues in:title' --json title --jq '.[].title' | grep -Fxq 'P0-03 Clean Existing Issues'; then
  echo '[github-remote] issue exists: P0-03 Clean Existing Issues'
else
  gh issue create --title 'P0-03 Clean Existing Issues' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p0-03-clean-existing-issues.md --label type:governance,area:docs,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P0-04 Establish Engineering Risk Ledger in:title' --json title --jq '.[].title' | grep -Fxq 'P0-04 Establish Engineering Risk Ledger'; then
  echo '[github-remote] issue exists: P0-04 Establish Engineering Risk Ledger'
else
  gh issue create --title 'P0-04 Establish Engineering Risk Ledger' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p0-04-establish-engineering-risk-ledger.md --label type:governance,area:docs,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P0-05 Fix Current Mainline Baseline in:title' --json title --jq '.[].title' | grep -Fxq 'P0-05 Fix Current Mainline Baseline'; then
  echo '[github-remote] issue exists: P0-05 Fix Current Mainline Baseline'
else
  gh issue create --title 'P0-05 Fix Current Mainline Baseline' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p0-05-fix-current-mainline-baseline.md --label type:governance,area:devops,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P0-06 Establish Change Admission Rules in:title' --json title --jq '.[].title' | grep -Fxq 'P0-06 Establish Change Admission Rules'; then
  echo '[github-remote] issue exists: P0-06 Establish Change Admission Rules'
else
  gh issue create --title 'P0-06 Establish Change Admission Rules' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p0-06-establish-change-admission-rules.md --label type:governance,area:devops,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P1-01 Establish Unified CI Workflow in:title' --json title --jq '.[].title' | grep -Fxq 'P1-01 Establish Unified CI Workflow'; then
  echo '[github-remote] issue exists: P1-01 Establish Unified CI Workflow'
else
  gh issue create --title 'P1-01 Establish Unified CI Workflow' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-01-establish-unified-ci-workflow.md --label type:governance,area:devops,type:test,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P1-02 Configure Branch Protection in:title' --json title --jq '.[].title' | grep -Fxq 'P1-02 Configure Branch Protection'; then
  echo '[github-remote] issue exists: P1-02 Configure Branch Protection'
else
  gh issue create --title 'P1-02 Configure Branch Protection' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-02-configure-branch-protection.md --label type:governance,area:devops,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P1-03 Normalize PR and Issue Templates in:title' --json title --jq '.[].title' | grep -Fxq 'P1-03 Normalize PR and Issue Templates'; then
  echo '[github-remote] issue exists: P1-03 Normalize PR and Issue Templates'
else
  gh issue create --title 'P1-03 Normalize PR and Issue Templates' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-03-normalize-pr-and-issue-templates.md --label type:governance,area:docs,priority:P1,evidence:required
fi
if gh issue list --state all --search 'P1-04 Establish Commit Convention in:title' --json title --jq '.[].title' | grep -Fxq 'P1-04 Establish Commit Convention'; then
  echo '[github-remote] issue exists: P1-04 Establish Commit Convention'
else
  gh issue create --title 'P1-04 Establish Commit Convention' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-04-establish-commit-convention.md --label type:governance,area:docs,priority:P1,evidence:required
fi
if gh issue list --state all --search 'P1-05 Establish CODEOWNERS Review in:title' --json title --jq '.[].title' | grep -Fxq 'P1-05 Establish CODEOWNERS Review'; then
  echo '[github-remote] issue exists: P1-05 Establish CODEOWNERS Review'
else
  gh issue create --title 'P1-05 Establish CODEOWNERS Review' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-05-establish-codeowners-review.md --label type:governance,area:devops,priority:P1,evidence:required
fi
if gh issue list --state all --search 'P1-06 Establish Unified Local Quality Entry in:title' --json title --jq '.[].title' | grep -Fxq 'P1-06 Establish Unified Local Quality Entry'; then
  echo '[github-remote] issue exists: P1-06 Establish Unified Local Quality Entry'
else
  gh issue create --title 'P1-06 Establish Unified Local Quality Entry' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-06-establish-unified-local-quality-entry.md --label type:test,area:devops,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'P1-07 Establish CI Failure Taxonomy in:title' --json title --jq '.[].title' | grep -Fxq 'P1-07 Establish CI Failure Taxonomy'; then
  echo '[github-remote] issue exists: P1-07 Establish CI Failure Taxonomy'
else
  gh issue create --title 'P1-07 Establish CI Failure Taxonomy' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p1-07-establish-ci-failure-taxonomy.md --label type:governance,type:test,area:docs,priority:P1,evidence:required
fi
if gh issue list --state all --search 'P2-01 Inventory Existing Validation Assets in:title' --json title --jq '.[].title' | grep -Fxq 'P2-01 Inventory Existing Validation Assets'; then
  echo '[github-remote] issue exists: P2-01 Inventory Existing Validation Assets'
else
  gh issue create --title 'P2-01 Inventory Existing Validation Assets' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/p2-01-inventory-existing-validation-assets.md --label type:test,area:devops,priority:P0,risk:release,evidence:required
fi
if gh issue list --state all --search 'SEC-06 Scan for Secret Leakage in:title' --json title --jq '.[].title' | grep -Fxq 'SEC-06 Scan for Secret Leakage'; then
  echo '[github-remote] issue exists: SEC-06 Scan for Secret Leakage'
else
  gh issue create --title 'SEC-06 Scan for Secret Leakage' --milestone 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/github_issue_bodies/sec-06-scan-for-secret-leakage.md --label type:test,area:security,priority:P0,risk:security,evidence:required
fi

echo "[github-remote] draft PR"
if gh pr list --head topic/v1.1-engineering-convergence --state all --json title --jq '.[].title' | grep -Fxq 'v1.1 Engineering Convergence'; then
  echo '[github-remote] PR exists: v1.1 Engineering Convergence'
else
  gh pr create --draft --base main --head topic/v1.1-engineering-convergence --title 'v1.1 Engineering Convergence' --body-file docs/engineering_convergence/pr_v1_1_engineering_convergence.md
fi

echo "[github-remote] branch protection remains a GitHub settings/admin step; see github_governance_runbook.md"
