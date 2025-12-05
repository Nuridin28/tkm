# Обновление подсчета метрик с учетом chat_interactions

## ✅ Что было сделано

### 1. Обновлен `/api/admin/metrics` (`admin.py`)

**Добавлено:**
- ✅ Подсчет авторешений из `chat_interactions` (где `ticket_created = FALSE`)
- ✅ Объединение метрик из тикетов и взаимодействий
- ✅ Подсчет SLA на основе авторешений из `chat_interactions`
- ✅ Среднее время ответа из `chat_interactions`

**Формулы:**
```python
# Авторешения
total_auto_resolved = auto_resolved_tickets + auto_resolved_interactions
total_requests = len(tickets) + len(interactions)
auto_resolve_rate = (total_auto_resolved / total_requests) * 100

# SLA
sla_compliant = resolved_tickets + auto_resolved_interactions
sla_compliance = (sla_compliant / total_requests) * 100
```

### 2. Обновлен `/api/admin/monitoring/metrics` (`monitoring.py`)

**Уже было реализовано:**
- ✅ Подсчет авторешений из `chat_interactions`
- ✅ Объединение метрик
- ✅ Подсчет времени ответа из `chat_interactions`

**Улучшено:**
- ✅ Определение категории для авторешений из `chat_interactions` (если категория не указана)
- ✅ Оптимизация подсчета времени ответа по источникам
- ✅ Добавлено логирование для отладки

### 3. Определение категорий для авторешений

Если в `chat_interactions` категория не указана (потому что тикет не создавался), категория определяется автоматически по содержимому сообщения:

- **billing** - тариф, цена, стоимость, оплат, биллинг
- **network** - интернет, сеть, подключ, скорост
- **telephony** - телефон, звонок
- **tv** - тв, телевизор, канал
- **equipment** - роутер, модем, оборудован
- **other** - остальное

## Структура данных

### Авторешения из chat_interactions

```sql
SELECT 
    COUNT(*) as total_auto_resolved,
    AVG(confidence) as avg_confidence,
    AVG(max_similarity) as avg_similarity,
    AVG(response_time_ms) / 1000.0 as avg_response_time_seconds
FROM chat_interactions
WHERE ticket_created = FALSE  -- Авторешение
AND created_at >= '2024-01-01'
AND created_at <= '2024-12-31';
```

### Общая статистика

```sql
-- Авторешения из обоих источников
WITH ticket_auto_resolved AS (
    SELECT COUNT(*) as count FROM tickets 
    WHERE auto_resolved = TRUE 
    AND created_at BETWEEN '2024-01-01' AND '2024-12-31'
),
interaction_auto_resolved AS (
    SELECT COUNT(*) as count FROM chat_interactions 
    WHERE ticket_created = FALSE 
    AND created_at BETWEEN '2024-01-01' AND '2024-12-31'
)
SELECT 
    (SELECT count FROM ticket_auto_resolved) as from_tickets,
    (SELECT count FROM interaction_auto_resolved) as from_interactions,
    (SELECT count FROM ticket_auto_resolved) + (SELECT count FROM interaction_auto_resolved) as total_auto_resolved;
```

## API Endpoints

### 1. `/api/admin/metrics`

**Обновлено:**
- `total_tickets` - теперь общее количество запросов (тикеты + взаимодействия)
- `auto_resolve_rate` - учитывает авторешения из обоих источников
- `sla_compliance` - учитывает авторешения из `chat_interactions`
- `avg_response_time` - среднее время ответа из `chat_interactions`

**Пример ответа:**
```json
{
  "total_tickets": 250,  // 100 тикетов + 150 взаимодействий
  "auto_resolve_rate": 72.0,  // (50 авторешенных тикетов + 130 авторешений из чата) / 250
  "sla_compliance": 85.0,
  "avg_response_time": 2.3,  // секунды
  "period_from": "2024-01-01T00:00:00Z",
  "period_to": "2024-12-31T23:59:59Z"
}
```

### 2. `/api/admin/monitoring/metrics`

**Уже обновлено:**
- `auto_resolve_stats` - учитывает оба источника
- `response_time_stats` - учитывает время ответа из `chat_interactions`
- `by_source` - включает источник "chat" для взаимодействий

## Проверка работы

### 1. Проверить сохранение взаимодействий

```sql
SELECT 
    ticket_created,
    COUNT(*) as count,
    AVG(response_time_ms) / 1000.0 as avg_response_time_seconds
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY ticket_created;
```

**Ожидаемый результат:**
- `ticket_created = FALSE` - авторешения
- `ticket_created = TRUE` - созданные тикеты

### 2. Проверить метрики через API

```bash
# Общие метрики
curl http://localhost:8000/api/admin/metrics?from_date=2024-01-01&to_date=2024-12-31 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Детальные метрики мониторинга
curl http://localhost:8000/api/admin/monitoring/metrics?from_date=2024-01-01&to_date=2024-12-31 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Проверить логи

В логах backend должны быть сообщения:
```
[METRICS] Auto-resolve stats:
  - Tickets: 100 total, 50 auto-resolved
  - Interactions: 150 total, 130 auto-resolved
  - Overall: 250 total, 180 auto-resolved (72.00%)
```

## Формулы метрик

### Авторешение

```
Авторешение (%) = (Авторешения из tickets + Авторешения из chat_interactions) / (Всего тикетов + Всего взаимодействий) * 100

Где:
- Авторешения из tickets = COUNT(*) WHERE auto_resolved = TRUE
- Авторешения из chat_interactions = COUNT(*) WHERE ticket_created = FALSE
```

### SLA соответствие

```
SLA соответствие (%) = (Resolved tickets + Авторешения из chat_interactions) / (Всего запросов) * 100

Где:
- Resolved tickets = тикеты со статусом resolved/auto_resolved/closed
- Авторешения из chat_interactions = взаимодействия с ticket_created = FALSE
```

### Среднее время ответа

```
Среднее время ответа = AVG(response_time_ms) / 1000.0 (секунды)

Где:
- response_time_ms берется из chat_interactions
```

## Важные замечания

1. **Два типа авторешений:**
   - Авторешения из `chat_interactions` - ИИ ответил без создания тикета
   - Авторешенные тикеты - тикет был создан, но автоматически решен

2. **Объединение метрик:**
   - Все метрики теперь учитывают оба источника
   - `total_tickets` в ответе = общее количество запросов (не только тикеты)

3. **Категории:**
   - Для авторешений из `chat_interactions` категория определяется автоматически, если не указана
   - Это позволяет группировать авторешения по категориям

4. **Время ответа:**
   - Измеряется только для `chat_interactions` (публичный чат)
   - Для тикетов используется таблица `response_times`

## Готово! ✅

Теперь все метрики правильно учитывают данные из `chat_interactions`:
- ✅ Авторешения считаются из обоих источников
- ✅ SLA учитывает авторешения из чата
- ✅ Время ответа берется из `chat_interactions`
- ✅ Категории определяются автоматически

