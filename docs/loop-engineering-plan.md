# Loop Engineering — design plan

> **Status:** Draft for discussion.
> **Owner:** Bibek
> **Last updated:** 2026-06-21
> **Companion PR:** this file lands as a doc-only PR — no code changes — so reviewers can comment before any infrastructure work begins.

## 1. Problem statement

Today most workflow automation is **reactive**: a webhook fires, the
workflow runs the predetermined steps, the workflow exits. The
developer sets up every branch up front.

Real operations work is **iterative**: triage an inbox, fix a flaky
test, reply to a thread, watch a queue, retry until success. Doing
this with a "static" workflow forces the developer to be the loop —
checking outputs, deciding what to do next, retrying.

**Loop engineering** moves that loop into the platform:

> Set up a system once that continuously gives the AI tasks, checks
> the output, and automatically retries until the job is completed.

For RunMyCrew this is the difference between "a workflow that ran" and
"an autonomous worker that owns a queue."

## 2. Current state of the codebase

We already have ~80% of the primitives needed. Inventory:

| Capability | Where | Status |
|------------|-------|--------|
| Scheduled wake-up | `apps/api/app/node_system/nodes/common/cron/cron_node.py` | ✅ |
| Webhook trigger | `apps/api/app/node_system/nodes/http/webhook/webhook.py` | ✅ |
| Multi-provider LLM | `apps/api/app/node_system/nodes/ai/llm/llm.py` | ✅ |
| **Agent node with tools + iterations** | `apps/api/app/node_system/nodes/ai/agent/agent.py` | ✅ (single-pass; needs hardening for autonomous loops) |
| Memory provider | `apps/api/app/node_system/nodes/ai/memory/` | ✅ |
| Skills (modular prompts) | referenced in `agent.py` `skills` field | ✅ |
| MCP server hookup | `agent.py` `mcpServers` field | ✅ |
| Sub-workflow node | `apps/api/app/node_system/nodes/logic/sub_workflow/` | ✅ |
| Loop / while / foreach / do-while | `apps/api/app/node_system/nodes/logic/{loop,while_loop,foreach,do_while}/` | ✅ |
| Run history + audit log | `apps/api/app/features/runs/`, audit log panel | ✅ |
| Per-runner async lock | `workflow_runner.py` `self._lock` | ⚠️ in-process only, not cross-run |
| Retry config on tools | `ToolRetryConfig` in `apps/api/app/node_system/tools/base.py` | ✅ |

So the question isn't "build an agent runtime from scratch" — it's
"productionise the runtime we already have so it survives autonomous
24/7 use, expose the right ergonomics in the editor, and ship a
handful of starter templates."

## 3. Gaps to close

| Gap | Required for | Effort |
|-----|--------------|--------|
| **Cross-run concurrency mutex** — a 2nd loop must not start while the 1st is running | All scheduled loops | small (Redis-backed) |
| **Stop-condition expression** — explicit success matcher (e.g. `result.status == "done"`) | Agent loop graceful exit | small |
| **Time + token + cost budgets** with hard cutoff | Cost control + run-away protection | small |
| **Trace persistence** — every think/tool/observation step queryable | Debuggability, dashboards | medium |
| **Tool-from-node registry** — auto-build tool schema from any node's `NodeMetadata` so the agent can call `slack.post` or `linear.create_issue` natively | Useful agents | medium (mostly already there in `agent.py`'s `tools` shape) |
| **Failure escalation** — paginate / Slack / GitHub-issue when N retries fail | Reliability | trivial — composable today |
| **Frontend trace viewer** — render `trace[]` as a chat-style timeline in the run logs panel | Operability | medium |
| **Workflow-level autopause** — pause the workflow after K consecutive failures | Safety | small |
| **Cron drift correction** — if the runner sleeps past a fire, catch up vs. skip (policy choice per workflow) | Predictability | small |

## 4. Proposed architecture

### 4.1 The runtime shape

```
              ┌────────────────────────────────────────┐
              │  Cron trigger  (every 5m)              │
              └────────────────────────────────────────┘
                              │
                              ▼
              ┌────────────────────────────────────────┐
              │  Agent (loop) node                     │
              │  ─────────────────                     │
              │  goal:          "triage new tickets"   │
              │  tools:         [linear.*, github.*]   │
              │  max_iter:      10                     │
              │  max_seconds:   600                    │
              │  budget_tokens: 50_000                 │
              │  success_when:  $.action_taken         │
              │  failure:       'escalate'             │
              │                                        │
              │  ┌── ReAct loop ────────────────────┐  │
              │  │  thought → tool → observation    │  │
              │  │  ↑                            │   │  │
              │  │  └────────────────────────────┘   │  │
              │  └──────────────────────────────────┘  │
              └────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
          success?       budget_out?    failure?
          ↓              ↓              ↓
        exit ok       exit warn      escalate path
                                     (post to Slack, file issue)
```

