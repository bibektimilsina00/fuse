# Phase 10 — More Nodes (Updated)

**Status: ⬜ Not Started**

## Goal
Implement core utility nodes: **Set Variable**, **JSON Transform**, **Merge**, and **Switch**. These nodes provide the logical backbone for complex workflows.

## Backend Pattern
- **Path**: `apps/api/app/node_system/nodes/common/<node_name>/<node_name>.py`
- **Pattern**: `BaseNode[PropertiesModel]` + `BaseModel` for properties.
- **Registration**: Add to `apps/api/app/node_system/registry/registry.py`.

## Frontend Pattern
- **Path**: `packages/node-definitions/src/nodes/common/<node_name>.ts`
- **Pattern**: `NodeDefinition` export.
- **Registration**: Import and add to `nodeDefinitions` in `packages/node-definitions/src/registry.ts`.

---

## 1. Set Variable (`logic.set_variable`)
Stores a value in the workflow execution context (`context.variables`).

- **Properties**:
  - `key` (string, required): Variable name.
  - `value` (string, required): Value to store (supports interpolation).
- **Implementation**: Mutates `context.variables[key] = value`.

## 2. JSON Transform (`logic.json_transform`)
Reshapes input data using a Jinja2 template.

- **Properties**:
  - `template` (json/string, required): The output structure.
- **Dependencies**: `jinja2` (already in some parts of the project, but ensure it's in `apps/api`).
- **Implementation**: Renders the template using `input_data` as context.

## 3. Merge (`logic.merge`)
Combines multiple incoming data streams.

- **Properties**:
  - `mode` (options): `shallow` or `deep`.
- **Implementation**: Currently a passthrough (handled by execution engine data merging), but provides a visual convergence point.

## 4. Switch (`logic.switch`)
Routes execution based on a field value.

- **Properties**:
  - `field` (string, required): Field to check in `input_data`.
  - `cases` (json): Mapping of values to branch names.
- **Outputs**: 2+ handles (dynamic branching support needed in UI, or static 2 for now).

---

## Implementation Checklist

- [ ] **Dependency**: Check if `jinja2` is in `apps/api/pyproject.toml`.
- [ ] **Set Variable**: Backend + Frontend + Registry.
- [ ] **JSON Transform**: Backend + Frontend + Registry.
- [ ] **Merge**: Backend + Frontend + Registry.
- [ ] **Switch**: Backend + Frontend + Registry.
- [ ] **Verification**: Run the "Acceptance Criteria" workflow (HTTP -> Transform -> Set Var).
