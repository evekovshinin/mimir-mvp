# Development Guide

## 👨‍💻 Working on Mimir

### Project Structure

```
mimir-mvp/
├── mimir/
│   ├── __init__.py          # Package exports
│   ├── cli.py               # CLI entry point (Typer)
│   ├── config.py            # Settings & logging
│   ├── db.py                # Database manager
│   ├── models.py            # SQLAlchemy ORM models
│   ├── state_manager.py     # Local ~/.mimir/state.json manager
│   └── services/
│       ├── __init__.py
│       ├── task_service.py  # Task CRUD
│       ├── commit_service.py # Commit operations & history
│       └── branch_service.py # Branch management
│
├── alembic/                 # Database migrations
│   ├── env.py
│   └── versions/
│       └── 001_initial.py   # Initial schema
│
├── tests/
│   ├── __init__.py
│   └── test_services.py     # Pytest tests
│
├── pyproject.toml           # Dependencies
├── alembic.ini              # Alembic config
├── .env.example             # Environment template
└── .gitignore

```

### Development Setup

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Create .env from example
cp .env.example .env

# 3. Adjust DATABASE_URL if needed
# DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/mimir_db

# 4. Initialize database
mimir init

# 5. Run tests to verify everything
pytest tests/ -v
```

### Running Tests

```bash
# All tests
pytest tests/

# Verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=mimir --cov-report=html

# Specific test
pytest tests/test_services.py::TestTaskService::test_create_task -v

# Watch mode (if pytest-watch installed)
ptw tests/
```

### Code Style

We follow Python 3.11+ conventions:

```bash
# Format code
black mimir/ tests/

# Lint
ruff check mimir/ tests/

# Type checking
mypy mimir/

# All in one
black mimir/ tests/ && ruff check mimir/ tests/ && mypy mimir/
```

### Adding New Features

#### 1. Adding a New Service

**Example: DocumentService**

```python
# mimir/services/document_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from mimir.models import Document

class DocumentService:
    def __init__(self, session: Session):
        self.session = session

    def create_document(self, task_id: UUID, commit_id: UUID, name: str) -> Document:
        """Create a document attached to a commit."""
        doc = Document(
            task_id=task_id,
            commit_id=commit_id,
            name=name,
        )
        self.session.add(doc)
        return doc
```

1. Create model in `models.py`
2. Create service in `services/`
3. Add tests in `tests/test_services.py`
4. Create migration in `alembic/versions/`
5. Update CLI command in `cli.py`

#### 2. Adding a New CLI Command

**Example: Show current branch details**

```python
# In mimir/cli.py

@app.command()
def branches(
    task: Optional[str] = typer.Option(None, "--task", help="Task name"),
) -> None:
    """Show all branches for a task."""
    try:
        task_name = task or StateManager.get_current_task()
        if not task_name:
            console.print("[red]Error: No task specified[/red]")
            raise typer.Exit(1)

        services = get_services()
        task_obj = services["task_service"].get_task_by_name(task_name)
        
        if not task_obj:
            console.print(f"[red]Error: Task '{task_name}' not found[/red]")
            raise typer.Exit(1)

        branches = services["branch_service"].list_branches(task_obj.id)
        
        # Display with Rich
        table = Table(title=f"Branches for {task_name}")
        table.add_column("Name")
        table.add_column("Head Commit")
        
        for branch in branches:
            table.add_row(branch.name, str(branch.head_commit_id)[:8] if branch.head_commit_id else "—")
        
        console.print(table)
        
    except Exception as e:
        logger.exception("Error in branches command")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

1. Add `@app.command()` function
2. Use services for business logic
3. Use `console.print()` for output (Rich formatting)
4. Handle exceptions and log errors
5. Test with `pytest`

#### 3. Adding a Database Migration