### 4.2 Schema for the enhanced Agent node

```jsonc
{
  "type": "ai.agent_loop",
  "name": "Agent Loop",
  "category": "ai",
  "inputs_required": ["goal", "llm"],
  "inputs_optional": [
    "tools", "memory", "skills", "mcp_servers",
    "max_iterations", "max_seconds", "max_input_tokens",
    "max_total_cost_usd",
    "success_when",       // jsonata expression on the final result
    "failure_policy"      // 'escalate' | 'retry' | 'silent'
  ],
  "outputs": {
    "status":     "success | budget_exhausted | failed | no_op",
    "iterations": "int",
    "trace":      "step[]",
    "result":     "any",
    "usage": {
      "input_tokens":  "int",
      "output_tokens": "int",
      "cost_usd":      "float"
    }
  }
}
```

`trace` is a list of `{thought, tool_call, tool_args, tool_result, duration_ms}`
records — one per ReAct cycle.

### 4.3 Tool-from-node registry

When the agent loads `tools: [linear_list_issues, github_create_pr]`,
the runtime walks each referenced node and:

1. Reads its `NodeMetadata.properties` to build a JSON-schema describing
   the tool's input.
2. Wraps the node's `execute()` in a thin shim that the LLM can call
   via tool-use APIs (Anthropic, OpenAI, Gemini all support this).
3. Emits each invocation as a `trace` step.

This means **every existing node automatically becomes an agent tool**.
No new tool registry — we already have one (the node metadata system).

### 4.4 ReAct loop

```python
while True:
    if iterations >= max_iterations: status = 'budget_exhausted'; break
    if elapsed_seconds >= max_seconds: status = 'budget_exhausted'; break
    if cost_usd >= max_total_cost_usd: status = 'budget_exhausted'; break

    response = await llm.complete(messages, tools=schema)

    if response.is_tool_call:
        result = await tool_registry[response.tool_name](response.args)
        messages.append(result)
        trace.append(step)
        continue

    if response.is_final:
        if success_when and not evaluate(success_when, response.result):
            messages.append("Re-evaluate; success condition not met.")
            continue
        status = 'success'
        break
```

### 4.5 State & memory

Two layers:

| Layer | Lifetime | Backed by |
|-------|----------|-----------|
| **In-loop messages** | Single loop invocation | In-memory list |
| **Cross-run memory** | Forever (per `memory_key`) | Existing `MemoryNode` provider (Redis or pgvector) |

