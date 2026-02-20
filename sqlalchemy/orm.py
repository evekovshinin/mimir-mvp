"""Minimal sqlalchemy.orm shim for tests.

Provides `Session`, `sessionmaker`, `DeclarativeBase`, `Mapped`, `mapped_column`,
and `relationship` used by `mimir.models` and `mimir.db`.
"""

from typing import Any


class Session:
    pass


def sessionmaker(bind=None, class_=None, expire_on_commit=True):
    """Return a factory that produces Session instances.

    This is intentionally tiny and only suitable for unit tests that mock
    actual DB operations.
    """

    def factory():
        return Session()

    return factory


class DeclarativeBase:
    """Placeholder base class for declarative mappings."""


class Mapped:
    @classmethod
    def __class_getitem__(cls, item):
        return cls


def mapped_column(*args, **kwargs):
    """Placeholder for mapped_column - returns None (annotation-only)."""
    return None


def relationship(*args, **kwargs):
    """Placeholder for relationship - returns None."""
    return None
