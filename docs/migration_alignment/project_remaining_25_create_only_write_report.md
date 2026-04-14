# Project remaining 25-row create-only write report

## Scope

- Task: `ITER-2026-04-14-0025`
- Database: `sc_demo`
- Model: `project.project`
- Input: `artifacts/migration/project_remaining_candidate_v6.csv`
- Authorization packet: `artifacts/migration/project_remaining_25_write_authorization_packet.json`
- Write mode: create-only

## Result

- Status: PASS
- Candidate rows: 25
- Created rows: 25
- Updated rows: 0
- Errors: 0
- Post-write identity count: 25
- Stage projection mismatches: 0

## Artifacts

- Pre-write snapshot: `artifacts/migration/project_remaining_25_pre_write_snapshot.csv`
- Post-write snapshot: `artifacts/migration/project_remaining_25_post_write_snapshot.csv`
- Write result: `artifacts/migration/project_remaining_25_write_result.json`

## Risk

- The write was an authorized DB mutation batch and remains high-risk by
  execution type.
- The write stayed within `project.project` safe fields from the authorization
  packet.
- No update, delete, workflow replay, ACL, security, payment, settlement, or
  accounting paths were touched.

## Rollback posture

The post-write snapshot contains the 25 created records and their legacy project
identities. Do not run rollback automatically. If rollback is required, open a
dedicated rollback task using the post-write snapshot as the target list.
