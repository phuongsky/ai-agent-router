# AI Requirement Router — Community Edition

**IDE-agnostic · Multi-project · MCP-native · Git-first · Local-first**

AI Requirement Router captures natural-language software requirements, classifies them
into registered business modules, checks duplicates, and appends structured Markdown
requirements. It is designed to work with any coding agent that supports MCP stdio tools,
and with compatible Agent Skills clients.

- No Docker
- No database server
- No hosted API required by the router
- No source-code modification
- No automatic Git commit/push
- Markdown files remain in your own repository

## Architecture

```text
User chat
   |
   v
IDE / Coding Agent (semantic understanding)
   |  Agent Skill + AGENTS.md
   v
MCP stdio tools
   |
   v
Python Router Core
   |-- project registry (outside repositories)
   |-- module registry (inside each repository)
   |-- rule validation + confidence gate
   |-- duplicate fingerprint
   |-- safe relative-path validation
   v
requirements/<module>/*.md
   |
   v
Git history (controlled by the user)
```

**Important:** MCP is the standard tool protocol; Agent Skills is the portable instruction
format. The model/IDE performs semantic understanding. The Python server validates the
selected module against the project's registered module list and local aliases. The server
does not secretly call an LLM or send project data over the network.

## Requirements

- Windows 11, macOS, or Linux
- Python 3.11+
- Git (recommended)
- An MCP-compatible agent for chat-driven automatic capture

## Install from source

```bash
git clone https://github.com/phuongsky/ai-agent-router
cd ai-agent-router
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Register multiple projects

```powershell
cd C:\YOUR_PATH\ai-agent-router
.\.venv\Scripts\python.exe -m pip install -e .

arr register --id project-1 --name "Project 1" --path "D:\project1"
arr register --id project-2 --name "Project 2" --path "D:\project2"
arr list
```

Or without installing the console script:

```powershell
python -m requirement_router register --id demo-crm --name "Demo CRM" --path "D:\Projects\CRM"
```

Registry location:
- Windows: `%LOCALAPPDATA%\AIRequirementRouter\projects.json`
- macOS/Linux: `$HOME/.local/share/AIRequirementRouter/projects.json` (unless `ARR_HOME` is set)

Each project gets `.requirement-router/modules.json`. Edit it to define business modules,
aliases, and Markdown destinations. See `examples/modules.json`.

## Configure an MCP host

The MCP server runs over stdio. Configure the host with:
- command: absolute path to this project's virtual-environment Python executable
- args: `[-m, requirement_router.server]`

The package is installed editable (`pip install -e .`), so the module entry point works from any working directory. The project currently pins the maintained MCP Python SDK v1 API line (`mcp<2`) to avoid the breaking v2 SDK API changes; the MCP wire protocol remains the standard protocol used by compatible clients.

The examples in `adapters/` are starting points. Merge the correct entry into the IDE's
existing MCP configuration; do not overwrite unrelated servers. Restart/reload the MCP host.

Available MCP tools:
- `arr_list_projects`
- `arr_list_modules`
- `arr_classify`
- `arr_save`
- `arr_search`

## Install portable agent instructions

Copy `AGENTS.md` into the project root. Install `skills/requirement-router/SKILL.md`
where your agent discovers Agent Skills, or copy its workflow into the IDE's native rules.
IDE support for Skills and automatic instruction discovery varies by product and version.

## Example agent workflow

User:
> Danh sách học viên: hãy thêm cột ngày sinh và lọc theo chi nhánh.

Agent:
1. Resolve current workspace to `hero-english-crm`.
2. Read module registry and search existing requirements.
3. Semantically choose `students`.
4. Call `arr_classify(project_id, request_text, ai_module="students", ai_type="ui")`.
5. If classified, call `arr_save(...)` with a concise title, faithful description, acceptance
   criteria, and optional related modules.
6. Report `REQ-STU-0001` and the target Markdown path.

A request "add teacher-in-charge column to student list" remains primarily `students`;
`teachers` can be included as a related module.

## Classification and confidence

The AI agent provides semantic module selection. The server verifies:
- the module exists in the project's module registry
- destination path is relative and stays inside project root
- deterministic aliases/rules do not contradict the selection
- confidence/ambiguity gates

The server never trusts an arbitrary filesystem path from the agent.

## Requirement format

Each saved item includes:
- unique module-scoped ID
- timestamp
- project, module, type, status
- related modules
- description
- acceptance criteria
- original user request
- duplicate fingerprint marker

Files are append-only in v2.0.0. For changes to an existing requirement, add a follow-up
requirement that references the previous ID. A reviewed edit/update API is planned separately.

## Git workflow

```powershell
git add .requirement-router/modules.json requirements AGENTS.md
git commit -m "docs(requirements): capture new requirements"
```

The router never commits or pushes automatically.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Security model

- Local-only file operations
- Registered projects only
- Module destinations must be relative to project root
- Path traversal is rejected
- Writes are atomic
- No auto commit/push/delete
- No telemetry
- Review MCP configuration before enabling write-capable tools in an IDE

## Compatibility

MCP-compatible clients can call the tools. Agent Skills-compatible clients can reuse the
same `SKILL.md`. Other clients can use the generic adapter pattern. Native instruction
loading and MCP configuration formats vary; see `adapters/`.

## License

Apache-2.0. Contributions are welcome.
