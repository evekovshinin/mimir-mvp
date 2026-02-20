"""Common utilities for handlers: session management and helpers."""
from __future__ import annotations

import functools
import logging
from typing import Any, Callable

from mimir.db import db_manager
from mimir.output import print_error
from mimir.state_manager import StateManager

logger = logging.getLogger(__name__)


def with_session(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: provide a DB session as kwarg `session` and ensure close.

    The wrapped function should accept a kwarg named `session`.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = db_manager.get_session()
        try:
            kwargs.setdefault("session", session)
            return func(*args, **kwargs)
        except ValueError:
            # propagate domain errors for CLI layer to handle
            raise
        except Exception as e:
            logger.exception("Unexpected error in handler %s", func.__name__)
            print_error(str(e))
            raise
        finally:
            try:
                session.close()
            except Exception:
                pass

    return wrapper


def resolve_task_name(task_opt: str | None) -> str | None:
    """Return explicit task name or current task from StateManager."""
    return task_opt or StateManager.get_current_task()


def require_task_name(task_name: str | None) -> str:
    """Ensure task name exists, otherwise print error and raise ValueError."""
    if not task_name:
        print_error("Task not specified")
        raise ValueError("Task required")
    return task_name
