# Fuse Node Packages

This directory contains the modular node packages for the Fuse automation system.
Each folder represents a self-contained node (or "plugin") that can be loaded by the engine.

## Structure

```
node_packages/
├── official/            # Official core nodes
│   ├── http-request/
│   ├── slack-send/
│   └── ...
├── community/           # Community-contributed nodes (future)
└── custom/             # Local custom nodes
```

## Anatomy of a Node Package

Each node package must have:

1. **manifest.json**: Configuration, inputs, outputs, and metadata.
2. **backend/execute.py**: The Python logic. Must export an `async def execute(context)` function.
3. **backend/requirements.txt**: Python dependencies (optional).
4. **README.md**: Documentation.

## Creating a New Node

1. Create a folder: `node_packages/custom/my-new-node`
2. Create `manifest.json`:
   ```json
   {
     "id": "my.new.node",
     "name": "My New Node",
     "version": "1.0.0",
     "description": "Does something cool",
     "inputs": [{"name": "text", "type": "string", "label": "Text"}],
     "outputs": [{"name": "result", "type": "string"}]
   }
   ```
3. Create `backend/execute.py`:
   ```python
   async def execute(context):
       text = context["inputs"]["text"]
       return {"result": f"Processed: {text}"}
   ```
4. Restart the server. The node will be auto-discovered!

## Hot Reloading

Changes to `execute.py` are loaded fresh on each restart.
For development without restart, you can use the `reload_node` API (coming soon).

## Migration Note

The old `fuse/workflows/engine/nodes/` class-based system has been removed.
All nodes must now live in this directory.
