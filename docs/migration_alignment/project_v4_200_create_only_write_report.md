# Project v4 200-row create-only write report

## Scope

- Task: `ITER-2026-04-14-0017`
- Database: `sc_demo`
- Model: `project.project`
- Input: `artifacts/migration/project_next_200_candidate_v4.csv`
- Authorization packet: `artifacts/migration/project_v4_200_write_authorization_packet.json`
- Write mode: create-only

## Result

- Status: PASS
- Candidate rows: 200
- Created rows: 200
- Updated rows: 0
- Errors: 0
- Post-write identity count: 200
- Stage projection mismatches: 0
- Created Odoo IDs: 2437 through 2636

## Artifacts

- Pre-write snapshot: `artifacts/migration/project_v4_200_pre_write_snapshot.csv`
- Post-write snapshot: `artifacts/migration/project_v4_200_post_write_snapshot.csv`
- Write result: `artifacts/migration/project_v4_200_write_result.json`

## Risk

- The write was an authorized DB mutation batch and remains high-risk by
  execution type.
- The write stayed within `project.project` safe fields from the authorization
  packet.
- No update, delete, workflow replay, ACL, security, payment, settlement, or
  accounting paths were touched.

## Rollback posture

The post-write snapshot contains the 200 created records and their legacy
project identities. Do not run rollback automatically. If rollback is required,
open a dedicated rollback task using the post-write snapshot as the target list.
