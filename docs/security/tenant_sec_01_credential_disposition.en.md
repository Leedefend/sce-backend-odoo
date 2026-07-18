# TENANT-SEC-01 credential risk disposition

中文：[tenant_sec_01_credential_disposition.md](tenant_sec_01_credential_disposition.md)

Status: `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE`

This record contains no credential value, reversible characteristic, redacted
fingerprint, or original match context. No legacy credential was tested, no
legacy system was accessed, and no public Git history rewrite was performed.

## Redacted classification

| ID | Type | First-seen commit | Current HEAD | Legacy system required | Revoked/rotated | Risk owner | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CRED-01` | Legacy-system username | `e8cbc880f692d504f2849f75d099aeabd0fb7220` | Absent | Yes | No | Delivery owner | `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE` |
| `CRED-02` | Legacy-system password | `e8cbc880f692d504f2849f75d099aeabd0fb7220` | Absent | Yes | No | Delivery owner | `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE` |
| `CRED-03` | Legacy-system password | `e8cbc880f692d504f2849f75d099aeabd0fb7220` | Absent | Yes | No | Delivery owner | `ACTIVE_WITH_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE` |

## Temporary risk-acceptance boundary

```text
LEGACY_SYSTEM_STILL_REQUIRED=true
ALLOWED_USE=data_completion_and_migration_only
CREDENTIAL_STORED_OUTSIDE_GIT=true
RETIREMENT_TRIGGER=new_system_cutover
RISK_ACCEPTED_BY=Delivery owner
```

Credential capability may only be supplied by a controlled secret outside Git.
Git defaults, cross-system fallback, embedded URL authentication, and log output
are forbidden. Credentials and related sessions must be invalidated at cutover.

## History decision

`HISTORY_REWRITE=NOT_EXECUTED_DURING_EXPLICIT_TEMPORARY_RISK_ACCEPTANCE`

Revocation, rotation, or provider invalidation has not been proven, so this task
does not claim `HISTORY_REWRITE_NOT_REQUIRED_AFTER_REVOCATION`. No filter-repo,
BFG, force push, tag deletion, or fork/cache cleanup was performed. If revocation
is still impossible at cutover, the decision must return to
`HISTORY_REWRITE_DECISION_REQUIRED`.
