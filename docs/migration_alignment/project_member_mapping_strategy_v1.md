# Project member mapping strategy v1

Status: L1 DRY-RUN PASS  
Iteration: `ITER-2026-04-14-0030R`  
Database: `sc_demo`

This document records the no-write project_member mapping result after source
path recovery.

## Input

- Source: `artifacts/migration/project_member_source_shadow_v1.csv`
- Original source: `tmp/raw/project_member/project_member.csv`
- Source rows: 21390

## Mapping Result

| Item | Result |
| --- | ---: |
| total rows | 21390 |
| mapped projects | 21390 |
| unmapped projects | 0 |
| duplicate project matches | 0 |
| mapped users | 7389 |
| unmapped users | 14001 |
| placeholder classifications | 14001 |
| duplicate project/user pairs | 3 |

## User Mapping

| Match mode | Rows |
| --- | ---: |
| `name` | 7389 |
| `placeholder_user` | 14001 |

## Decision

Project identity mapping is ready for downstream screening because every
project_member row maps to a `project.project` by `legacy_project_id`.

User identity mapping is not ready for write mode. `placeholder_user` is only a
dry-run classification and must not be materialized as a real project member
without a dedicated authority decision.

## Next Gate

Before any project_member write:

- screen the 14001 placeholder-user rows;
- define whether unmapped users are skipped, mapped to a real fallback user, or
  held for manual mapping;
- define record-rule impact and approval criteria;
- generate a safe slice with no placeholder users.
