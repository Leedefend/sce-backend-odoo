# Capability Intent Binding Spec v1

## 1. Objective

Freeze the relationship between capability assets and runtime intents so
capability governance and execution protocol stay decoupled but connected.

## 2. Core Separation

- Capability answers: what is recognized and governable.
- Intent answers: what action is executed now.
- Contract/Orchestration answers: how execution is structured and delivered.

## 3. Binding Contract

Capability rows must bind runtime intents through explicit binding payloads.

### 3.1 Required Binding Concepts

- `primary_intent`
- `secondary_intents` (optional list)
- `contract_subject`
- `entry_target`

### 3.2 Canonical Shape

```json
{
  "binding": {
    "intent": {
      "primary_intent": "app.open",
      "secondary_intents": ["ui.contract"]
    },
    "contract": {
      "subject": "scene",
      "contract_type": "entry_contract",
      "contract_version": "v1"
    },
    "exposure": {
      "menu_xmlid": "...",
      "action_xmlid": "..."
    }
  }
}
```

## 4. Mapping Rules

- One capability may bind multiple intents.
- One intent may be reused by multiple capabilities.
- Capability key must not be forced to equal intent key.
- Runtime dispatch must use intent protocol, not capability identifier.

## 5. Guard Rules

- No direct runtime execution by capability registry.
- No resolver/parser direct call to frontend final surface.
- No implicit binding inference in frontend.

## 6. Versioning

- Capability binding schema version is governed by capability schema lifecycle.
- Intent contract version remains runtime protocol version.
- Upgrade requires compatibility path for both binding and intent contract.

## 7. Validation Checklist

- `primary_intent` is present for executable capabilities.
- `contract_subject` is present for contract-driven capabilities.
- `entry_target` is present for entry capabilities.
- `secondary_intents` is additive and optional.

