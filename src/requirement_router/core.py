from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_HOME = Path(os.environ.get(
    "ARR_HOME",
    str(Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "AIRequirementRouter")
)).expanduser().resolve()
REGISTRY_PATH = APP_HOME / "projects.json"
CONFIG_NAME = ".requirement-router"
MODULES_NAME = "modules.json"
MIN_RULE_CONFIDENCE = 0.45


class RouterError(Exception):
    """Base error for user-actionable router errors."""


class ProjectNotFound(RouterError):
    pass


class InvalidConfiguration(RouterError):
    pass


class UnsafePath(RouterError):
    pass


def now_local() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFD", text.casefold())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = value.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def fingerprint(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:20]


def ensure_home() -> None:
    APP_HOME.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        write_json_atomic(REGISTRY_PATH, {"schema_version": 1, "projects": []})


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidConfiguration(f"Cannot read JSON file {path}: {exc}") from exc


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def load_registry() -> dict[str, Any]:
    ensure_home()
    data = read_json(REGISTRY_PATH, {"schema_version": 1, "projects": []})
    if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
        raise InvalidConfiguration(f"Invalid registry schema: {REGISTRY_PATH}")
    return data


def save_registry(data: dict[str, Any]) -> None:
    write_json_atomic(REGISTRY_PATH, data)


def register_project(project_id: str, name: str, path: str) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise RouterError(f"Project directory does not exist: {root}")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{1,63}", project_id):
        raise RouterError("project_id must be 2-64 chars: letters, numbers, dot, underscore, hyphen.")
    data = load_registry()
    projects = [p for p in data["projects"] if p.get("id", "").casefold() != project_id.casefold()]
    projects.append({
        "id": project_id,
        "name": name.strip() or project_id,
        "root": str(root),
        "enabled": True,
        "modules_file": f"{CONFIG_NAME}/{MODULES_NAME}",
    })
    data["projects"] = sorted(projects, key=lambda p: p["id"].casefold())
    save_registry(data)

    config_dir = root / CONFIG_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    modules_path = config_dir / MODULES_NAME
    if not modules_path.exists():
        write_json_atomic(modules_path, default_modules())
    return {"project_id": project_id, "name": name or project_id,
            "root": str(root), "modules_file": str(modules_path)}


def default_modules() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "modules": [
            {"id": "students", "name": "Students", "file": "requirements/students/student-requirement.md",
             "aliases": ["học viên", "hoc vien", "student", "students", "danh sách học viên", "hồ sơ học viên"]},
            {"id": "teachers", "name": "Teachers", "file": "requirements/teachers/teacher-requirement.md",
             "aliases": ["giáo viên", "giao vien", "teacher", "teachers", "giảng viên"]},
            {"id": "sales", "name": "Sales", "file": "requirements/sales/sales-requirement.md",
             "aliases": ["sale", "sales", "nhân viên kinh doanh", "doanh số", "hoa hồng"]},
            {"id": "reports", "name": "Reports", "file": "requirements/reports/report-requirement.md",
             "aliases": ["báo cáo", "bao cao", "report", "reports", "thống kê", "thong ke"]},
            {"id": "permissions", "name": "Permissions", "file": "requirements/permissions/permission-requirement.md",
             "aliases": ["phân quyền", "phan quyen", "permission", "permissions", "vai trò", "role"]},
            {"id": "notifications", "name": "Notifications", "file": "requirements/notifications/notification-requirement.md",
             "aliases": ["thông báo", "thong bao", "notification", "notifications", "email", "zalo"]},
            {"id": "general", "name": "General", "file": "requirements/general/general-requirement.md",
             "aliases": ["cấu hình chung", "he thong", "hệ thống", "general", "system"]},
        ],
    }


def get_projects() -> list[dict[str, Any]]:
    return load_registry()["projects"]


