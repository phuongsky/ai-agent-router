# OpenAI Codex adapter

Add the MCP server to `~/.codex/config.toml` or project-supported Codex configuration.
Example:

```toml
[mcp_servers.ai-requirement-router]
command = "C:\\PATH\\TO\\PYTHON.EXE"
args = ["C:\\PATH\\TO\\ai-requirement-router\\src\\requirement_router\\server.py"]
```

Keep `AGENTS.md` at repository root. Verify with `codex mcp list`.
