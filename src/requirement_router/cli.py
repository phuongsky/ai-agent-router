from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from . import core


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arr", description="AI Requirement Router")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    reg = sub.add_parser("register", help="Register a local project")
    reg.add_argument("--id", required=True)
    reg.add_argument("--name", default="")
    reg.add_argument("--path", required=True)

    sub.add_parser("list", help="List registered projects")

    modules = sub.add_parser("modules", help="List modules in a project")
    modules.add_argument("--project", required=True)

    classify = sub.add_parser("classify", help="Rule-only classification test")
    classify.add_argument("--project", required=True)
    classify.add_argument("--text", required=True)
    classify.add_argument("--module", default="")
    classify.add_argument("--type", default="feature")

    search = sub.add_parser("search", help="Search saved requirements")
    search.add_argument("--project", required=True)
    search.add_argument("--query", required=True)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "register":
            result = core.register_project(args.id, args.name, args.path)
        elif args.command == "list":
            result = {"registry": str(core.REGISTRY_PATH), "projects": core.get_projects()}
        elif args.command == "modules":
            project = core.get_project(args.project)
            result = {"project_id": args.project, "modules": core.get_modules(project)}
        elif args.command == "classify":
            result = core.classify(args.project, args.text, args.module, args.type)
        elif args.command == "search":
            result = core.search_requirements(args.project, args.query)
        else:
            raise SystemExit(2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except core.RouterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
