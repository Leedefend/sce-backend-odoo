# SCEMS v1.0 Phase 6: Pilot Issue Ledger

> Scope: track Phase 6 pilot issues with P0/P1/P2 severity and closure status.

| ID | Time | Scenario | Step | Role | Severity | Symptom | Root Cause | Owner | Status | Closed Time |
|---|---|---|---|---|---|---|---|---|---|---|
| P6-001 | 2026-03-11 | W6-02 rehearsal batch | Batch-1 | all roles | P2 | No launch-blocking defect found in first rehearsal; recorded as baseline item | none | release manager | CLOSED | 2026-03-11 |

## Round-1 Conclusion (2026-03-11)
- Open `P0`: `0`
- Open `P1`: `0`
- Launch blockers: none

## Severity Rules
- `P0`: launch-blocking or core path unavailable; must be zero before launch.
- `P1`: high-risk issue; allowed only with explicit mitigation and post-launch follow-up.
- `P2`: general issue; non-blocking for launch.

## Closure Rules
- Every issue must include repro steps + scenario + role + severity.
- Status and close time are updated daily.
- Launch review must include a severity-based summary.
