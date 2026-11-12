import json
from pathlib import Path

import pytest

from requirement_router import core


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "APP_HOME", tmp_path / "home")
    monkeypatch.setattr(core, "REGISTRY_PATH", tmp_path / "home" / "projects.json")
    project = tmp_path / "crm"
    project.mkdir()
    core.register_project("demo-crm", "Demo CRM", str(project))
    return project


def test_register_and_classify_student(isolated_home):
    result = core.classify("demo-crm", "Danh sách học viên: thêm cột ngày sinh")
    assert result["status"] == "classified"
    assert result["module"] == "students"


def test_semantic_module_is_validated(isolated_home):
    result = core.classify("demo-crm", "Bổ sung field phone", ai_module="teachers")
    assert result["status"] == "classified"
    assert result["module"] == "teachers"
    unknown = core.classify("demo-crm", "Bổ sung field phone", ai_module="billing")
    assert unknown["status"] == "needs_clarification"


def test_save_and_duplicate(isolated_home):
    kwargs = dict(
        project_id="demo-crm",
        request_text="Danh sách học viên: thêm cột ngày sinh",
        ai_module="students",
        title="Thêm cột ngày sinh",
        description="Hiển thị ngày sinh trong danh sách học viên.",
        ai_type="ui",
        acceptance_criteria=["Hiển thị ngày sinh", "Định dạng dd/MM/yyyy"],
    )
    first = core.save_requirement(**kwargs)
    second = core.save_requirement(**kwargs)
    assert first["status"] == "saved"
    assert first["requirement_id"] == "REQ-STU-0001"
    assert second["status"] == "duplicate"
    assert Path(first["file"]).is_file()


def test_reject_path_traversal(isolated_home):
    config = isolated_home / ".requirement-router" / "modules.json"
    data = json.loads(config.read_text(encoding="utf-8"))
    data["modules"][0]["file"] = "../../outside.md"
    config.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(core.UnsafePath):
        core.get_modules(core.get_project("demo-crm"))


def test_search(isolated_home):
    core.save_requirement("demo-crm", "Danh sách học viên: thêm cột ngày sinh",
                          "students", title="Ngày sinh")
    result = core.search_requirements("demo-crm", "ngày sinh")
    assert result["results"]
