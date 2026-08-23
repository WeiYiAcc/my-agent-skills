---
name: ariadne-fact
description: Query and maintain the local ariadne-fact knowledge base through MCP. Use when looking up or recording structured facts.
---

# ariadne-fact MCP

Use the `ariadne_fact` Python module from the IPython kernel. The URL comes from
`ARIADNE_FACT_URL` (default: tailnet `http://100.110.98.84:7735/mcp`; on racknerd
itself use `http://127.0.0.1:7735/mcp`) and uses the configured bearer token.

Discover the current API before calling a tool:

```python
import ariadne_fact
for tool in await ariadne_fact.list_tools():
    print(tool["name"], tool["description"])
```

Every discovered operation is async and must be awaited. Do not assume tool
names or argument schemas; inspect `list_tools()` first.
