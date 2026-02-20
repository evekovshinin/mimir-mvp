import pytest


class DummySession:
    def __init__(self):
        self.committed = False
        self.closed = False

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


@pytest.fixture
def dummy_session():
    return DummySession()


@pytest.fixture(autouse=True)
def patch_db_session(monkeypatch, dummy_session):
    """Patch db_manager.get_session to return a lightweight dummy session."""
    import mimir.db.db_manager as db_manager

    monkeypatch.setattr(db_manager, "get_session", lambda: dummy_session)
    yield dummy_session


@pytest.fixture
def capture_prints(monkeypatch):
    """Replace mimir.output print helpers with call-capturing stubs."""
    calls = {}

    def make_stub(name):
        def stub(*args, **kwargs):
            calls.setdefault(name, []).append((args, kwargs))

        return stub

    import mimir.output as output

    for fn in [
        "print_error",
        "print_success",
        "print_task_created",
        "print_commit_created",
        "print_branch_created",
        "print_branch_deleted",
        "print_switched",
        "print_branches_list",
        "print_history_table",
        "print_commit_details",
        "print_context_concatenated",
        "print_status",
        "print_db_initialized",
        "print_dim",
        "print_tasks_list",
    ]:
        monkeypatch.setattr(output, fn, make_stub(fn))

    return calls
