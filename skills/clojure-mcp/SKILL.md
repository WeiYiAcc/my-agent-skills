---
name: clojure-mcp
description: Evaluate Clojure and query/fix DataScript data through the local clojure-mcp nREPL bridge (port 8078). Use for ariadne-fact schema-level entity cleanup, data repair, and datalog debugging that the HTTP API cannot do.
---

# clojure-mcp MCP

Use the `clojure_mcp` Python module from the IPython kernel. The server is a
local process at `http://127.0.0.1:8078/mcp` (override with `CLOJURE_MCP_URL`),
no auth needed.

Discover the current API before calling a tool:

```python
import clojure_mcp
for tool in await clojure_mcp.list_tools():
    print(tool["name"], tool["description"])
```

Every discovered operation is async and must be awaited.

## When to use (ariadne-fact project rules)

- Cleanup of orphan tag / class / closed-value schema entities
- Repairing corrupted historical data (misplaced blocks, wrong `:block/parent`)
- Debugging datalog queries with `d/entity` / `d/touch`
- Read-only first: inspect with `d/q` before any retract; writes should be
  single-point or `:in`-parameterized batch retracts
- After fixing, record a troubleshooting fact explaining why nREPL was needed