def get_project(project_id: str) -> dict[str, Any]:
    for item in get_projects():
        if item.get("id", "").casefold() == project_id.casefold() and item.get("enabled", True):
            root = Path(item["root"]).expanduser().resolve()
            if not root.is_dir():
                raise ProjectNotFound(f"Registered project folder is missing: {root}")
            item = dict(item)
            item["root"] = str(root)
            return item
    raise ProjectNotFound(f"Project '{project_id}' is not registered or is disabled.")


def safe_path(root: Path, relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise UnsafePath("Only non-empty relative paths are allowed.")
    resolved_root = root.resolve()
    target = (resolved_root / relative_path).resolve()
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise UnsafePath("Target path escapes the registered project root.") from exc
    return target


def get_modules(project: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(project["root"])
    rel = project.get("modules_file", f"{CONFIG_NAME}/{MODULES_NAME}")
    path = safe_path(root, rel)
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("modules"), list):
        raise InvalidConfiguration(f"Invalid modules registry: {path}")
    modules = data["modules"]
    ids = [m.get("id", "").casefold() for m in modules]
    if len(ids) != len(set(ids)):
        raise InvalidConfiguration(f"Duplicate module IDs in {path}")
    for module in modules:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}", module.get("id", "")):
            raise InvalidConfiguration(f"Invalid module id in {path}: {module.get('id')}")
        safe_path(root, module.get("file", ""))
    return modules


def classify(project_id: str, request_text: str, ai_module: str = "",
              ai_type: str = "feature") -> dict[str, Any]:
    if not request_text.strip():
        raise RouterError("request_text cannot be empty.")
    project = get_project(project_id)
    modules = get_modules(project)
    haystack = f" {normalize(request_text)} "
    ranked: list[dict[str, Any]] = []

    for module in modules:
        matched = []
        score = 0.0
        for alias in module.get("aliases", []):
            term = normalize(alias)
            if term and f" {term} " in haystack:
                matched.append(alias)
                # More specific aliases contribute more than short generic terms.
                score += min(0.22, 0.07 + len(term.split()) * 0.035)
        score = min(score, 0.92)
        if ai_module and ai_module.casefold() == module["id"].casefold():
            score = max(score, 0.74)
            matched.append("agent-semantic-selection")
        ranked.append({"id": module["id"], "name": module.get("name", module["id"]),
                       "file": module["file"], "score": round(score, 3), "matched": matched})

    ranked.sort(key=lambda x: x["score"], reverse=True)
    ai_known = any(ai_module.casefold() == m["id"].casefold() for m in modules) if ai_module else False
    if ai_module and not ai_known:
        return {"status": "needs_clarification", "reason": f"Unknown module '{ai_module}'.",
                "available_modules": [m["id"] for m in modules]}

    top = ranked[0]
    second = ranked[1]["score"] if len(ranked) > 1 else 0.0
    selected = next((m for m in ranked if ai_module and m["id"].casefold() == ai_module.casefold()), None)

    # A semantic choice may resolve weak/noisy rules, but it must not silently
    # override a strong contradictory rule match.
    if ai_known and selected is not None:
        strongest_other = max((m["score"] for m in ranked if m["id"] != selected["id"]), default=0.0)
        if strongest_other >= 0.55 and strongest_other > selected["score"] + 0.15:
            return {
                "status": "needs_clarification", "project_id": project_id,
                "module": None, "confidence": round(strongest_other, 2),
                "reason": "Agent semantic selection conflicts with strong module keyword evidence.",
                "agent_selected_module": selected["id"],
                "rule_suggested_module": top["id"],
                "alternatives": ranked[:3],
            }
        top = selected

    confidence = max(top["score"], 0.74 if ai_known and selected is not None else 0.0)
    second = max((m["score"] for m in ranked if m["id"] != top["id"]), default=0.0)
    ambiguous = confidence < MIN_RULE_CONFIDENCE or (
        second >= 0.55 and confidence - second < 0.12 and not ai_known
    )
    return {
        "status": "needs_clarification" if ambiguous else "classified",
        "project_id": project_id,
        "module": None if ambiguous else top["id"],
        "module_name": None if ambiguous else top["name"],
        "target_file": None if ambiguous else top["file"],
        "confidence": round(confidence, 2),
        "matched_aliases": top["matched"],
        "alternatives": ranked[1:3],
        "requirement_type": ai_type,
        "reason": "Agent semantic choice validated against registered modules and local rules."
                 if ai_known and not ambiguous else
                 ("Rule-based classification." if not ambiguous else "Insufficient or conflicting evidence."),
    }