The Cron-fired loop persists nothing to "in-loop messages" between
invocations — each cron tick starts fresh. But it can read + write
durable state via the memory node (e.g. "last_processed_ticket_id =
ENG-2701").

### 4.6 Concurrency lock

New env: `RUNMYCREW_CONCURRENCY_BACKEND=redis|noop` (default redis in
prod).

Workflow-level field `concurrency` (one of `skip` / `queue` / `replace`):

| Policy | Behaviour |
|--------|-----------|
| `skip` (default for loops) | If a run is in-flight, this fire is a no-op and gets logged as `skipped_concurrent` |
| `queue` | New fire waits behind the in-flight run (FIFO, capped at 10) |
| `replace` | Cancel the in-flight run and start the new one (rare; useful for "freshest data wins" agents) |

Lock key: `runmycrew:concurrency:workflow:{workflow_id}` — `SET NX PX
{max_seconds + buffer}`. Released on run completion, expires on crash.

## 5. UX in the editor

### 5.1 New "Agent Loop" node

Same renderer + inspector as the existing `ai.agent` node, but the
property panel groups things into three tabs:

| Tab | What |
|-----|------|
| **Goal** | The prompt + skills + success_when expression |
| **Tools** | Drag-and-drop list of nodes to expose as tools, with permission toggles per tool |
| **Limits** | max_iter, max_seconds, token + cost budgets, failure_policy |

### 5.2 Trace viewer in the logs panel

Today the logs panel shows JSON I/O per node. For agent loops it
shows a **chat-style timeline**:

```
🧠  Thought:    "Need to read the open tickets, then pick the oldest"
🛠  linear.list_issues({queue: "Bug"})  →  3 items
🧠  Thought:    "Triage ENG-2701: needs label 'backend'"
🛠  linear.update_issue({id: "ENG-2701", labels: ["backend"]})  →  ok
✅  Final:      {ticket_triaged: "ENG-2701", action: "label_added"}
```

Each row is collapsible to show full args + raw result. Re-uses the
existing `JsonTreeView` + `CopilotMessage` styling.

### 5.3 Live tail during the loop

Server-sent events from the runner already exist (we use them for
Copilot streaming + node-status). We extend them with a
`loop_step` event so the frontend can render trace rows as they
land.

## 6. Templates

Three first-party templates shipped under the `Loops` category, each
with a 30-second demo screencast in the docs:

1. **Triage Linear bug queue** (`templates/triage-linear-bugs`)
   - Cron every 30 min → Agent reads `Bug` queue → labels +
     priority + auto-assigns by component.
2. **Dependabot auto-merger** (`templates/auto-merge-dependabot`)
   - GitHub webhook on `pull_request.opened` → Agent checks if
     PR author is Dependabot + CI green + patch/minor → auto-merge,
     else escalate to Slack.
3. **Sentry → GitHub issue** (`templates/sentry-to-issue`)
   - Cron every 15 min → Agent fetches new Sentry issues → for each,
     check if a GitHub issue already references the fingerprint, else
     create one + post to Slack.

Each template ships with sample workflow JSON, a 2-paragraph
description, the required credentials list, and a `Try this` button
that imports it.

## 7. Phased delivery

| Phase | Deliverable | Estimated effort | Gate |
|-------|-------------|-----------------|------|
| **0 — Spec review** *(this doc)* | This file, reviewed, approved | 0.5 day | — |
| **1 — Hardening pass on existing `ai.agent` node** | Add `success_when`, time + cost budgets, failure_policy, structured trace output | 2 days | Spec approved |
| **2 — Concurrency mutex** | Redis backend + workflow-level `concurrency` field + UI toggle | 1 day | — |
| **3 — Trace persistence + viewer** | Store `trace[]` to run history; render in logs panel | 2 days | Phase 1 |
| **4 — Tool registry polish** | Auto-build tool schema from `NodeMetadata`; per-tool permission toggle in inspector | 1 day | Phase 1 |
| **5 — Cron drift policy** | Workflow-level `cron_drift: catchup|skip` + run skipped/catchup audit events | 1 day | Phase 2 |
| **6 — Starter templates × 3** | The three templates above, with screencasts | 2 days | Phases 1–4 |
| **7 — Docs + landing page** | `/docs/agent-loops`, marketing-site section, blog post | 1 day | All |

**Total: ~10 working days** of focused effort once spec approved.

Phases 1–2 are the gate to "real autonomous loops work safely at all";
phases 3–6 are the polish that makes them sellable. Anyone can
hand-roll the same loop today using the existing Agent + Cron + Memory
nodes, but it isn't yet "set it and forget it."

## 8. Naming

I'm proposing the new variant ship as **Agent Loop** node, separate
from the existing `Agent` node. Reasons:

- `Agent` (single-pass) is what most workflows want; defaults stay
  conservative (max_iter=1, no budget needed).
- `Agent Loop` (autonomous) opts in to the looping semantics, signals
  the cost shape (loops cost N× tokens), and gets its own template
  shelf.

The underlying runtime is shared — only the surface is split.

## 9. Open questions for review

1. **Concurrency default**: I'm proposing `skip` for loop workflows
   (don't overlap with self). Should this be opt-in per workflow or
   a global default?
2. **Budgets**: Hard or soft? Today I propose **hard** (LLM call is
   skipped, status becomes `budget_exhausted`). Soft would warn-only.
3. **Trace storage**: Full trace per loop iteration could explode run
   history size for noisy agents. Options:
   - Always store full trace.
   - Store full trace for first N iterations + summarised trace after.
   - User-controlled per workflow.
4. **Failure escalation**: Should `escalate` be a built-in policy (we
   ship a default Slack/email handler) or a configured sub-workflow
   reference?
5. **MCP / external tools**: We already accept MCP servers in the
   agent config. Do we ship the loop with bundled MCP servers
   (filesystem? web?) or leave it BYO?
6. **Cost attribution**: Run history needs a per-loop `cost_usd`
   column for billing. Are we ready to start tracking that, or do we
   leave it as a `usage.cost_usd` blob until we wire billing?

## 10. Non-goals (explicitly out of scope for v1)

- Multi-agent debate / consensus / hand-off. This is single-agent
  loops only. Multi-agent comes after we prove single-agent works.
- Built-in code-writing or PR-opening primitives. The loop can call
  `github.create_pr` like any other tool; we don't ship a special
  "coder" loop.
- A separate billing tier for agent loops. Same plans as everything
  else, just `cost_usd` is tracked + visible.
- Custom user-defined ReAct prompts. We ship one good ReAct prompt;
  customisation comes later if users ask for it.
