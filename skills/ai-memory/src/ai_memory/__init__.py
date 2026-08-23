import os

from rlm import McpIntegration


def _default_url() -> str:
    # 注入约定: AI_MEMORY_SERVER_URL 来自 sops 管理的 ~/.hermes/.env;
    # 默认 tailnet IP 在所有机器(含 racknerd 本机)可达, 127.0.0.1 仅 VPS 本机成立
    base = (
        os.environ.get("AI_MEMORY_SERVER_URL")
        or os.environ.get("AI_MEMORY_URL")
        or "http://100.110.98.84:49374"
    ).rstrip("/")
    return base + "/mcp"


class AiMemory(McpIntegration):
    server = "ai-memory"
    url = _default_url()
    bearer_token_env = "AI_MEMORY_AUTH_TOKEN"


ai_memory = AiMemory()
_RESERVED = {"run", "__wrapped__", "__call__"}


def __getattr__(name):
    if name.startswith("_") or name in _RESERVED:
        raise AttributeError(name)
    return getattr(ai_memory, name)
