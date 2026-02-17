"""Output formatting and display utilities."""
from datetime import datetime
from uuid import UUID

from rich.console import Console
from rich.table import Table

from mimir.models import Branch, ContextCommit, Task

console = Console()


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✓ {message}[/bold green]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]✗ {message}[/bold red]")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[bold yellow]ⓘ {message}[/bold yellow]")


def print_dim(message: str) -> None:
    """Print dim message."""
    console.print(f"[dim]{message}[/dim]")


def format_load_uncertainty(load: int | None, unc: int | None) -> str:
    """Format cognitive load and uncertainty metrics."""
    if load is None and unc is None:
        return "—"
    load_str = str(load) if load is not None else "—"
    unc_str = str(unc) if unc is not None else "—"
    return f"{load_str}/{unc_str}"


def print_task_created(task: Task) -> None:
    """Print task creation confirmation."""
    print_success(f"Created task: {task.name}")
    print_dim(f"  ID: {task.id}")
    print_dim(f"  Main branch created")


def print_commit_created(commit: ContextCommit, branch_name: str) -> None:
    """Print commit creation confirmation."""
    print_success(f"Created commit: {commit.message}")
    print_dim(f"  ID: {commit.id}")
    print_dim(f"  Branch: {branch_name}")
    print_dim(f"  Author: {commit.author}")
    if commit.cognitive_load is not None:
        print_dim(f"  Cognitive Load: {commit.cognitive_load}")
    if commit.uncertainty is not None:
        print_dim(f"  Uncertainty: {commit.uncertainty}")


def print_branch_created(name: str, from_branch: str | None = None) -> None:
    """Print branch creation confirmation."""
    print_success(f"Created branch: {name}")
    if from_branch:
        print_dim(f"  From: {from_branch}")


def print_branch_deleted(name: str) -> None:
    """Print branch deletion confirmation."""
    print_success(f"Deleted branch: {name}")


def print_switched(task_name: str | None = None, branch_name: str | None = None) -> None:
    """Print switch confirmation."""
    if task_name:
        print_success(f"Switched to task: {task_name}")
    if branch_name:
        print_success(f"Switched to branch: {branch_name}")


def print_branches_list(branches: list[Branch], task_name: str) -> None:
    """Print list of branches."""
    if not branches:
        print_dim("No branches found")
        return

    table = Table(title=f"Branches for {task_name}")
    table.add_column("Name", style="cyan")
    table.add_column("Head Commit", style="green")
    table.add_column("Created At", style="dim")

    for br in branches:
        commit_id = str(br.head_commit_id)[:8] if br.head_commit_id else "—"
        created = br.created_at.isoformat()[:19]
        table.add_row(br.name, commit_id, created)

    console.print(table)


def print_history_table(commits: list[ContextCommit]) -> None:
    """Print commit history as table."""
    if not commits:
        print_dim("No commits found")
        return

    table = Table(title="Commit History")
    table.add_column("Commit ID", style="cyan")
    table.add_column("Message", style="white")
    table.add_column("Author", style="green")
    table.add_column("Created At", style="dim")
    table.add_column("Load/Unc", style="yellow")

    for c in commits:
        commit_id = str(c.id)[:8]
        message = c.message[:40]
        author = c.author
        created = c.created_at.isoformat()[:19]
        load_unc = format_load_uncertainty(c.cognitive_load, c.uncertainty)
        table.add_row(commit_id, message, author, created, load_unc)

    console.print(table)


def print_commit_details(commit: ContextCommit) -> None:
    """Print full commit details."""
    console.print(f"[bold cyan]Commit:[/bold cyan] {commit.id}")
    console.print(f"[bold cyan]Message:[/bold cyan] {commit.message}")
    console.print(f"[bold cyan]Author:[/bold cyan] {commit.author}")
    console.print(f"[bold cyan]Created:[/bold cyan] {commit.created_at.isoformat()}")
    
    if commit.cognitive_load is not None:
        console.print(f"[bold cyan]Cognitive Load:[/bold cyan] {commit.cognitive_load}")
    if commit.uncertainty is not None:
        console.print(f"[bold cyan]Uncertainty:[/bold cyan] {commit.uncertainty}")

    console.print("\n[bold cyan]Context:[/bold cyan]")
    console.print(commit.full_context)


def print_context_concatenated(commits: list[ContextCommit]) -> None:
    """Print concatenated contexts with headers."""
    if not commits:
        print_dim("No commits found")
        return

    for c in commits:
        commit_id = str(c.id)[:8]
        console.rule(f"Commit {commit_id} — {c.message}")
        console.print(f"Author: {c.author}  Created: {c.created_at.isoformat()}")
        
        load_unc = format_load_uncertainty(c.cognitive_load, c.uncertainty)
        if load_unc != "—":
            console.print(f"Metrics: {load_unc}")
        
        console.print()
        console.print(c.full_context)
        console.print()


def print_status(current_task: str | None, current_branch: str | None) -> None:
    """Print current status."""
    console.print("[bold]Status:[/bold]")
    
    if current_task:
        console.print(f"  [dim]Task:[/dim] {current_task}")
    else:
        console.print(f"  [dim]Task:[/dim] [yellow](not set)[/yellow]")

    if current_branch:
        console.print(f"  [dim]Branch:[/dim] {current_branch}")
    else:
        console.print(f"  [dim]Branch:[/dim] [yellow](not set)[/yellow]")


def print_db_initialized() -> None:
    """Print database initialization success."""
    print_success("Database initialized successfully")


def print_version() -> None:
    """Print application version."""
    try:
        from mimir import __version__

        console.print(f"[bold cyan]mimir {__version__}[/bold cyan]")
    except Exception:
        console.print("[bold cyan]mimir (unknown version)[/bold cyan]")
