# Быстрый старт Mimir

## Предварительные требования

- Python 3.11+
- PostgreSQL 14+
- pip/venv

## 1️⃣ Установка

### Клонируем и входим в проект

```bash
cd mimir-mvp
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Устанавливаем зависимости

```bash
pip install -e ".[dev]"
```

## 2️⃣ Настройка БД

### Создаем БД в PostgreSQL

```bash
createdb mimir_db
```

### Создаем .env

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/mimir_db
LOG_LEVEL=INFO
```

### Инициализируем БД

```bash
mimir init
```

## 3️⃣ Первые шаги

### Создаем задачу

```bash
mimir create-task "TASK-42"
```

### Создаем commit с контекстом

```bash
# Создаем файл контекста
cat > context.txt << 'EOF'
# Architecture Design

## Problem
Need to design async refactoring strategy

## Initial Context
- System uses synchronous I/O
- Performance bottleneck identified in DB queries
- Need to evaluate async/await implementation
EOF

# Коммитим контекст
mimir commit \
  --task TASK-42 \
  --branch main \
  --message "Initial architecture analysis" \
  --context-file context.txt \
  --cognitive-load 6 \
  --uncertainty 4 \
  --author "alice"
```

### Просматриваем историю

```bash
mimir history --task TASK-42 --branch main
```

### Создаем ветку для экспериментов

```bash
mimir branch create async-experiment --task TASK-42 --from main
```

### Переключаемся на ветку

```bash
mimir switch --task TASK-42 --branch async-experiment
```

### Создаем второй commit в новой ветке

```bash
cat > async_context.txt << 'EOF'
# Async Architecture

## Approach
1. Use asyncio for I/O operations
2. Refactor DB calls to use async drivers
3. Implement connection pooling

## Uncertainties
- Performance implications of context switching
- Compatibility with existing code
EOF

mimir commit \
  --message "Async approach exploration" \
  --context-file async_context.txt \
  --cognitive-load 7 \
  --uncertainty 6
```

### Просматриваем контент commit'а

```bash
# Получаем id наиболее свежего commit'а
COMMIT_ID=$(mimir history --task TASK-42 --branch async-experiment --limit 1 | grep -o '[a-f0-9]\{8\}' | head -1)

# Просматриваем контекст
mimir show $COMMIT_ID
```

### Проверяем статус

```bash
mimir status
```

## 4️⃣ Запуск тестов

```bash
pytest tests/ -v

# С coverage
pytest tests/ --cov=mimir --cov-report=html
```

## 5️⃣ CLI справка

```bash
# Помощь по всем командам
mimir --help

# Помощь по конкретной команде
mimir commit --help
mimir history --help
mimir branch --help
```

## 📊 Полезные команды

### Список всех веток

```bash
mimir branch list --task TASK-42
```

### Переход между веками

```bash
# На другую ветку
mimir switch --task TASK-42 --branch main

# Просмотр текущего состояния
mimir status
```

### Удаление ветки

```bash
mimir branch delete async-experiment --task TASK-42
```

## 🐛 Troubleshooting

### Ошибка подключения к БД

```
Error: Connection failed to postgresql+psycopg://...
```

**Решение:**
1. Проверьте, что PostgreSQL запущен: `psql -U postgres`
2. Проверьте DATABASE_URL в .env
3. Убедитесь, что БД создана: `psql -l | grep mimir_db`

### Таблицы не созданы

**Решение:**
```bash
mimir init
# или
alembic upgrade head
```

### Миграции не применены

```bash
alembic current              # Текущая версия
alembic history              # История миграций
alembic upgrade head         # Применить все
```

## 📚 Дальше

- Смотрите [README.md](README.md) для полной документации
- Смотрите примеры в [tests/test_services.py](tests/test_services.py)
- Документация по модели данных в [mimir/models.py](mimir/models.py)

## 🚀 Готово!

Теперь вы можете использовать Mimir для управления когнитивным контекстом в своих задачах!
