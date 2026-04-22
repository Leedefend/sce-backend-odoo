# Scene Entry Semantics v1

## 1. Goal

Freeze the meanings of native entry, scene work entry, canonical entry, and
compatibility fallback.

## 2. Terms

- native entry
- scene work entry
- canonical entry
- compatibility fallback
- native-only degrade

## 3. Entry Classes

### 3.1 `/s/:sceneKey`

Represents the canonical scene/work entry.

### 3.2 `/a/:actionId`

Represents a native action compatibility entry or a native-first fallback path.

### 3.3 `/m/:menuId`

Represents a navigation origin. It is not automatically the final work entry.

## 4. Resolution Order

1. canonical scene entry
2. scene compatibility mapping
3. native fallback
4. unavailable

## 5. Required Output Contract

After entry/menu interpretation, the stable output should include at least:

- `target_type`
- `scene_key`
- `route`
- `native_action_id`
- `native_model`
- `native_view_mode`
- `reason_code`
- `confidence`
- `compatibility_used`

## 6. Allowed Patterns

- scene work entry with native fallback
- native entry coexisting with scene canonical route
- route-only compat scene where native menu/action are intentionally absent

## 7. Forbidden Behavior

- frontend guessing scene from menu/action by itself
- capability payload overriding canonical entry in reverse
- provider runtime rewriting entry identity
- one scene having multiple canonical work entries without explicit semantic split
