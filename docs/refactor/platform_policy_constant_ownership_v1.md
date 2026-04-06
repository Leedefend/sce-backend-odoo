# Platform Policy Constant Ownership v1

## Purpose

Define policy constant ownership migration from industry bridge module to
platform `smart_core` policy/config layer.

## Ownership Matrix

- `SERVER_ACTION_WINDOW_MAP`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: action routing policy
  - contribution mode: optional module override contribution

- `FILE_UPLOAD_ALLOWED_MODELS`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: file api policy
  - contribution mode: optional module model list contribution

- `FILE_DOWNLOAD_ALLOWED_MODELS`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: file api policy
  - contribution mode: optional module model list contribution

- `API_DATA_WRITE_ALLOWLIST`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: data api write policy
  - contribution mode: optional module allowlist contribution

- `API_DATA_UNLINK_ALLOWED_MODELS`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: data api unlink policy
  - contribution mode: optional module model list contribution

- `MODEL_CODE_MAPPING`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: model exposure policy
  - contribution mode: optional mapping contribution

- `CREATE_FIELD_FALLBACKS`
  - current owner: `smart_construction_core`
  - target owner: `smart_core.core.platform_policy_defaults`
  - policy type: create fallback policy
  - contribution mode: yes (industry fallback contribution)

## Migration Rule

- platform handlers/resolvers must consume `smart_core` policy defaults first.
- legacy `smart_core_*` hooks remain compatibility fallback in migration stage.
- industry module no longer acts as mandatory primary owner.

