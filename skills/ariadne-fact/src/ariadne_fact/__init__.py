import os

from rlm import McpIntegration


def _default_url() -> str:
    # 127.0.0.1 只在 racknerd 本机成立; 其他机器走 ARIADNE_FACT_URL (tailnet)
    base = os.environ.get("ARIADNE_FACT_URL", "http://127.0.0.1:7735").rstrip("/")
    return base + "/mcp"


class AriadneFact(McpIntegration):
    server = "ariadne-fact"
    url = _default_url()
    bearer_token_env = "ARIADNE_API_KEY"


ariadne_fact = AriadneFact()
_RESERVED = {"run", "__wrapped__", "__call__"}


def __getattr__(name):
    if name.startswith("_") or name in _RESERVED:
        raise AttributeError(name)
    return getattr(ariadne_fact, name)
