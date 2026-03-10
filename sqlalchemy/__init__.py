"""Minimal local shim for tests to import parts of SQLAlchemy used in the tests.

This shim provides a very small subset of the public API expected by
`mimir.db`: `create_engine` and the `orm` submodule with `Session` and
`sessionmaker`.
"""
from . import orm


class _DummyEngine:
	def __init__(self, url, **kwargs):
		self.url = url


def create_engine(url, **kwargs):
	return _DummyEngine(url, **kwargs)


__all__ = ["orm", "create_engine"]

# Lightweight placeholders for symbols imported by mimir.models
def ForeignKey(target):
	return target


SmallInteger = int


def String(length=None):
	return str


Text = str


class UniqueConstraint:
	def __init__(self, *args, **kwargs):
		pass


class _Event:
	@staticmethod
	def listen(*args, **kwargs):
		return None


event = _Event()


def and_(*conds):
	return ("AND", conds)


def select(*args, **kwargs):
	return ("SELECT", args)


def text(s: str):
	return s
