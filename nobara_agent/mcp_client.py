import contextlib
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONFIG_PATH = os.path.expanduser("~/.config/nobara-agent/mcp_servers.json")


@contextlib.asynccontextmanager
async def open_mcp_sessions():
    if not os.path.exists(CONFIG_PATH):
        yield []
        return
    try:
        with open(CONFIG_PATH) as f:
            servers = json.load(f)
    except Exception as e:
        print(f"[mcp] erro lendo {CONFIG_PATH}: {e}")
        yield []
        return

    sessions = []
    stacks = []
    try:
        for name, spec in servers.items():
            try:
                ctx = stdio_client(StdioServerParameters(
                    command=spec["command"],
                    args=spec.get("args", []),
                    env=spec.get("env"),
                ))
                read, write = await ctx.__aenter__()
                sctx = ClientSession(read, write)
                session = await sctx.__aenter__()
                await session.initialize()
                sessions.append((name, session))
                stacks.append((ctx, sctx))
                print(f"[mcp] conectado: {name}")
            except Exception as e:
                print(f"[mcp] falha ao conectar '{name}': {e}")
        yield sessions
    finally:
        for ctx, sctx in reversed(stacks):
            with contextlib.suppress(Exception):
                await sctx.__aexit__(None, None, None)
            with contextlib.suppress(Exception):
                await ctx.__aexit__(None, None, None)
