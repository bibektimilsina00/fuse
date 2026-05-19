---
name: new-node
description: "Scaffold a complete workflow node — backend (BaseNode subclass + Pydantic model + NodeMetadata) and frontend (NodeDefinition in node-definitions package). Follows the exact project patterns so the node is auto-discovered by the registry. Usage: /new-node"
---

# new-node skill

Ask the user for:
1. **Category** — one of: `common`, `http`, `slack`, or a new category name
2. **Node name** — PascalCase (e.g. `EmailSender`, `SlackReaction`, `WebhookReceiver`)
3. **What it does** — one sentence description
4. **Properties** — list of fields the user configures (name, type, required?)
5. **Inputs / Outputs** — how many connection handles (usually 1 input, 1 output)
6. **Credential type** — if it needs auth (e.g. `slack_oauth`, `gmail_oauth`, or none)
7. **allowError** — should it have an error output handle? (yes/no)

## Files to create

### Backend: `apps/api/app/node_system/nodes/<category>/<snake_name>/<snake_name>.py`

Follow this exact pattern from `apps/api/app/node_system/nodes/http/request/request.py`:

```python
from pydantic import BaseModel
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

class <NodeName>Properties(BaseModel):
    # one field per user-specified property
    field_name: str = ""

class <NodeName>Node(BaseNode[<NodeName>Properties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="<snake_type>",
            name="<Display Name>",
            category="<category>",
            description="<description>",
            icon="<lucide-icon-name>",
            color="#<hex>",
            inputs=1,
            outputs=1,
            properties=[
                # one dict per property matching the Pydantic model
            ],
            credential_type=None,  # or "<credential_type>"
            allow_error=False,
        )

    @classmethod
    def get_properties_model(cls):
        return <NodeName>Properties

    async def execute(self, input_data: dict, context: NodeContext) -> NodeResult:
        try:
            # implementation
            return NodeResult(success=True, output_data={})
        except Exception as e:
            return NodeResult(success=False, error=str(e))
```

Also create `apps/api/app/node_system/nodes/<category>/<snake_name>/__init__.py` (empty).

If the category is new, create `apps/api/app/node_system/nodes/<category>/__init__.py` (empty).

### Frontend: `packages/node-definitions/src/nodes/<category>/<snake_name>.ts`

```typescript
import type { NodeDefinition } from '../../types'

export const <NodeName>Definition: NodeDefinition = {
  type: '<snake_type>',
  name: '<Display Name>',
  category: '<category>',
  description: '<description>',
  icon: '<lucide-icon-name>',
  color: '#<hex>',
  inputs: 1,
  outputs: 1,
  properties: [
    // one object per property, matching backend exactly
  ],
}
```

Then register it in `packages/node-definitions/src/index.ts` by adding it to the exported `nodeDefinitions` array.

## Validation checklist before finishing

- NodeMetadata `type` string matches frontend `type` string exactly
- Every Pydantic field name matches a `name` in the frontend `properties[]`
- `inputs`/`outputs` counts match in both files
- `credential_type` in backend matches `credentialType` in frontend (or both null)
- `allow_error` in backend matches `allowError` in frontend
- No manual registry registration needed — auto-discovered

## After creating

Tell the user to restart the API server (`uvicorn` / `celery`) to pick up the new node.
