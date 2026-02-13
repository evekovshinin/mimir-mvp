# Примеры использования Mimir

## 📚 Сценарии использования

### Сценарий 1: Исследование архитектуры с несколькими гипотезами

Вы работаете над рефакторингом системы и хотите изучить несколько подходов.

#### Этап 1: Создание задачи и начального контекста

```bash
# Создаем задачу
$ mimir create-task "ARCH-001-REFACTOR"

# Переключаемся на эту задачу
$ mimir switch --task ARCH-001-REFACTOR

# Создаем файл с начальным контекстом
$ cat > requirements.txt << 'EOF'
# Refactoring Requirements

## Current State
- Monolithic service with ~50K lines
- Synchronous I/O operations
- Response time: 2-5 seconds
- Database queries not optimized

## Goals
1. Reduce response time to < 500ms
2. Implement async/await
3. Add caching layer
4. Optimize database queries

## Constraints
- Must maintain backward compatibility
- Cannot break existing API
- Have 2 weeks for refactoring
EOF

# Коммитим начальный контекст
$ mimir commit \
  --message "Initial state: monolithic service analysis" \
  --context-file requirements.txt \
  --cognitive-load 4 \
  --uncertainty 6 \
  --author "alice"

# ✓ Created commit: Initial state: monolithic service analysis
# ✓ ID: a1b2c3d4...
# ✓ Branch: main
```

#### Этап 2: Создание веток для исследования разных подходов

```bash
# Подход 1: Полный рефакторинг на asyncio
$ mimir branch create approach-asyncio --task ARCH-001-REFACTOR --from main
$ mimir switch --branch approach-asyncio

$ cat > asyncio_analysis.txt << 'EOF'
# Asyncio Approach Analysis

## Advantages
✓ Native Python async/await
✓ Built-in event loop
✓ Good for I/O-bound operations
✓ Mature ecosystem

## Challenges
✗ Need to refactor all database calls
✗ Thread safety considerations
✗ Debugging becomes harder
✗ Requires dependency updates

## Estimated Effort: 2 weeks
## Risk Level: Medium-High

## Next Steps:
1. Create async database wrapper
2. Refactor services one by one
3. Add comprehensive tests
4. Load testing and benchmarking
EOF

$ mimir commit \
  --message "Asyncio approach: deep analysis" \
  --context-file asyncio_analysis.txt \
  --cognitive-load 7 \
  --uncertainty 4 \
  --author "alice"
  
# Continue with more detailed analysis...
$ cat > asyncio_detailed.txt << 'EOF'
# Asyncio Detailed Plan

## Phase 1: Infrastructure (Days 1-2)
- Create async database connection pool
- Setup asyncio context and event loop
- Add async logging

## Phase 2: Service Refactoring (Days 3-8)
- User service: convert DB calls to async
- Order service: convert DB calls to async
- Payment service: convert DB calls to async

## Phase 3: Integration (Days 9-10)
- Update HTTP handlers to be async
- Test all endpoints
- Load testing

## Phase 4: Deployment (Days 11-14)
- Staging deployment
- Production gradual rollout
- Monitoring and rollback plan

## Updated Uncertainty: 3 (concrete plan now)
EOF

$ mimir commit \
  --message "Detailed asyncio implementation plan" \
  --context-file asyncio_detailed.txt \
  --cognitive-load 6 \
  --uncertainty 3 \
  --author "bob"
```

```bash
# Подход 2: Минимальные изменения с FastAPI (ASGI)
$ mimir switch --task ARCH-001-REFACTOR --branch main  # Back to main
$ mimir branch create approach-fastapi --task ARCH-001-REFACTOR --from main
$ mimir switch --branch approach-fastapi

$ cat > fastapi_analysis.txt << 'EOF'
# FastAPI/ASGI Approach Analysis

## Advantages
✓ Zero changes to business logic
✓ Just replace Flask with FastAPI
✓ ASGI automatically handles concurrency
✓ Minimal refactoring required

## Challenges
✗ Database is still synchronous
✗ Max benefit limited by blocking DB calls
✗ Still need connection pooling

## Estimated Effort: 3 days
## Risk Level: Low

## Performance Estimate
- Current: ~4 seconds per request
- After: ~3.5 seconds (only marginal improvement)
- But: Can handle more concurrent requests

## Verdict: Insufficient for goals
This is just a band-aid solution.
EOF

$ mimir commit \
  --message "FastAPI approach: dismissed due to insufficient gains" \
  --context-file fastapi_analysis.txt \
  --cognitive-load 5 \
  --uncertainty 7 \
  --author "alice"
```

