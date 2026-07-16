# Legacy credential incident v1

Status: `ACCEPTED_UNTIL_LEGACY_SYSTEM_RETIREMENT` (not `CLOSED`)

Repository baseline: `859dae5bf0511facfa5ad95d8d93693ad40ffe75`

## Manual prerequisite

The delivery owner has accepted temporary continued use under this boundary:

```text
LEGACY_SYSTEM_STILL_REQUIRED=true
LEGACY_CREDENTIAL_ROTATION_DEFERRED=true
LEGACY_SYSTEM_ALLOWED_USE=data_completion_and_migration_only
LEGACY_SYSTEM_RETIREMENT_DEADLINE=pending formal cutover date
RISK_ACCEPTED_BY=Delivery owner
```

This acceptance does not close the incident or assert credential/session
revocation. Old credentials are not tested, replacement credentials are not
requested, and production users/databases remain out of scope. Legacy access
is limited to the controlled management network and data completion/migration.

## Fingerprint inventory

`config/security/legacy_credential_fingerprints.json` contains the 15
fingerprints produced by the earlier PR-body candidate scan. It records only
fingerprint IDs, source categories, PR numbers and disposition. The catalog
also contains three separately confirmed repository-history incident
fingerprints from the 2026-07-15 incident record. It contains no raw value,
length, prefix, suffix or reversible encoding.

The 15 PR fingerprints were replayed against the current tree and PR bodies.
The classifier separates confirmed migration assignments from test fixtures,
normal text and unresolved candidates. A regular-expression match is not
treated as a live credential by itself.

## Branch-size audit

The SEC-POST-01 checkpoint initially changed 14 files with 1,710 additions and
1,233 deletions. Its changed-line composition was:

| Category | Changed lines |
| --- | ---: |
| Production code | 0 |
| CI/Make wiring | 13 |
| Scanner implementation | 253 |
| Scanner test fixture/code | 77 |
| Generated inventory/reports | 2,438 |
| Security catalog, report and documentation | 162 |

The generated churn came from inserting two new script assets into a
sequential-ID inventory, which renumbered nearly the entire report. The
standalone legacy scanner and test also duplicated the existing secret scanner.
SEC-POST-01R merged legacy handling into `secret_scan.py`, removed both extra
scripts and restored the generated inventory to its mainline form. The final
branch has nine changed files and no generated inventory churn, no PR-body
copy, no raw match context and no reversible credential characteristic.

## Current-tree remediation

The new guard found one current Markdown assignment matching confirmed history
fingerprint `HC-003`. It was replaced in place with
`<REVOKED_LEGACY_SECRET>` without printing or copying the value. A repeat scan
found zero blocking current-tree matches.

| Measure | Result |
| --- | ---: |
| Target text files scanned | 8,553 |
| Confirmed current-tree exposures before cleanup | 1 |
| Confirmed current-tree exposures after cleanup | 0 |
| Current-tree replacements | 1 |
| Secret values recorded | 0 |

## GitHub metadata inventory

The offline export contained 998 PR bodies. Nineteen PRs were minimally edited
to replace 47 confirmed assignments; the affected PRs are #245–#248, #259–#263,
#265–#273 and #788. PR #269 and #788 each contained four replacements. Every
edited body was re-read, confirmed fingerprints were absent, placeholders were
present and the PR remained closed/open exactly as before.

The remaining 47 candidate matches are classified as 25 `TEST_FIXTURE`, 11
`NORMAL_TEXT` and 11 `UNRESOLVED`. Unresolved items are owned by the Security
owner with deadline at the formal legacy cutover date; they were not modified.
The prior global comment scan found zero issue-comment and zero review-comment
matches, so comments were not changed.

## Guard contract

- `make security.secret_scan` runs the existing high-confidence worktree scan.
- `make security.legacy_credential_guard` requires the fingerprint catalog,
  scans the worktree and additions relative to `origin/main`, and fails on any
  confirmed history fingerprint.
- `scripts/ci/secret_scan.py --legacy-only --pr-jsonl <offline-export>` adds an
  offline PR-body scan without contacting GitHub or writing metadata.
- Output is limited to path/PR, line, rule ID and fingerprint ID. Candidate
  values are never included.
- Both guards run in `ci.local.quick` and the full `make ci` entry.

## Deferred actions

Generic session invalidation is skipped by the explicit risk acceptance; it
must be completed when the legacy system is retired. The owner must replace the
missing formal cutover date before retirement execution. At cutover, disable
the legacy entry point and revoke all legacy sessions. Until that evidence
exists the incident remains accepted, not closed.
