# User Data Migration Closure Gate

Status: PASS
Database: sc_demo
Generated At: 2026-06-13T02:04:35.341621+00:00

| Step | Status | Return Code | Key Result |
| --- | --- | ---: | --- |
| user_asset_verify | PASS | 0 | records=101 package=user_sc_v1 |
| history_legacy_user_recovery_probe | PASS | 0 | profiles=140 roles=330 scopes=90871 |
| user_data_reconciliation_full_scope_probe | PASS | 0 | blocking=0 warnings=14 models=39 |
| scbs_55_user_visible_business_data_final_probe | PASS | 0 | rows=55 review=0 |
