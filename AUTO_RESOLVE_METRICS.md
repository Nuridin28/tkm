# Метрики авторешений и SLA

## Определения

### Авторешение (Auto-Resolve)
**Авторешение** = когда ИИ ассистент ответил на вопрос пользователя **БЕЗ создания тикета**.

Это означает, что:
- Пользователь задал вопрос
- ИИ нашел информацию в базе знаний (RAG)
- ИИ дал ответ пользователю
- Тикет НЕ был создан (`ticket_created = FALSE`)

**Формула:**
```
Авторешение (%) = (Количество взаимодействий с ticket_created = FALSE / Всего взаимодействий) * 100
```

### SLA соответствие
**SLA соответствие** = время ответа ИИ ассистента находится в допустимых пределах.

**Метрики:**
- Среднее время ответа (мс)
- Процент ответов в пределах SLA (например, < 5 секунд)
- Медианное время ответа

## Структура данных

### Таблица `chat_interactions`

Каждое взаимодействие с ИИ ассистентом сохраняется в таблице `chat_interactions`:

```sql
{
    id: UUID,
    user_id: TEXT,                    -- ID пользователя
    client_type: 'corporate' | 'private',
    message: TEXT,                     -- Запрос пользователя
    ai_response: TEXT,                 -- Ответ ИИ
    conversation_history: JSONB,      -- История до этого сообщения
    ticket_created: BOOLEAN,           -- FALSE = авторешение, TRUE = создан тикет
    ticket_id: UUID,                   -- ID тикета (если создан)
    confidence: FLOAT,                 -- Уверенность ИИ (0.0-1.0)
    max_similarity: FLOAT,              -- Релевантность найденной информации
    is_technical_issue: BOOLEAN,
    ai_explicitly_requested_ticket: BOOLEAN,
    category: TEXT,                    -- Если тикет создан
    subcategory: TEXT,
    department: TEXT,
    priority: TEXT,
    language: TEXT,
    response_time_ms: INTEGER,         -- Время ответа для SLA
    sources: JSONB,                    -- Источники из RAG
    session_id: TEXT,                  -- ID сессии
    created_at: TIMESTAMPTZ
}
```

## Подсчет метрик

### 1. Авторешения из chat_interactions

```python
# Все взаимодействия
total_interactions = COUNT(*) FROM chat_interactions WHERE created_at BETWEEN from_date AND to_date

# Авторешения (без создания тикета)
auto_resolved = COUNT(*) FROM chat_interactions 
WHERE ticket_created = FALSE 
AND created_at BETWEEN from_date AND to_date

# Процент авторешений
auto_resolve_rate = (auto_resolved / total_interactions) * 100
```

### 2. Авторешения из tickets (старая логика)

```python
# Тикеты, которые были автоматически решены
auto_resolved_tickets = COUNT(*) FROM tickets 
WHERE auto_resolved = TRUE 
AND created_at BETWEEN from_date AND to_date
```

### 3. Общая метрика авторешений

**Общее авторешение** = Авторешения из chat_interactions + Авторешения из tickets

```python
total_auto_resolved = auto_resolved_interactions + auto_resolved_tickets
total_requests = total_interactions + total_tickets
overall_auto_resolve_rate = (total_auto_resolved / total_requests) * 100
```

### 4. SLA соответствие

```python
# Среднее время ответа
avg_response_time = AVG(response_time_ms) FROM chat_interactions 
WHERE created_at BETWEEN from_date AND to_date

# Процент ответов в пределах SLA (например, < 5000ms)
sla_threshold_ms = 5000  # 5 секунд
sla_compliant = COUNT(*) FROM chat_interactions 
WHERE response_time_ms < sla_threshold_ms 
AND created_at BETWEEN from_date AND to_date

sla_compliance_rate = (sla_compliant / total_interactions) * 100
```

## Примеры запросов

### Авторешения по категориям

```sql
SELECT 
    category,
    COUNT(*) FILTER (WHERE ticket_created = FALSE) as auto_resolved,
    COUNT(*) as total,
    (COUNT(*) FILTER (WHERE ticket_created = FALSE)::FLOAT / COUNT(*) * 100) as auto_resolve_rate
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '30 days'
AND category IS NOT NULL
GROUP BY category;
```

### SLA соответствие по времени

```sql
SELECT 
    CASE 
        WHEN response_time_ms < 1000 THEN '< 1s'
        WHEN response_time_ms < 3000 THEN '1-3s'
        WHEN response_time_ms < 5000 THEN '3-5s'
        ELSE '> 5s'
    END as response_time_bucket,
    COUNT(*) as count,
    AVG(response_time_ms) as avg_time
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY response_time_bucket
ORDER BY response_time_bucket;
```

### Авторешения по уверенности

```sql
SELECT 
    CASE 
        WHEN confidence >= 0.8 THEN 'High (>=0.8)'
        WHEN confidence >= 0.6 THEN 'Medium (0.6-0.8)'
        WHEN confidence >= 0.4 THEN 'Low (0.4-0.6)'
        ELSE 'Very Low (<0.4)'
    END as confidence_bucket,
    COUNT(*) FILTER (WHERE ticket_created = FALSE) as auto_resolved,
    COUNT(*) as total,
    AVG(confidence) as avg_confidence
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY confidence_bucket
ORDER BY confidence_bucket;
```

## Интеграция в API

### Обновление `/api/admin/monitoring/metrics`

Нужно добавить подсчет метрик из `chat_interactions`:

```python
# 1. Авторешения из chat_interactions
interactions_result = supabase.table("chat_interactions")\
    .select("*")\
    .gte("created_at", from_date)\
    .lte("created_at", to_date)\
    .execute()

interactions = interactions_result.data or []
total_interactions = len(interactions)
auto_resolved_interactions = len([i for i in interactions if not i.get("ticket_created")])

# 2. Объединить с метриками из tickets
total_auto_resolved = auto_resolved_interactions + auto_resolved_tickets
total_requests = total_interactions + total_tickets
overall_auto_resolve_rate = (total_auto_resolved / total_requests * 100) if total_requests > 0 else 0.0

# 3. SLA метрики
response_times = [i.get("response_time_ms", 0) for i in interactions if i.get("response_time_ms")]
avg_response_time_ms = sum(response_times) / len(response_times) if response_times else 0
avg_response_time_seconds = avg_response_time_ms / 1000

sla_threshold_ms = 5000  # 5 секунд
sla_compliant = len([i for i in interactions if i.get("response_time_ms", 0) < sla_threshold_ms])
sla_compliance_rate = (sla_compliant / total_interactions * 100) if total_interactions > 0 else 0.0
```

## Рекомендации

1. **Использовать обе метрики:**
   - Авторешения из `chat_interactions` - для публичного чата
   - Авторешения из `tickets` - для других источников (email, phone, etc.)

2. **SLA пороги:**
   - Быстрый ответ: < 1 секунда
   - Нормальный ответ: 1-3 секунды
   - Медленный ответ: 3-5 секунд
   - Нарушение SLA: > 5 секунд

3. **Мониторинг:**
   - Отслеживать тренды авторешений по времени
   - Анализировать категории с низким процентом авторешений
   - Мониторить время ответа и оптимизировать медленные запросы

