# ETag Validation Report

- status: PASS
- checks: 4
- failures: 0

| intent | first_status | has_etag | conditional_status | etag_changed |
|---|---:|---:|---:|---:|
| system.init | 200 | Y | 200 | Y |
| ui.contract | 200 | Y | 304 | Y |
| api.data | 200 | Y | 304 | Y |
| meta.describe_model | 200 | Y | 304 | Y |
