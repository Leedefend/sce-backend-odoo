# Legacy Online Capture Configuration Contract v1

## Boundary

Online capture is a P4 delivery/operations tool. Its default mode is `offline`. Preflight only validates configuration: it performs no DNS lookup, network request, database access, or successful-capture manifest creation.

Secrets must come from the runtime environment or an existing secret manager. Documentation, Make, Compose, CI, and scripts must not provide username, password, or token defaults. SCBSLY credentials must never fall back to SCBS credentials.

## Global configuration

| Variable | Required | Meaning |
| --- | --- | --- |
| `SCBS_CAPTURE_MODE` | Always | `offline` (default) or `online` |
| `SCBS_ONLINE_CAPTURE_CONFIRM` | Online | Must equal the controlled confirmation value; it is not a secret |
| `SCBS_CAPTURE_DESTINATION_ALLOWLIST` | Online | Comma-separated allowed origins including the selected Base URL origin |
| `SCBS_CAPTURE_DRY_RUN` | Optional | Caller dry-run intent; never bypasses another guard |

## System-specific variables

SCBS requires `OLD_SCBS_BASE_URL`, `OLD_SCBS_USERNAME`, `OLD_SCBS_PASSWORD`, `OLD_SCBS_CAPTURE_WINDOW`, `SCBS_CAPTURE_RAW_OUTPUT_DIR`, `SCBS_CAPTURE_MANIFEST_OUTPUT_DIR`, and `SCBS_CAPTURE_AUDIT_LOG_PATH` in online mode. Optional bounded settings are `OLD_SCBS_REQUEST_TIMEOUT_SECONDS` (1–600, default 90) and `OLD_SCBS_REQUEST_RETRY_LIMIT` (0–10, default 3).

SCBSLY requires `SCBSLY_BASE_URL`, `SCBSLY_USERNAME`, `SCBSLY_PASSWORD`, `SCBSLY_CAPTURE_WINDOW`, `SCBSLY_CAPTURE_RAW_OUTPUT_DIR`, `SCBSLY_CAPTURE_MANIFEST_OUTPUT_DIR`, and `SCBSLY_CAPTURE_AUDIT_LOG_PATH`. Optional bounded settings are `SCBSLY_REQUEST_TIMEOUT_SECONDS` and `SCBSLY_REQUEST_RETRY_LIMIT` with the same ranges.

Base URLs may not contain embedded credentials, query strings, or fragments. SCBSLY must use its dedicated variables.

## Preflight

```bash
make online.capture.preflight
```

Online readiness additionally requires runtime injection of all variables and `ONLINE_CAPTURE_REQUIRE_ONLINE=1`. Missing settings, placeholders, invalid confirmation, disallowed destinations, or credential-bearing URLs fail before network access with stable exit code `78`.

Preflight output contains only missing-variable reasons, boolean state, and non-sensitive paths. It does not run replay or touch a database. Failed preflight creates no successful-capture manifest, screenshot, or trace.

Chinese: [online_capture_configuration_contract_v1.md](online_capture_configuration_contract_v1.md)
