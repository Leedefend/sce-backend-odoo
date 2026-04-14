# Project member legacy role source audit v1

Status: FROZEN_NO_AUTHORITATIVE_SOURCE  
Iteration: `ITER-2026-04-14-0030RF`  
Database: `LegacyDb`

## Probe Scope

The audit queried the old SQL Server database directly through the existing
`legacy-sqlserver` container.

Primary legacy member table:

```text
dbo.BASE_SYSTEM_PROJECT_USER
```

Primary table columns:

```text
ID, PID, USERID, XMID, XMMC, LRR, LRRID, LRSJ
```

Primary table rows:

```text
21390
```

## Direct Role Source

Result:

```text
authoritative role source in dbo.BASE_SYSTEM_PROJECT_USER = no
role-like columns = none
mapping rate from primary member table = 0.0
```

This confirms that the exported CSV did not drop a role field from the primary
member table. The old database primary member table itself does not carry the
target role fact required by `project.responsibility.role_key`.

## Candidate Search

The old database contains role-like facts elsewhere:

| Item | Result |
| --- | ---: |
| role-like columns discovered | 454 |
| project/user/role triad candidate tables | 17 |
| best triad mapping rate back to `BASE_SYSTEM_PROJECT_USER` | 0.0 |

Top candidate tables included:

| Table | Rows | Candidate columns | Coverage |
| --- | ---: | --- | ---: |
| `BASE_ORGANIZATION_DEPARTMENT_PDUTY_USER` | 4915 | `XMID`, `USERID`, `PDUTYNAME` | 0.0 |
| `P_ZTB_GCBMGL` | 2848 | `XMID`, `LXR_UserID`, `D_ZTZH_XMPZWH` | 0.0 |
| `Pm_Person_Department_PDuty_History` | 177 | `XMID`, `Ding_Userid`, `PDutyId` | 0.0 |
| `BGGL_XZ_BZ` | 115 | `XMID`, `RYID`, `BMGW` | 0.0 |
| `Pm_Person_Department_PDuty` | 102 | `XMID`, `Ding_Userid`, `PDutyId` | 0.0 |

Other role tables such as `BASE_SYSTEM_USER_ROLE`, `tr_RoleToUser`, and
`BASE_SYSTEM_ROLE` describe global user-role or permission-role structures, not
a direct project-member role fact for `(XMID, USERID)`.

## Audit Decision

No authoritative legacy role source is available for the current
`project_member` importer lane.

The data can support a membership relation:

```text
legacy_member_id + legacy_project_id + legacy_user_id
```

It cannot support a responsibility role:

```text
project.responsibility.role_key
```

## Frozen Decision

Do not write `project.responsibility` with a fabricated fixed role.

Proceed through `sc.project.member.staging` for neutral member-fact preservation.
Any later promotion to responsibility requires a separate verified source or
business-approved rule.