#### Этап 3: Сравнение подходов

```bash
# Просмотр истории asyncio подхода
$ mimir history --task ARCH-001-REFACTOR --branch approach-asyncio --limit 10

# Commit ID         Message                                Author  Created         Load/Unc
# ──────────────────────────────────────────────────────────────────────────────
# 8f9e7d6c  Detailed asyncio implementation plan      bob     2026-02-13...  6/3
# a1b2c3d4  Asyncio approach: deep analysis           alice   2026-02-13...  7/4
# 5e6f7g8h  Initial state: monolithic service analysis alice   2026-02-13...  4/6

# Просмотр истории FastAPI подхода
$ mimir history --task ARCH-001-REFACTOR --branch approach-fastapi

# Commit ID         Message                                Author  Created         Load/Unc
# ──────────────────────────────────────────────────────────────────────────────
# 9c8d7e6f  FastAPI approach: dismissed due to...     alice   2026-02-13...  5/7
# 5e6f7g8h  Initial state: monolithic service analysis alice   2026-02-13...  4/6

# Просмотр полного контекста asyncio решения
$ mimir show 8f9e7d6c
# Commit: 8f9e7d6c...
# Message: Detailed asyncio implementation plan
# Author: bob
# Created: 2026-02-13T10:30:00
# Cognitive Load: 6
# Uncertainty: 3
#
# Context:
# # Asyncio Detailed Plan
# ...
```

#### Этап 4: Выбор и merge

```bash
# Решено: идем с asyncio подходом
# Переходим в main и создаем финальный контекст
$ mimir switch --task ARCH-001-REFACTOR --branch main

$ cat > decision.txt << 'EOF'
# Decision: Asyncio Approach Selected

## Rationale
- Only approach that meets performance goals
- Risk is manageable with proper planning
- Team has experience with async patterns
- 2-week timeline is realistic

## Approved Plan
- See approach-asyncio branch for detailed analysis
- Phase 1-4 implementation plan confirmed
- Start with database layer refactoring
- Daily standups for risk mitigation

## Next Immediate Action
Create implementation backlog and start Phase 1
EOF

$ mimir commit \
  --message "Decision: Asyncio approach approved for implementation" \
  --context-file decision.txt \
  --cognitive-load 3 \
  --uncertainty 2 \
  --author "lead"
```

---

### Сценарий 2: Отладка сложной проблемы

При отладке трудной проблемы нужно отслеживать гипотезы и их проверку.

```bash
# Создаем задачу для баг репорта
$ mimir create-task "BUG-2891-RACE-CONDITION"

# Начальный анализ
$ cat > initial.txt << 'EOF'
# BUG-2891: Race Condition in Order Processing

## Observed Behavior
- Order payment confirmed
- But inventory not updated
- Happens in ~0.5% of orders
- More frequent under load

## Initial Hypotheses
1. Database isolation level issue
2. Race condition in order completion handler
3. Async timing issue
4. Cache invalidation problem

## Environment
- PostgreSQL 14
- Python 3.11 + asyncio
- Redis cache
EOF

$ mimir commit \
  --message "Bug analysis: race condition in order processing" \
  --context-file initial.txt \
  --cognitive-load 7 \
  --uncertainty 8 \
  --author "developer"

# Создаем ветки для разных гипотез
$ mimir branch create hyp-isolation-level
$ mimir branch create hyp-race-condition
$ mimir branch create hyp-async-timing

# Исследуем первую гипотезу
$ mimir switch --branch hyp-isolation-level

$ cat > isolation_investigation.txt << 'EOF'
# Hypothesis 1: Database Isolation Level

## Investigation
Checked current isolation level: READ_COMMITTED
PostgreSQL documentation suggests:
- Recommended for most workloads
- Could have dirty reads in edge cases

## Testing
- Ran transactions with isolation level logs
- Added query logging to see execution order
- Results: No isolation violations detected

## Conclusion
✗ Likely NOT the root cause
- Isolation level is appropriate
- No transaction conflicts observed
- Moving to next hypothesis

## Effort: 2 hours
## Outcome: Dead end
EOF

$ mimir commit \
  --message "Investigated: isolation level NOT the cause" \
  --context-file isolation_investigation.txt \
  --cognitive-load 5 \
  --uncertainty 6

# Исследуем вторую гипотезу
$ mimir switch --task BUG-2891-RACE-CONDITION --branch hyp-race-condition

$ cat > race_condition_investigation.txt << 'EOF'
# Hypothesis 2: Race Condition in Order Completion

## Code Review
Looked at order completion handler:

```python
async def complete_order(order_id):
    order = await db.get_order(order_id)
    
    # Race window here! #########
    await payment_service.confirm(order.payment_id)
    await inventory.reserve(order.items)
    # Could fail between these two
    
    order.status = 'completed'
    await db.save(order)