def _next_id(text: str, prefix: str) -> str:
    numbers = [int(x) for x in re.findall(rf"(?m)^## REQ-{re.escape(prefix)}-(\d{{4,}})\b", text)]
    return f"REQ-{prefix}-{max(numbers, default=0) + 1:04d}"


def save_requirement(project_id: str, request_text: str, ai_module: str, title: str = "",
                     description: str = "", ai_type: str = "feature",
                     acceptance_criteria: list[str] | None = None,
                     related_modules: list[str] | None = None) -> dict[str, Any]:
    project = get_project(project_id)
    classification = classify(project_id, request_text, ai_module, ai_type)
    if classification["status"] != "classified":
        return classification

    modules = get_modules(project)
    module = next(m for m in modules if m["id"].casefold() == classification["module"].casefold())
    allowed = {m["id"] for m in modules}
    related = [m for m in (related_modules or []) if m in allowed and m != module["id"]]
    root = Path(project["root"])
    target = safe_path(root, module["file"])
    target.parent.mkdir(parents=True, exist_ok=True)

    fp = fingerprint(request_text)
    marker = f"<!-- arr-fingerprint:{fp} -->"
    current = target.read_text(encoding="utf-8") if target.exists() else f"# {module.get('name', module['id'])} Requirements\n"
    if marker in current:
        return {"status": "duplicate", "project_id": project_id, "module": module["id"],
                "file": str(target), "fingerprint": fp, "message": "Exact request already saved."}

    normalized_source = normalize(request_text)
    if normalized_source and normalized_source in normalize(current):
        return {"status": "possible_duplicate", "project_id": project_id, "module": module["id"],
                "file": str(target), "fingerprint": fp,
                "message": "Similar source text found; no write performed."}

    prefix = re.sub(r"[^A-Z0-9]", "", module["id"].upper())[:3] or "GEN"
    req_id = _next_id(current, prefix)
    clean_title = (title or request_text.strip().splitlines()[0])[:160]
    criteria = acceptance_criteria or ["Clarify measurable acceptance criteria."]
    criteria_md = "\n".join(f"- [ ] {item.strip()}" for item in criteria if item.strip())
    if not criteria_md:
        criteria_md = "- [ ] Clarify measurable acceptance criteria."
    related_text = ", ".join(related) if related else "None"
    quoted = "\n".join("> " + line for line in request_text.strip().splitlines())
    block = f"""

{marker}
## {req_id}: {clean_title}

- **Created:** {now_local()}
- **Project:** {project_id}
- **Module:** {module['id']}
- **Type:** {ai_type}
- **Status:** Pending
- **Related modules:** {related_text}

### Description
{description.strip() or request_text.strip()}

### Acceptance Criteria
{criteria_md}

### Original Request
{quoted}

---
"""
    # Atomic replace avoids partial writes if process exits mid-write.
    temp = target.with_name(target.name + ".arr-tmp")
    temp.write_text(current.rstrip() + block, encoding="utf-8", newline="\n")
    os.replace(temp, target)
    return {"status": "saved", "project_id": project_id, "module": module["id"],
            "requirement_id": req_id, "file": str(target), "fingerprint": fp,
            "classification_confidence": classification["confidence"]}


def search_requirements(project_id: str, query: str, limit: int = 20) -> dict[str, Any]:
    project = get_project(project_id)
    root = Path(project["root"])
    needle = normalize(query)
    results = []
    for module in get_modules(project):
        path = safe_path(root, module["file"])
        if not path.is_file():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if needle and needle in normalize(line):
                results.append({"module": module["id"], "file": str(path),
                                "line": line_no, "text": line.strip()})
                if len(results) >= max(1, min(limit, 100)):
                    return {"results": results}
    return {"results": results}
