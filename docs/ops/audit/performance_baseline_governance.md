# Performance Baseline Governance

## Purpose

This document defines how performance baseline numbers are produced and consumed by regression gates.

## Baseline Metadata (Required)

- Baseline source report: `artifacts/backend/platform_sla_report.json`
- Baseline commit/tag: must be recorded in PR/Release notes when baseline is refreshed.
- Baseline environment:
  - DB name
  - role/login used
  - host/container mode
  - cache state policy (cold/warm)

## Sampling Policy

- Warmup requests per round: default `20`
- Measured rounds: default `3`
- Iterations per round:
  - `system.init`: `200`
  - `ui.contract`: `200`
  - `execute_button`: `1000`
- Metrics:
  - `P50`, `P95`, `P99`, `max`, `variance`
  - status/error rate

## Regression Grading

- `PASS`: all rounds under warn threshold, error rate `0`
- `WARN`: threshold warning exceeded in one or more rounds, but fail criteria not met
- `FAIL`:
  - non-2xx status exists, or
  - fail-threshold exceeded in at least `2/3` rounds (configurable)

## Threshold Policy

- Generic fail threshold: `max(baseline*1.10, baseline+abs_delta)`
- Generic warn threshold: `max(baseline*1.05, baseline+warn_abs_delta)`
- `execute_button` uses extra absolute floor (default fail floor `80ms`) to reduce noise sensitivity.

## Baseline Refresh Rule

Refresh baseline only when:

1. major infra/runtime condition changed, or
2. validated performance improvement is accepted.

Any baseline refresh must include:

- previous vs new baseline diff
- reason for refresh
- exact command and environment notes
