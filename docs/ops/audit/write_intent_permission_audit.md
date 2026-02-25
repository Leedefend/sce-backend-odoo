# Write Intent Permission Audit

- intents_scanned: 6
- high_risk_count: 0
- medium_risk_count: 0

| intent | exists | required_groups | acl_guard | sudo_calls | unguarded_sudo | risk | source |
|---|---:|---:|---:|---:|---:|---|---|
| execute_button | Y | 0 | Y | 3 | 0 | low | addons/smart_core/handlers/execute_button.py |
- matched: `execute_button`
- note: `execute_button` execute_button: REQUIRED_GROUPS not explicitly defined (relying on model ACL)
| api.data(write) | Y | 0 | Y | 3 | 0 | low | addons/smart_core/handlers/api_data_batch.py, addons/smart_core/handlers/api_data_unlink.py, addons/smart_core/handlers/api_data_write.py |
- matched: `api.data.create, api.data.unlink, api.data.batch`
- note: `api.data(write)` api.data.create: REQUIRED_GROUPS not explicitly defined (relying on model ACL)
- note: `api.data(write)` api.data.unlink: REQUIRED_GROUPS not explicitly defined (relying on model ACL)
- note: `api.data(write)` api.data.batch: REQUIRED_GROUPS not explicitly defined (relying on model ACL)
| api.data.batch | Y | 0 | Y | 1 | 0 | low | addons/smart_core/handlers/api_data_batch.py |
- matched: `api.data.batch`
- note: `api.data.batch` api.data.batch: REQUIRED_GROUPS not explicitly defined (relying on model ACL)
| file.upload | Y | 0 | Y | 0 | 0 | low | addons/smart_core/handlers/file_upload.py |
- matched: `file.upload`
- note: `file.upload` file.upload: REQUIRED_GROUPS not explicitly defined (relying on model ACL)
| report.export | Y | 1 | Y | 1 | 0 | low | addons/smart_construction_core/handlers/usage_export_csv.py |
- matched: `usage.export.csv`
- note: `report.export` usage.export.csv: permission posture looks acceptable
| job.cancel | N | 0 | N | 0 | 0 | low | - |
- note: `job.cancel` job.cancel: intent not found in handlers
