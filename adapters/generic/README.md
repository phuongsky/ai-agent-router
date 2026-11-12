# Generic MCP-compatible agent

1. Configure an MCP stdio server with the Python executable and `server.py` path.
2. Expose the tools `arr_list_projects`, `arr_list_modules`, `arr_classify`, `arr_save`,
   and `arr_search`.
3. Add `AGENTS.md` or the portable Skill instructions to the agent's project context.
4. Ensure the agent follows the required sequence: resolve project → classify → validate →
   save → report.
