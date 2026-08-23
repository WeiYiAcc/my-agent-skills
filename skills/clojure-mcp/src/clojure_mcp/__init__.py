import os

from rlm import McpIntegration


def _default_url() -> str:
    # clojure-mcp 是本机进程 (nREPL 桥), 127.0.0.1:8078; 可用 CLOJURE_MCP_URL 覆盖
    base = os.environ.get("CLOJURE_MCP_URL", "http://127.0.0.1:8078").rstrip("/")
    return base + "/mcp"


class ClojureMcp(McpIntegration):
    server = "clojure-mcp"
    url = _default_url()

    async def _resolve_token(self) -> str:
        # 本地 nREPL 桥无鉴权; 基类强制要求非空 token, 这里返回占位值跳过凭据检查
        return "local"


clojure_mcp = ClojureMcp()
_RESERVED = {"run", "__wrapped__", "__call__"}


def __getattr__(name):
    if name.startswith("_") or name in _RESERVED:
        raise AttributeError(name)
    return getattr(clojure_mcp, name)
