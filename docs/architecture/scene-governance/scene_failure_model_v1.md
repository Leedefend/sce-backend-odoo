# Scene Failure Model v1

## 1. Goal

Freeze failure types, reason semantics, logging expectations, and frontend
consumption constraints for backend scenification.

## 2. Failure Types

- `identity_missing`
- `authority_conflict`
- `provider_missing`
- `canonical_entry_missing`
- `compatibility_fallback_used`
- `native_only_degraded`
- `permission_denied`
- `record_context_insufficient`
- `runtime_build_failed`

## 3. Per-Type Expectations

For each failure type the system should eventually define:

- definition
- likely source layer
- user-visible impact
- allowed fallback
- verify expectation

Current minimum active set for this repository package:

- `identity_missing`
  - meaning: scene identity cannot be resolved or is absent from governed sources
- `authority_conflict`
  - meaning: multiple sources claim incompatible identity semantics
- `canonical_entry_missing`
  - meaning: a governed scene/family lacks a stable canonical entry explanation
- `compatibility_fallback_used`
  - meaning: runtime/menu resolution had to use compatibility rather than
    canonical scene entry
- `native_only_degraded`
  - meaning: scene-first path is unavailable and native-only entry remains
- `provider_missing`
  - meaning: published scene lacks provider or explicit fallback
- `record_context_insufficient`
  - meaning: scene/detail semantics need model/record identity that was not
    supplied
- `runtime_build_failed`
  - meaning: orchestration/runtime delivery failed before stable scene-ready
    output

## 4. Reason Codes

Reason codes should be stable enough for:

- backend diagnostics
- frontend state display
- guard/audit interpretation

## 5. Frontend Constraint

Frontend may consume:

- failure type
- reason code
- fallback hint

Frontend may not infer backend root cause beyond those fields.

## 6. Diagnostic Requirement

Each failure type should be traceable with enough evidence to answer:

- which layer failed
- whether fallback was used
- whether user-facing recovery is available

The structured CSV companion for this model is:

- `assets/scene_failure_codes_v1.csv`