```

## Root Cause Found!
Between payment confirmation and inventory reservation:
1. Payment confirmation succeeds
2. Inventory reservation fails (out of stock)
3. Order status updated to 'completed' anyway
4. Payment charged but inventory not reserved

## Solution
Use database transaction to ensure atomicity:
- Wrap both operations in single transaction
- Rollback both if either fails
EOF

$ mimir commit \
  --message "FOUND ROOT CAUSE: atomicity violation in order completion" \
  --context-file race_condition_investigation.txt \
  --cognitive-load 9 \
  --uncertainty 1

# Создаем fix branch
$ mimir branch create fix-atomic-transaction

$ cat > fix_implementation.txt << 'EOF'
# Fix Implementation: Atomic Order Completion

## Solution Code

async def complete_order_atomic(order_id):
    async with db.transaction():  # Atomic transaction
        order = await db.get_order(order_id)
        
        payment = await payment_service.confirm(order.payment_id)
        if not payment.success:
            raise PaymentException("Payment failed")
        
        inventory = await inventory.reserve(order.items)
        if not inventory.success:
            raise InventoryException("Inventory unavailable")
        
        order.status = 'completed'
        await db.save(order)

## Testing
- Unit tests for both success paths
- Unit tests for both failure scenarios
- Integration test with load simulation
- Verified: Race condition eliminated

## Deploy
- Merged to main
- Deployed to staging
- Deployed to production
- Monitored for 24 hours
✓ Bug fixed!
EOF

$ mimir switch --task BUG-2891-RACE-CONDITION --branch main
$ mimir commit \
  --message "FIXED: Atomic transaction ensures order consistency" \
  --context-file fix_implementation.txt \
  --cognitive-load 4 \
  --uncertainty 1
```

---

### Сценарий 3: Design Decision with Team

Командное обсуждение архитектурного решения.

