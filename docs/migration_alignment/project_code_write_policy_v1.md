# Project Code Write Policy v1

## Fact Base

- Legacy `PROJECT_CODE` has 479 non-empty values and all 479 are unique.
- The dry run marked `PROJECT_CODE -> project_code` as `defer` because current
  project-code sequence policy has not been approved for direct writes.
- Current model has `project_code` and alias `code`; `project_code` is unique.
- This document does not import legacy data and does not implement any code
  writing behavior.

## Strategy A: Write Legacy Code To Official `project_code`

Decision: not recommended for first safe slice.

Pros:

- Preserves old visible project codes directly.
- Allows users to search by legacy code without extra field logic.

Risks:

- May bypass or conflict with the current system sequence policy.
- 276 rows have empty legacy project code and would still require generated
  codes or fallback behavior.
- It makes the legacy code the new official code before code governance is
  approved.

## Strategy B: Write Legacy Code To Legacy/External Code Carrier

Decision: recommended.

Recommended target behavior:

- Do not write `project_code` in the first safe slice.
- Preserve `PROJECT_CODE` in a legacy-code carrier before small sample import.
- If no dedicated legacy-code carrier exists yet, hold `PROJECT_CODE` out of
  the first sample import and include it in the next field-carrier task.

Reason:

- It keeps current internal code generation stable.
- It preserves old code traceability without redefining official code semantics.
- It lets the sample import proceed for project skeleton data while code policy
  remains isolated.

## Strategy C: Do Not Import Legacy Code

Decision: not recommended as final policy.

Pros:

- Lowest immediate write risk.

Risks:

- Loses a useful legacy reconciliation key for 479 rows.
- Makes later user support and migration audit harder.

## Recommendation

Use Strategy B. For the next small sample import, exclude `PROJECT_CODE` from
formal writes unless a dedicated legacy-code carrier is added and upgraded first.
Do not write `project_code` directly in the first safe import slice.
