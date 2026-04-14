# Project State Expand Sample Matrix v1

Status: Gate Matrix  
Iteration: ITER-2026-04-13-1834

## 1. Expansion Layers

| Layer | Rows | Status | Purpose |
| --- | ---: | --- | --- |
| Existing written trial | 30 | already written in ITER-2026-04-13-1825 | baseline readability and rollback lock |
| Candidate expansion | 100 | dry-run only in ITER-2026-04-13-1834 | next bounded create-only write authorization candidate |

The previously suggested 10/30/100 strategy is treated as already satisfied for
30-row baseline plus 100-row bounded candidate. A separate 10-row write slice is
not needed unless the next write authorization batch chooses to split the 100
candidate rows further.

## 2. Candidate Selection Rules

- Source: `tmp/raw/project/project.csv`.
- Exclude all 30 `legacy_project_id` values already created in the 1825 trial.
- Keep only rows with non-empty `legacy_project_id` and `name`.
- Use the frozen 22 safe-slice fields only.
- Prefer early diversity across company, project environment, and business nature.
- Fill remaining rows in source order until 100 rows are selected.

## 3. Candidate Header

The candidate CSV contains exactly the 22 safe fields:

```text
legacy_project_id,legacy_parent_id,name,short_name,project_environment,legacy_company_id,legacy_company_name,legacy_specialty_type_id,specialty_type_name,legacy_price_method,business_nature,detail_address,project_profile,project_area,legacy_is_shared_base,legacy_sort,legacy_attachment_ref,project_overview,legacy_project_nature,legacy_is_material_library,other_system_id,other_system_code
```

## 4. Next Write-Batch Validation Matrix

| Validation | Required Result |
| --- | --- |
| pre-write identity check | all 100 candidate `legacy_project_id` values absent in target |
| write mode | create-only |
| update/upsert count | 0 |
| write error count | 0 |
| rollback lock | 100 rows uniquely matched by `legacy_project_id` |
| lifecycle default | allowed default `draft` unless next task explicitly maps lifecycle |
| stage projection | 100% `stage_id == lifecycle_state` projection |
| native form/list/kanban | sample read PASS |
| dashboard/read-side state | lifecycle-derived labels PASS |

## 5. Stop Conditions For Next Write Batch

Stop before writing if any of the following occurs:

- candidate target identity already exists;
- update/upsert path appears;
- unsafe fields appear;
- `stage_id` or `lifecycle_state` appears in the candidate CSV;
- rollback key is not unique;
- state projection or read-side guards fail.

