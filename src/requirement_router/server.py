from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import core

mcp = FastMCP("ai-requirement-router")


@mcp.tool()
def arr_list_projects() -> dict:
    """List registered projects and their availability."""
    items = []
    for project in core.get_projects():
        from pathlib import Path
        root = Path(project["root"]).expanduser()
        items.append({
            "id": project["id"], "name": project.get("name", project["id"]),
            "root": str(root), "enabled": project.get("enabled", True),
            "exists": root.is_dir()
        })
    return {"registry": str(core.REGISTRY_PATH), "projects": items}


@mcp.tool()
def arr_list_modules(project_id: str) -> dict:
    """List configured requirement modules for a registered project."""
    project = core.get_project(project_id)
    return {"project_id": project_id, "modules": [
        {"id": m["id"], "name": m.get("name", m["id"]), "file": m["file"],
         "aliases": m.get("aliases", [])}
        for m in core.get_modules(project)
    ]}


@mcp.tool()
def arr_classify(project_id: str, request_text: str,
                 ai_module: str = "", ai_type: str = "feature") -> dict:
    """Hybrid classification: agent semantic choice validated by local module rules."""
    return core.classify(project_id, request_text, ai_module, ai_type)


@mcp.tool()
def arr_save(project_id: str, request_text: str, ai_module: str,
             title: str = "", description: str = "", ai_type: str = "feature",
             acceptance_criteria: list[str] | None = None,
             related_modules: list[str] | None = None) -> dict:
    """Validate and append a requirement to its registered Markdown destination."""
    return core.save_requirement(project_id, request_text, ai_module, title, description,
                                 ai_type, acceptance_criteria, related_modules)


@mcp.tool()
def arr_search(project_id: str, query: str, limit: int = 20) -> dict:
    """Search requirement Markdown files in a registered project."""
    return core.search_requirements(project_id, query, limit)


def main() -> None:
    core.ensure_home()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
