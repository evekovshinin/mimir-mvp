import uuid

import pytest

from mimir import handlers


def test_init_creates_db(monkeypatch):
    called = {}

    def fake_init_db(url):
        called["url"] = url

    import mimir.db.db_manager as db_manager

    monkeypatch.setattr(db_manager, "init_db", fake_init_db)

    handlers.handle_init("sqlite:///:memory:")
    assert called.get("url") == "sqlite:///:memory:"


def test_create_task_sets_state_and_creates_task(monkeypatch, patch_db_session, capture_prints):
    # prepare project lookup
    class P:
        id = 1
        name = "proj"

    class T:
        id = 10
        name = "TASK-1"

    monkeypatch.setattr(
        "mimir.services.project_service.ProjectService.get_project_by_name",
        lambda self, name: P(),
    )

    def fake_create_task(self, project_id, name, author, external_id):
        return T()

    monkeypatch.setattr(
        "mimir.services.task_service.TaskService.create_task",
        fake_create_task,
    )

    called = {}

    def fake_set_current(task_name):
        called["task"] = task_name

    from mimir import state_manager

    monkeypatch.setattr(state_manager.StateManager, "set_current_task", staticmethod(fake_set_current))

    handlers.handle_create_task(project="proj", name="TASK-1")
    assert called.get("task") == "TASK-1"


def test_commit_creates_commit(monkeypatch, patch_db_session, capture_prints):
    # prepare task lookup
    class TaskObj:
        id = 2

    monkeypatch.setattr(
        "mimir.services.task_service.TaskService.get_task_by_name",
        lambda self, name: TaskObj(),
    )

    created = {}

    def fake_create_commit(self, task_id, branch_name, message, context, author, cognitive_load=None, uncertainty=None):
        created["task_id"] = task_id
        created["branch"] = branch_name
        return type("C", (), {"id": "c1"})()

    monkeypatch.setattr(
        "mimir.services.commit_service.CommitService.create_commit",
        fake_create_commit,
    )

    handlers.handle_commit(task=None, branch=None, message="m", context_file=None, context="ctx", author="a", cognitive_load=None, uncertainty=None)
    assert created.get("task_id") == 2


def test_branch_create_calls_service(monkeypatch, patch_db_session):
    # ensure task resolution
    monkeypatch.setattr(
        "mimir.services.task_service.TaskService.get_task_by_name",
        lambda self, name: type("T", (), {"id": 3})(),
    )

    called = {}

    def fake_create_branch(self, task_id, name, from_commit_id=None):
        called["task_id"] = task_id
        called["name"] = name

    monkeypatch.setattr(
        "mimir.services.branch_service.BranchService.create_branch",
        fake_create_branch,
    )

    handlers.handle_branch(action="create", name="feature", task=None, from_branch=None)
    assert called.get("name") == "feature"


def test_branch_list_no_task_shows_hint(monkeypatch, patch_db_session, capture_prints):
    # ensure no current task
    monkeypatch.setattr("mimir.state_manager.StateManager.get_current_task", staticmethod(lambda: None))

    handlers.handle_branch_list(task=None)
    assert "print_dim" in capture_prints


def test_switch_updates_state(monkeypatch, capture_prints):
    called = {}

    def fake_set_current(task_name):
        called.setdefault("task", []).append(task_name)

    def fake_set_branch(branch_name):
        called.setdefault("branch", []).append(branch_name)

    from mimir import state_manager

    monkeypatch.setattr(state_manager.StateManager, "set_current_task", staticmethod(fake_set_current))
    monkeypatch.setattr(state_manager.StateManager, "set_current_branch", staticmethod(fake_set_branch))

    handlers.handle_switch(task="T", branch="B")
    assert called.get("task") == ["T"]
    assert called.get("branch") == ["B"]


def test_context_shows_concatenated_commits(monkeypatch, patch_db_session, capture_prints):
    # prepare task and commits
    monkeypatch.setattr(
        "mimir.services.task_service.TaskService.get_task_by_name",
        lambda self, name: type("T", (), {"id": 4})(),
    )

    monkeypatch.setattr(
        "mimir.services.commit_service.CommitService.get_commits_for_task",
        lambda self, task_id: [type("C", (), {"id": 1})(), type("C", (), {"id": 2})()],
    )

    handlers.handle_context(task="T", branch=None, reverse=False)
    assert "print_context_concatenated" in capture_prints


def test_history_shows_commits(monkeypatch, patch_db_session, capture_prints):
    monkeypatch.setattr(
        "mimir.services.task_service.TaskService.get_task_by_name",
        lambda self, name: type("T", (), {"id": 5})(),
    )

    monkeypatch.setattr(
        "mimir.services.commit_service.CommitService.get_history",
        lambda self, task_id, branch, limit: [1, 2, 3],
    )

    handlers.handle_history(task="T", branch=None, limit=10)
    assert "print_history_table" in capture_prints


def test_show_valid_uuid_shows_commit(monkeypatch, patch_db_session, capture_prints):
    test_uuid = str(uuid.uuid4())

    monkeypatch.setattr(
        "mimir.services.commit_service.CommitService.get_commit",
        lambda self, cid: type("C", (), {"id": cid})(),
    )

    handlers.handle_show(test_uuid)
    assert "print_commit_details" in capture_prints


def test_status_outputs_current_state(monkeypatch, capture_prints):
    monkeypatch.setattr("mimir.state_manager.StateManager.get_current_task", staticmethod(lambda: "X"))
    monkeypatch.setattr("mimir.state_manager.StateManager.get_current_branch", staticmethod(lambda: "Y"))

    handlers.handle_status()
    assert "print_status" in capture_prints
