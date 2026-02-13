"""Local state management for Mimir."""
import json
import logging
from pathlib import Path
from typing import Any

from mimir.config import STATE_FILE

logger = logging.getLogger(__name__)


class StateManager:
    """Manages local state in ~/.mimir/state.json."""

    @staticmethod
    def load() -> dict[str, Any]:
        """Load state from file."""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state: {e}")
        return {"current_task": None, "current_branch": None}

    @staticmethod
    def save(state: dict[str, Any]) -> None:
        """Save state to file."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
            logger.debug(f"State saved to {STATE_FILE}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    @staticmethod
    def set_current_task(task_name: str) -> None:
        """Set current task."""
        state = StateManager.load()
        state["current_task"] = task_name
        StateManager.save(state)
        logger.info(f"Current task set to: {task_name}")

    @staticmethod
    def set_current_branch(branch_name: str) -> None:
        """Set current branch."""
        state = StateManager.load()
        state["current_branch"] = branch_name
        StateManager.save(state)
        logger.info(f"Current branch set to: {branch_name}")

    @staticmethod
    def get_current_task() -> str | None:
        """Get current task."""
        state = StateManager.load()
        return state.get("current_task")

    @staticmethod
    def get_current_branch() -> str | None:
        """Get current branch."""
        state = StateManager.load()
        return state.get("current_branch")
