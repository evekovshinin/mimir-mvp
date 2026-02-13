# Архитектура Mimir

## 🏗 Обзор архитектуры

Mimir построена на принципах Git-подобной системы версионирования, но для управления когнитивным контекстом вместо кода.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  (Typer Commands: create-task, commit, branch, history)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │   TaskService    │  │ CommitService    │  │BranchService││
│  └──────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   ORM Layer (SQLAlchemy)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Task | ContextCommit | CommitParent | Branch         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              PostgreSQL Database                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  tasks | context_commits | commit_parents | branches  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Слои архитектуры

### 1. CLI Layer (mimir/cli.py)

Точка входа для пользователя. Использует Typer для построения интерфейса командной строки.

**Команды:**
- `create-task` - Создание новой задачи
- `commit` - Создание commit с контекстом
- `branch` - Управление ветками
- `switch` - Переключение текущей задачи/ветки
- `history` - Просмотр истории commits
- `show` - Показ полного контекста commit'а
- `status` - Текущее состояние

**Ответственность:**
- Парсинг аргументов и опций
- Валидация входных данных
- Обработка ошибок и форматирование вывода
- Интеграция с StateManager для текущего контекста

### 2. Service Layer (mimir/services/)

Бизнес-логика приложения. Три основных сервиса:

#### TaskService (task_service.py)
```python
class TaskService:
    def create_task(name, author) -> Task
    def get_task(task_id) -> Task | None
    def get_task_by_name(name) -> Task | None
    def list_tasks() -> list[Task]
    def delete_task(task_id) -> bool
```

**Ответственность:**
- Создание задач
- Создание main branch при создании задачи
- Базовые CRUD операции

#### CommitService (commit_service.py)
```python
class CommitService:
    def create_commit(...) -> ContextCommit
    def get_commit(commit_id) -> ContextCommit | None
    def get_commit_parents(commit_id) -> list[ContextCommit]
    def get_history(task_id, branch_name) -> list[ContextCommit]
    def merge_commit(...) -> ContextCommit
```

**Ответственность:**
- Создание commits (с автоматической связью к родителю)
- Управление CommitParent отношениями
- Обновление branch head при создании commit
- Получение истории через recursive CTE
- Поддержка merge commits

**Ключевая логика:**
```python
# При создании commit:
1. Проверить что branch существует
2. Если branch.head_commit_id не null:
   - Создать CommitParent(child_id=new_commit, parent_id=old_head)
3. Обновить branch.head_commit_id = new_commit.id
```

#### BranchService (branch_service.py)
```python
class BranchService:
    def create_branch(task_id, name, from_commit_id) -> Branch
    def get_branch(task_id, name) -> Branch | None
    def list_branches(task_id) -> list[Branch]
    def delete_branch(task_id, name) -> bool
    def rename_branch(task_id, old_name, new_name) -> Branch | None
```

**Ответственность:**
- Создание и удаление веток
- Валидация уникальности имен веток в контексте задачи
- Защита main branch от удаления
- Переименование веток

### 3. ORM Layer (mimir/models.py)

SQLAlchemy моделины описывают структуру данных и связи.

#### Task
```python
class Task:
    id: UUID          # Primary Key
    name: str         # Unique
    created_at: datetime
    
    # Relationships
    commits: list[ContextCommit]
    branches: list[Branch]
```

#### ContextCommit (immutable)
```python
class ContextCommit:
    id: UUID          # Primary Key
    task_id: UUID     # Foreign Key to Task
    message: str
    full_context: str  # Immutable snapshot
    author: str
    cognitive_load: int | None   # 0-10
    uncertainty: int | None      # 0-10
    created_at: datetime
    
    # Relationships
    task: Task
    parents: list[ContextCommit]  # Via CommitParent
    branches: list[Branch]        # Commits where this is head
```

#### CommitParent (junction table)
```python
class CommitParent:
    child_id: UUID    # Foreign Key, Part of PK
    parent_id: UUID   # Foreign Key, Part of PK
    
    # Enforces:
    # - No cycles (logically)
    # - Unique constraint (child_id, parent_id)
    # - Supports multiple parents (merge)
```

#### Branch (pointer)
```python
class Branch:
    id: UUID
    task_id: UUID     # Foreign Key to Task
    name: str
    head_commit_id: UUID | None  # Foreign Key to ContextCommit
    created_at: datetime
    
    # Relationships
    task: Task
    head_commit: ContextCommit | None
    
    # Constraints:
    # - Unique (task_id, name)
    # - Can be null before first commit
```

## 🔄 Data Flow

### Поток создания commit

```
CLI (commit command)
    ↓
CommitService.create_commit()
    ↓
1. Verify task exists
2. Get branch
3. Create ContextCommit instance
4. session.add(commit)
5. session.flush()  ← Get commit.id
    ↓
6. If branch.head_commit_id is not None:
     Create CommitParent(child_id=commit.id, parent_id=branch.head_commit_id)
    ↓
7. Update branch.head_commit_id = commit.id
    ↓
8. session.commit()  ← Write to DB
    ↓
CLI (show success message)
```

### Поток получения истории