```bash
# Create new migration (autogenerate if possible)
alembic revision --autogenerate -m "Add documents table"

# Edit alembic/versions/002_*.py with SQL

# Test the migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

#### 4. Adding Tests

```python
# In tests/test_services.py

class TestNewService:
    def test_new_feature(self, db_session):
        """Test new feature."""
        service = NewService(db_session)
        result = service.some_method()
        
        assert result is not None
        assert result.property == expected_value
        
        db_session.commit()
```

### Common Tasks

#### Can't connect to PostgreSQL

```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Check DATABASE_URL in .env
grep DATABASE_URL .env

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### Migrations not applied

```bash
# Check current migration status
alembic current

# Check migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Downgrade by 1 step
alembic downgrade -1
```

#### Reset database (for development only!)

```bash
# Drop and recreate
dropdb mimir_db
createdb mimir_db

# Re-apply migrations
alembic upgrade head

# Or use the CLI
mimir init
```

#### Debug a test

```bash
# Run with print statements visible
pytest tests/test_services.py::TestName::test_method -v -s

# Or use pdb
import pdb; pdb.set_trace()  # In your test code
```

### Architecture Review Checklist

When adding new features, ensure:

- [ ] **Models**: Proper relationships, constraints, indexes
- [ ] **Services**: Single responsibility, clear error handling
- [ ] **CLI**: User-friendly error messages, proper formatting
- [ ] **Tests**: Unit tests for services, integration tests if needed
- [ ] **Docs**: Update README/ARCHITECTURE if needed
- [ ] **Migrations**: SQL migrations are idempotent
- [ ] **Logging**: Proper log levels, useful context
- [ ] **Type hints**: Full type coverage (mypy compliant)

### Performance Considerations

**Current bottlenecks:**
- Full context stored as TEXT (not indexed)
- Recursive CTE with no optimization
- No query result caching

**Optimization opportunities:**
1. Add full-text search index on `context_commits.full_context`
2. Add pagination to `history()` method
3. Cache recent commits
4. Connection pooling optimization
5. Partition tables by `task_id`

### Debugging Tips

```python
# Enable SQL logging
settings.database_echo = True

# Add logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable: {var}")

# Use SQLAlchemy inspector
from sqlalchemy import inspect
inspector = inspect(engine)
inspector.get_table_names()

# Check relationships
for parent in commit.parents:
    print(parent.id)
```

### Git Workflow Recommendation

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, add tests
# ...

# Run full test suite
pytest tests/ --cov=mimir

# Format and lint
black mimir/ && ruff check mimir/

# Commit
git add .
git commit -m "Add your feature"

# Push
git push origin feature/your-feature

# Create PR
# ... (GitHub UI)
```

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.10.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [sqlalchemy, typer]
EOF

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Documentation Standards

When writing docstrings:

```python
def create_commit(
    self,
    task_id: UUID,
    branch_name: str,
    message: str,
    context: str,
) -> ContextCommit:
    """Create a new commit on a branch.
    
    Args:
        task_id: The UUID of the task
        branch_name: Name of the branch
        message: Commit message
        context: Full context content
        
    Returns:
        Created ContextCommit object
        
    Raises:
        ValueError: If task or branch not found
        
    Example:
        >>> commit = service.create_commit(
        ...     task_id=uuid.uuid4(),
        ...     branch_name="main",
        ...     message="Initial context",
        ...     context="Details...",
        ... )
    """
```

### Performance Testing

```bash
# Load testing with locust (if added to dependencies)
pip install locust

# Create locustfile.py
# Run tests
locust -f locustfile.py
```

### Security Considerations

- [ ] SQL injection: Use SQLAlchemy ORM (prevents by design)
- [ ] SQL injection in raw queries: Use parameterized queries
- [ ] Access control: Implement if multi-user needed
- [ ] Input validation: Validate in services before DB
- [ ] Logging: Don't log sensitive data
- [ ] Secrets: Use environment variables, never hardcode

---

Happy coding! 🚀
