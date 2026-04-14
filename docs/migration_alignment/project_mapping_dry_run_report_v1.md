# Project Mapping Dry Run Report v1

## Result

PASS_WITH_IMPORT_BLOCKERS

The dry run produced all requested project-only mapping tables. It does not
import data and does not create a formal import script.

## Data Facts

- Rows scanned: 755
- `ID`: 755 non-empty, 755 unique
- `PROJECT_CODE`: 479 non-empty, 479 unique
- `OTHER_SYSTEM_ID`: 696 non-empty, 696 unique
- `OTHER_SYSTEM_CODE`: 696 non-empty, 696 unique
- Company: 7 unique names, 8 unique ID/name pairs
- Specialty type: 36 unique names, 37 unique IDs
- Region: no non-empty values
- Project manager / technical responsibility / owner / supervision source text: no non-empty values in this export

## Field Mapping Type Statistics

| Type | Field Count |
| --- | ---: |
| direct | 28 |
| dictionary | 8 |
| text_match | 5 |
| defer | 22 |
| total | 63 |

## Dictionary Coverage

| Domain | Coverage |
| --- | ---: |
| Company exact row coverage | 659 / 755 = 87.28% |
| Company exact unique-name coverage | 1 / 7 = 14.29% |
| Company exact unique ID/name pair coverage | 2 / 8 = 25.00% |
| Specialty exact row coverage | 309 / 755 = 40.93% |
| Specialty exact unique-name coverage | 4 / 36 = 11.11% |
| Lifecycle/stage normalized coverage | 0 / 755 = 0.00% |
| Region dictionary coverage | N/A, source values empty |

## Text Match Success

| Domain | Result |
| --- | --- |
| User matching | N/A: project responsibility source columns are empty |
| Partner matching | N/A: owner/supervision source columns are empty |

## Unresolved Blockers

1. Company mapping needs decisions for six branch/company names not present as
   `res.company`: `保盛重庆分公司`, `保盛新疆分公司`, `保盛绵阳分公司`,
   `保盛西藏分公司`, `保盛广元分公司`, `项目实施分公司`.
2. Specialty dictionary mapping covers only 40.93% of rows exactly. The
   remaining 446 rows need new dictionary values or an approved normalization
   table.
3. `PROJECT_CODE` is unique when present, but writing it directly needs a
   project-code sequence policy decision.
4. Lifecycle/state/delete mapping is not ready: `STATE=0`,
   `IS_COMPLETE_PROJECT`, and `DEL=1` need an approved conversion table before
   writing `stage_id`, `lifecycle_state`, or `active`.
5. Contract, tax, account/bank, cost, file, audit metadata, and requirement
   confirmation fields remain intentionally deferred.

## Import Readiness

The repository is ready for a limited first-round dry-run importer design that
preserves raw legacy fields and imports only safe direct project master data.

It is not ready for a full first-round project data import that writes
`company_id`, `project_type_id`, `project_category_id`, `stage_id`,
`lifecycle_state`, `active`, user relations, partner relations, contract fields,
tax/account fields, or cost fields.

## Next Step

Create a mapping-approval task for:

- company branch mapping;
- specialty dictionary extension or normalization;
- `PROJECT_CODE` write policy;
- lifecycle/stage/state/delete conversion;
- whether `PROJECT_ENV=测试项目` should be excluded or imported with a test flag.