```
CLI (history command)
    ↓
CommitService.get_history(task_id, branch_name)
    ↓
1. Get branch from DB
    ↓
2. Execute recursive CTE:

    WITH RECURSIVE commit_history AS (
        -- Base: Start from branch head
        SELECT * FROM context_commits WHERE id = branch.head_commit_id
        UNION ALL
        -- Recursive: Get parents
        SELECT cc.* FROM context_commits cc
        JOIN commit_parents cp ON cc.id = cp.parent_id
        JOIN commit_history ch ON cp.child_id = ch.id
        WHERE depth < limit
    )
    SELECT * FROM commit_history ORDER BY depth
    
    ↓
3. Convert SQL rows to ContextCommit objects
    ↓
CLI (display table)
```

## 💾 Database Schema

### Tables

```sql
-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- Context Commits (immutable)
CREATE TABLE context_commits (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id),
    message VARCHAR(512) NOT NULL,
    full_context TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    cognitive_load SMALLINT,
    uncertainty SMALLINT,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX ix_context_commits_task_id ON context_commits(task_id);

-- Commit Parents (DAG edges)
CREATE TABLE commit_parents (
    child_id UUID PRIMARY KEY REFERENCES context_commits(id),
    parent_id UUID PRIMARY KEY REFERENCES context_commits(id),
    UNIQUE(child_id, parent_id)
);

-- Branches (pointers)
CREATE TABLE branches (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id),
    name VARCHAR(255) NOT NULL,
    head_commit_id UUID REFERENCES context_commits(id),
    created_at TIMESTAMP NOT NULL,
    UNIQUE(task_id, name)
);
CREATE INDEX ix_branches_task_id ON branches(task_id);
CREATE INDEX ix_branches_head_commit_id ON branches(head_commit_id);
```

## 🔐 Constraints and Validation

### Database Constraints

1. **Task.name** - UNIQUE (no duplicate task names)
2. **Branch.name** - UNIQUE per (task_id, name) pair
3. **CommitParent** - UNIQUE(child_id, parent_id)
4. **Foreign Keys** - Ensure referential integrity

### Application Logic Constraints

1. **No cycles** - CommitParent must not form cycles
   - Logically enforced (recursive CTE limits)
   - Could be enhanced with cycle detection

2. **Main branch protection** - Cannot delete "main" branch
   - Validated in BranchService.delete_branch()

3. **Immutability** - ContextCommit is immutable after creation
   - No UPDATE operations on context_commits table

4. **Branch must belong to task** - Validated before operations
   - All branch operations check task_id -> branch.task_id

## 🔌 Local State Management

### StateManager (state_manager.py)

Хранит текущий контекст пользователя локально в `~/.mimir/state.json`:

```python
class StateManager:
    @staticmethod
    def load() -> dict
    @staticmethod
    def save(state: dict) -> None
    @staticmethod
    def set_current_task(task_name: str) -> None
    @staticmethod
    def get_current_task() -> str | None
    @staticmethod
    def get_current_branch() -> str | None
```

**Использование:**
- Запоминает последнюю использованную задачу и ветку
- Позволяет опускать --task и --branch флаги в CLI командах
- Персистентна между выполнениями программы

## 🧪 Testing Architecture

### Test Structure (tests/test_services.py)

Использует pytest с in-memory SQLite базой:

```python
@pytest.fixture
def db_session():
    """Use SQLite :memory: for testing"""
    db_manager = DatabaseManager("sqlite:///:memory:")
    Base.metadata.create_all(db_manager.engine)
    session = db_manager.get_session()
    yield session
    session.close()

@pytest.fixture
def commit_service(db_session):
    return CommitService(db_session)
```

**Тесты покрывают:**
- TaskService: create, get, list, delete operations
- CommitService: create with parent, history, validation
- BranchService: create, list, delete, rename, main branch protection

## 🚀 Deployment & Operations

### Database Initialization

```python
# Alembic migration process
1. Tables created by 001_initial.py migration
2. Indexes created automatically
3. Constraints enforced at DB level
```

### Configuration

```python
# DatabaseManager in db.py
engine = create_engine(
    database_url,
    echo=settings.database_echo,  # For debugging
    future=True,  # SQLAlchemy 2.0 style
)
```

### Error Handling

```
CLI Command → Service Layer → ORM Layer
    ↓
ValueError raised in Service
    ↓
CLI catches and displays user-friendly message
    ↓
Logging to console and log file
```

## 🔄 Extension Points

### Adding a new service

1. Create `mimir/services/new_service.py`
2. Implement service class with business logic
3. Inject `Session` in constructor
4. Register in `cli.py` get_services()

### Adding a new command

1. Add `@app.command()` function in `cli.py`
2. Use services to perform operations
3. Use `console.print()` for output with Rich formatting
4. Catch exceptions and display errors

### Adding metrics

1. Extend ContextCommit model with new columns
2. Create Alembic migration
3. Update CommitService.create_commit() to accept new parameter
4. Update CLI command to expose new options

## 📈 Scalability Considerations

### Current Limitations

- Single PostgreSQL instance (no sharding)
- Recursive CTE limited by depth parameter (safety)
- Full context stored as TEXT (not indexed)

### Future Optimizations

- Full-text search on context field
- Partitioning by task_id
- Caching of recent commits
- Connection pooling tuning
- Query result pagination

## 🔗 Dependency Injection

```python
# Services receive Session via constructor
def get_services():
    session = db_manager.get_session()
    return {
        "task_service": TaskService(session),
        "commit_service": CommitService(session),
        "branch_service": BranchService(session),
        "session": session,
    }
```

This enables:
- Easy testing (inject mock/memory session)
- Clean separation of concerns
- Transaction management
- Session cleanup

---

**Архитектура готова к расширению!** 🚀
