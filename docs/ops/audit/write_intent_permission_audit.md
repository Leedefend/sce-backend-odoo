# Write Intent Permission Audit

- intents_scanned: 6
- high_risk_count: 2
- medium_risk_count: 4

| intent | exists | required_groups | acl_guard | sudo_calls | unguarded_sudo | risk | source |
|---|---:|---:|---:|---:|---:|---|---|
| execute_button | Y | 0 | Y | 3 | 0 | medium | addons/smart_core/handlers/execute_button.py |
- matched: `execute_button`
- note: `execute_button` execute_button: REQUIRED_GROUPS not explicitly defined
| api.data(write) | Y | 0 | Y | 3 | 0 | medium | addons/smart_core/handlers/api_data_batch.py, addons/smart_core/handlers/api_data_unlink.py, addons/smart_core/handlers/api_data_write.py |
- matched: `api.data.create, api.data.unlink, api.data.batch`
- note: `api.data(write)` api.data.create: REQUIRED_GROUPS not explicitly defined
- note: `api.data(write)` api.data.unlink: REQUIRED_GROUPS not explicitly defined
- note: `api.data(write)` api.data.batch: REQUIRED_GROUPS not explicitly defined
| api.data.batch | Y | 0 | Y | 1 | 0 | medium | addons/smart_core/handlers/api_data_batch.py |
- matched: `api.data.batch`
- note: `api.data.batch` api.data.batch: REQUIRED_GROUPS not explicitly defined
| file.upload | Y | 0 | Y | 0 | 0 | medium | addons/smart_core/handlers/file_upload.py |
- matched: `file.upload`
- note: `file.upload` file.upload: REQUIRED_GROUPS not explicitly defined
| report.export | Y | 0 | N | 1 | 1 | high | addons/smart_construction_core/handlers/usage_export_csv.py |
- matched: `report.export, usage.export.csv`
- note: `report.export` report.export: intent not found in handlers
- note: `report.export` usage.export.csv: missing ACL guard call (check_access_rights/check_access_rule/has_group)
- note: `report.export` usage.export.csv: sudo usage without explicit ACL guard in file
- note: `report.export` usage.export.csv: REQUIRED_GROUPS not explicitly defined
| job.cancel | N | 0 | N | 0 | 0 | high | - |
- note: `job.cancel` job.cancel: intent not found in handlers