```bash
# Задача: выбрать подход к кэшированию
$ mimir create-task "INFRA-005-CACHING-STRATEGY"

# Alice начинает исследование
$ mimir commit \
  --message "Caching strategy exploration" \
  --context "Current: No caching. Goal: Reduce DB load by 50%." \
  --author "alice" \
  --cognitive-load 4 \
  --uncertainty 8

# Bob предлагает Redis подход
$ mimir branch create approach-redis --from main
$ mimir switch --branch approach-redis

$ cat > redis_approach.txt << 'EOF'
# Redis Caching Approach (by Bob)

## Benefits
- Distributed cache
- Automatic TTL
- Supports complex data structures
- Great ecosystem

## Risks
- Extra infrastructure
- Network latency
- Cache invalidation complexity
- Cost: Redis cluster maintenance

## Estimate: 1 week
EOF

$ mimir commit \
  --message "Redis approach: pros and cons" \
  --context-file redis_approach.txt \
  --author "bob" \
  --cognitive-load 5 \
  --uncertainty 6

# Charlie предлагает локальное кэширование
$ mimir switch --task INFRA-005-CACHING-STRATEGY --branch main
$ mimir branch create approach-local-cache

$ cat > local_cache.txt << 'EOF'
# Local In-Memory Caching (by Charlie)

## Benefits
- Zero network latency
- Simple implementation
- No extra infrastructure
- Low operating costs

## Risks
- Cache not shared across instances
- Memory usage per instance
- Invalidation only local
- Won't work well with load balancer

## Better for: Single instance or small team
## Estimate: 2 days
EOF

$ mimir commit \
  --message "Local cache approach: lightweight alternative" \
  --context-file local_cache.txt \
  --author "charlie" \
  --cognitive-load 3 \
  --uncertainty 5

# Дэйв предлагает гибридный подход
$ mimir switch --task INFRA-005-CACHING-STRATEGY --branch main
$ mimir branch create approach-hybrid

$ cat > hybrid_approach.txt << 'EOF'
# Hybrid Approach: Local + Distributed (by Dave)

## Architecture
1. Local L1 cache (in-memory, process-local)
   - Very fast reads
   - For frequently accessed items

2. Distributed L2 cache (Redis)
   - Shared across instances
   - Longer TTL
   - Cache miss in L1 → hit in L2

## Benefits
- Best of both worlds
- Handle both local and cross-instance access
- Graceful degradation if Redis down

## Complexity
- Double cache logic
- Invalidation strategy needed
- More moving parts

## Estimate: 2 weeks
## Risk: Medium

## Recommendation: USE THIS APPROACH
Most balanced solution for our scale.
EOF

$ mimir commit \
  --message "RECOMMENDED: Hybrid L1/L2 caching strategy" \
  --context-file hybrid_approach.txt \
  --author "dave" \
  --cognitive-load 6 \
  --uncertainty 2

# Lead делает final decision
$ mimir switch --task INFRA-005-CACHING-STRATEGY --branch main

$ cat > decision.txt << 'EOF'
# Final Decision: Hybrid Caching Strategy

## Meeting Notes (2026-02-13)
- Reviewed all three approaches
- Dave's hybrid approach wins:
  - Meets performance goals
  - Reasonable complexity
  - Scalable for future growth

## Implementation Plan
1. Start with L1 local cache
2. Add L2 Redis in next phase
3. Define invalidation strategies
4. Load testing before prod

## Timeline: 4 weeks
## Owner: Dave
## Reviewers: Alice, Bob, Charlie
EOF

$ mimir commit \
  --message "DECISION: Hybrid L1/L2 caching approved" \
  --context-file decision.txt \
  --author "lead-eng"
```

---

## 🧠 Best Practices

### 1️⃣ Commit Messages

```bash
# ✓ Good: Clear, specific, actionable
mimir commit \
  --message "DB query optimization: indexed user_id lookup" \
  --context "..."

# ✗ Bad: Vague
mimir commit --message "Updates" --context "..."
```

### 2️⃣ Context Content

```bash
# ✓ Good: Structured, with decisions and rationale
cat > context.txt << 'EOF'
# Feature: User Authentication

## Current State
- Using session-based auth
- No rate limiting
- Auth failures not logged

## Decision: JWT + Rate Limiting

### Why JWT?
- Stateless
- Scalable
- Industry standard

### Why Rate Limiting?
- Prevent brute force
- Reduce bot attacks
- Protect resources

### Implementation
[Details...]

## Risks
- JWT secret rotation needed
- Client-side token storage
- Clock sync issues

## Mitigations
[...]
EOF

# ✗ Bad: Too vague
mimir commit --message "Auth stuff" --context "Added JWT"
```

### 3️⃣ Metrics Usage

```bash
# Use cognitive_load to track complexity
# Use uncertainty to track confidence

# During exploration (high uncertainty)
mimir commit --cognitive-load 7 --uncertainty 8 --message "..."

# After decision (low uncertainty)
mimir commit --cognitive-load 5 --uncertainty 2 --message "..."

# Dead-end investigation (mark as done)
mimir commit --cognitive-load 4 --uncertainty 1 --message "Investigated: ruled out"
```

### 4️⃣ Branch Naming Conventions

```bash
# Feature exploration
mimir branch create approach-feature-name

# Bug investigation
mimir branch create hyp-root-cause-name

# Performance optimization
mimir branch create optimize-component-name

# Refactoring
mimir branch create refactor-area-name

# Experimental
mimir branch create exp-crazy-idea-name
```

---

Готово к использованию! 🚀
