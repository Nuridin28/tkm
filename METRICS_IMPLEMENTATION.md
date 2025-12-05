# Реализация метрик авторешений и SLA

## ✅ Что было сделано

### 1. Создана таблица `chat_interactions`

**Миграция:** `supabase/migrations/010_add_chat_interactions_table.sql`

Таблица сохраняет все взаимодействия с ИИ ассистентом в публичном чате:
- Запрос пользователя
- Ответ ИИ
- Был ли создан тикет (`ticket_created`)
- Время ответа (`response_time_ms`)
- Метрики (confidence, similarity, etc.)

### 2. Обновлен `public_chat.py`

**Добавлено:**
- Сохранение каждого взаимодействия в `chat_interactions`
- Измерение времени ответа (`response_time_ms`)
- Сохранение `session_id` для группировки взаимодействий
- Сохранение `ticket_id` если тикет был создан

### 3. Обновлен `monitoring.py`

**Добавлено:**
- Подсчет авторешений из `chat_interactions` (когда `ticket_created = FALSE`)
- Объединение метрик из тикетов и взаимодействий
- Подсчет SLA на основе `response_time_ms` из `chat_interactions`

## Формулы метрик

### Авторешение

```
Авторешение = (Авторешения из chat_interactions + Авторешения из tickets) / (Всего взаимодействий + Всего тикетов) * 100

Где:
- Авторешения из chat_interactions = COUNT(*) WHERE ticket_created = FALSE
- Авторешения из tickets = COUNT(*) WHERE auto_resolved = TRUE
```

### SLA соответствие

```
SLA соответствие = (Количество ответов < порога) / Всего ответов * 100

Где:
- Порог по умолчанию = 5000ms (5 секунд)
- Время ответа берется из response_time_ms в chat_interactions
```

## Как это работает

### Сценарий 1: Авторешение (тикет НЕ создан)

1. Пользователь задает вопрос: "Какие тарифы на интернет?"
2. ИИ находит информацию в базе знаний (similarity > 0.2)
3. ИИ отвечает пользователю
4. Тикет НЕ создается (`ticket_created = FALSE`)
5. **Сохраняется в `chat_interactions` с `ticket_created = FALSE`** ✅
6. Это считается **авторешением**

### Сценарий 2: Создание тикета

1. Пользователь задает вопрос: "Роутер не работает"
2. ИИ определяет техническую проблему
3. ИИ отвечает и создает тикет
4. Тикет создается (`ticket_created = TRUE`)
5. **Сохраняется в `chat_interactions` с `ticket_created = TRUE` и `ticket_id`** ✅
6. Это НЕ авторешение

## Проверка работы

### 1. Применить миграцию

```sql
-- Выполните в Supabase SQL Editor
-- Файл: supabase/migrations/010_add_chat_interactions_table.sql
```

### 2. Проверить сохранение взаимодействий

После отправки сообщения в чат проверьте:

```sql
SELECT 
    ticket_created,
    response_time_ms,
    confidence,
    max_similarity,
    created_at
FROM chat_interactions
ORDER BY created_at DESC
LIMIT 10;
```

### 3. Проверить метрики

```bash
# Запрос к API
GET /api/admin/monitoring/metrics?from_date=2024-01-01&to_date=2024-12-31
```

Должны вернуться:
- `auto_resolve_stats.total_auto_resolved` - общее количество авторешений
- `auto_resolve_stats.total_tickets` - общее количество запросов (взаимодействия + тикеты)
- `auto_resolve_stats.auto_resolve_rate` - процент авторешений
- `response_time_stats.avg_response_time_seconds` - среднее время ответа

## Примеры SQL запросов

### Авторешения за последние 7 дней

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) FILTER (WHERE ticket_created = FALSE) as auto_resolved,
    COUNT(*) as total,
    ROUND(COUNT(*) FILTER (WHERE ticket_created = FALSE)::FLOAT / COUNT(*) * 100, 2) as auto_resolve_rate
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Среднее время ответа по дням

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as interactions,
    ROUND(AVG(response_time_ms) / 1000.0, 2) as avg_response_time_seconds,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) / 1000.0, 2) as median_response_time_seconds
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '7 days'
AND response_time_ms IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Авторешения по категориям

```sql
SELECT 
    COALESCE(category, 'no_category') as category,
    COUNT(*) FILTER (WHERE ticket_created = FALSE) as auto_resolved,
    COUNT(*) as total,
    ROUND(COUNT(*) FILTER (WHERE ticket_created = FALSE)::FLOAT / COUNT(*) * 100, 2) as auto_resolve_rate
FROM chat_interactions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY category
ORDER BY auto_resolved DESC;
```

## Важные замечания

1. **Авторешение = `ticket_created = FALSE`**
   - Это означает, что ИИ ответил без создания тикета
   - Пользователь получил ответ и ушел довольным

2. **SLA = время ответа ИИ**
   - Измеряется от получения запроса до отправки ответа
   - Сохраняется в миллисекундах (`response_time_ms`)
   - Для отображения конвертируется в секунды

3. **Объединение метрик**
   - Авторешения из `chat_interactions` (публичный чат)
   - Авторешения из `tickets` (другие источники)
   - Общая метрика = сумма обоих

4. **Session ID**
   - Используется для группировки взаимодействий одного пользователя
   - Можно передавать из frontend или генерировать автоматически

## Следующие шаги

1. ✅ Применить миграцию `010_add_chat_interactions_table.sql`
2. ✅ Перезапустить backend
3. ✅ Протестировать сохранение взаимодействий
4. ✅ Проверить метрики в API `/api/admin/monitoring/metrics`

