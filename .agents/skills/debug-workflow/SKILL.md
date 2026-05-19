---
name: debug-workflow
description: "Diagnose a failing or misbehaving workflow execution. Reads execution logs, traces the node execution path, identifies the failure point, and suggests a fix. Usage: /debug-workflow <execution_id or description of the problem>"
---

# debug-workflow skill

## Inputs

Ask the user for one of:
- An execution ID (UUID) — to look up logs directly
- A description of what's failing (e.g. "HTTP node always errors", "Slack message not sending")
- A screenshot or error message they're seeing

## Investigation steps

### 1. Check execution logs in the database

If an execution ID is given, query:
```sql
SELECT id, node_id, level, message, payload, timestamp
FROM execution_log
WHERE execution_id = '<id>'
ORDER BY timestamp ASC;
```

Or check via the API: `GET /api/v1/executions/<id>/logs`

Look for:
- `level = 'error'` entries — these are failure points
- `payload.error` — the actual exception message
- Which `node_id` appears last before failure

### 2. Trace the execution path

Map `node_id` values in the logs back to the workflow graph:
- `GET /api/v1/workflows/<workflow_id>` — read the `graph.nodes` array
- Match `node.id` to `node.type` and `node.data.label`

Draw the execution path: `Start → Node A → Node B (FAILED) → ...`

### 3. Common failure patterns

| Symptom | Likely cause | Fix |
|---|---|---|
| `"missing required fields"` | Property not filled in inspector | Open node, fill required field |
| `"No credential found"` | Credential not selected or deleted | Re-select credential in node |
| `"expression 'X' failed to locate"` | Model not imported in `models/__init__.py` | Add import |
| `"NoneType has no attribute"` | Previous node returned empty output, template `{{node.output.field}}` is null | Add null check or default |
| HTTP 422 from external API | Wrong request body format | Check node's body/headers |
| `"TemplateError"` | Bad `{{ }}` expression syntax | Fix interpolation in node properties |
| Node never starts | Edge missing or condition node blocked path | Check edges in workflow graph |

### 4. Check node configuration

For the failing node:
- Read its `resolved_properties` from the error log payload (`payload.input`)
- Compare against what the node's Pydantic model expects
- Check if any required field is empty string or None

### 5. Check the node implementation

If it's a code issue:
- Read `apps/api/app/node_system/nodes/<category>/<type>/<type>.py`
- Look at the `execute()` method
- Check if it's handling the error case and returning `NodeResult(success=False, error=...)` instead of raising

## Output format

```
EXECUTION: <id>
WORKFLOW: <name>

Path: Start → [Node A: HTTP Request] → [Node B: Slack Message] ❌ FAILED

Failure at: Node B (Slack Message)
Error: "Missing required fields: channel"
Root cause: The Slack Message node's 'channel' property is empty.

Fix: Open the Slack Message node in the editor → set the Channel field.
     If you want it dynamic: use {{http_request.output.channel}} to pass it from the previous node.
```
