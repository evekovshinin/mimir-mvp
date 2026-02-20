from mimir.output import print_status
from mimir.state_manager import StateManager


def handle_status() -> None:
    """Show current status."""
    current_task = StateManager.get_current_task()
    current_branch = StateManager.get_current_branch()
    print_status(current_task, current_branch)
