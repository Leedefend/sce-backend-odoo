# Legacy credential incident v1

Status: `BLOCKED_BY_MANUAL_CREDENTIAL_REVOCATION`

Repository baseline: `859dae5bf0511facfa5ad95d8d93693ad40ffe75`

## Manual prerequisite

The required external confirmation has not been provided:

```text
LEGACY_CREDENTIALS_REVOKED=false
LEGACY_SESSIONS_REVOKED=false
REVOKED_AT=null
REVOKED_BY=null
```

No old credential was tested, no replacement credential was requested, and no
production user or database was accessed. GitHub PR bodies were read only and
were not edited.

## Fingerprint inventory

`config/security/legacy_credential_fingerprints.json` contains the 15
fingerprints produced by the earlier PR-body candidate scan. It records only
fingerprint IDs, source categories, PR numbers and disposition. The catalog
also contains three separately confirmed repository-history incident
fingerprints from the 2026-07-15 incident record. It contains no raw value,
length, prefix, suffix or reversible encoding.

The 15 PR fingerprints remain `UNREVIEWED`. Replaying them against the current
tree produced hundreds of matches in test and historical documentation, which
proves that a regular-expression match cannot safely be treated as a live
credential. Bulk PR replacement is therefore prohibited until a security owner
confirms revocation and reviews each candidate class.

## Current-tree remediation

The new guard found one current Markdown assignment matching confirmed history
fingerprint `HC-003`. It was replaced in place with
`<REVOKED_LEGACY_SECRET>` without printing or copying the value. A repeat scan
found zero blocking current-tree matches.

| Measure | Result |
| --- | ---: |
| Target text files scanned | 6,977 |
| Confirmed current-tree exposures before cleanup | 1 |
| Confirmed current-tree exposures after cleanup | 0 |
| Current-tree replacements | 1 |
| Secret values recorded | 0 |

## GitHub metadata inventory

The offline export contained 998 PR bodies. The current classifier produced 92
candidate assignments across the 15 candidate fingerprints. These are not all
confirmed leaks. PRs #788 and #269 remain high-priority manual-review items
from the earlier incident. No PR body was changed because credential/session
revocation is not confirmed. The prior global comment scan found zero issue
comment and zero review-comment matches; comments were not modified.

## Guard contract

- `make security.secret_scan` runs the existing high-confidence worktree scan.
- `make security.legacy_credential_guard` requires the fingerprint catalog,
  scans the worktree and additions relative to `origin/main`, and fails on any
  confirmed history fingerprint.
- `scripts/ci/legacy_credential_guard.py --pr-jsonl <offline-export>` adds an
  offline PR-body scan without contacting GitHub or writing metadata.
- Output is limited to path/PR, line, rule ID and fingerprint ID. Candidate
  values are never included.
- Both guards run in `ci.local.quick` and the full `make ci` entry.

## Deferred actions

After the external system owner supplies all four revocation fields, the
security owner must classify the PR candidates, replace only confirmed PR-body
leaks, re-read each edited body, and run the test-session invalidation matrix.
Until then the P0 must not be closed and no security-cleanup PR may be opened.
