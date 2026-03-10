# project.management Block Contract v1

## 1. Supported Block Types
- `record_summary`
- `metric_row`
- `progress_summary`
- `record_table`
- `alert_panel`

## 2. Common Envelope
```json
{
  "block_key": "block.project.metrics",
  "block_type": "metric_row",
  "title": "项目关键指标总览",
  "state": "ready",
  "visibility": {
    "allowed": true,
    "reason_code": "OK",
    "reason": ""
  },
  "data": {},
  "error": {
    "code": "",
    "message": ""
  }
}
```

## 3. Type: record_summary
- Required `data` fields:
  - `summary` (object)
  - `quick_actions` (array, optional in empty state)
- State-shape rule:
  - `ready | empty | forbidden` must all keep `summary` key.

## 4. Type: metric_row
- Required `data` fields:
  - `items`: array of `{key,label,value,unit}`
- State-shape rule:
  - `ready | empty | forbidden` must all keep `items` key.

## 5. Type: progress_summary
- Required `data` fields:
  - `task_total`
  - `task_done`
  - `completion_percent`
- State-shape rule:
  - `ready | empty | forbidden` must all keep the three keys.

## 6. Type: record_table
- Required `data` fields:
  - `columns`: array
  - `rows`: array
  - `quick_actions` (optional)
- State-shape rule:
  - `ready | empty | forbidden` must all keep `columns` and `rows`.

## 7. Type: alert_panel
- Required `data` fields:
  - `alerts`: array of `{level,code,title,value}`
  - `quick_actions` (optional)
- State-shape rule:
  - `ready | empty | forbidden` must all keep `alerts`.

## 8. State Semantics
- `ready`: data available and allowed.
- `empty`: allowed but no effective business data.
- `forbidden`: blocked by capability/group policy.
- `error`: runtime/data-source failure; envelope still stable.

## 9. Frontend Minimum Rendering Requirements
- Render by `block_type`.
- Respect `state` first, then render `data`.
- Do not infer permission from business fields; use `visibility`.
- Show safe fallback when unknown `block_type` appears.
