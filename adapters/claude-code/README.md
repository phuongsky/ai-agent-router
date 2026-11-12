# Claude Code adapter

Project-level MCP config: copy `mcp.json.example` to `.mcp.json` at repository root,
then replace absolute paths. Claude Code supports project-scoped MCP configuration.
Install the shared skill in `.claude/skills/requirement-router/SKILL.md` or use the
global skill directory supported by your Claude Code version.

Example:
`claude mcp add --transport stdio ai-requirement-router -- "C:\path\to\python.exe" -m requirement_router.server`

Keep `AGENTS.md` and `CLAUDE.md` in the repository root if you want both Claude and
other agents to discover their respective instructions.
