---
name: ai-memory
description: Query and update the local ai-memory MCP service for project memory, handoffs, and durable context. Use when recalling prior work or saving project knowledge.
---

# ai-memory MCP

Use the `ai_memory` Python module from the IPython kernel. The URL comes from `AI_MEMORY_SERVER_URL` (injected via sops-managed `~/.hermes/.env`; fallback `AI_MEMORY_URL`)
(default: tailnet `http://100.110.98.84:49374/mcp`; on racknerd itself use
`http://127.0.0.1:49374/mcp`) and uses the configured bearer token.

Discover the current API before calling a tool:

```python
import ai_memory
for tool in await ai_memory.list_tools():
    print(tool["name"], tool["description"])
```

Every discovered operation is async and must be awaited. Prefer the existing
memory operations for recall, recent pages, handoffs, and durable writes rather
than maintaining a second local cache.
