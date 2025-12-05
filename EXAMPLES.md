# Примеры использования API

## Создание тикета

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "source": "portal",
    "subject": "Не работает интернет",
    "text": "Добрый день, у меня пропал интернет сегодня утром. Проверял роутер, все индикаторы горят, но подключения нет.",
    "incoming_meta": {
      "client_email": "client@example.com",
      "client_phone": "+77001234567"
    }
  }'
```

## Обработка тикета с ИИ

```bash
curl -X POST http://localhost:8000/api/ai/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "ticket_id": "uuid-тикета"
  }'
```

Ответ:
```json
{
  "ticket_id": "uuid",
  "language": "ru",
  "category": "network",
  "subcategory": "internet_connection",
  "department_id": "uuid-отдела",
  "priority": "high",
  "summary": "Клиент сообщает о потере интернет-соединения...",
  "auto_resolve": false,
  "suggested_response": "Проверьте подключение кабеля..."
}
```

## Получение списка тикетов

```bash
curl -X GET "http://localhost:8000/api/tickets?status=new&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Обновление тикета

```bash
curl -X PATCH http://localhost:8000/api/tickets/{ticket_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "status": "in_progress",
    "priority": "high",
    "assigned_to": "user-uuid"
  }'
```

## Поиск в базе знаний (RAG)

```bash
curl -X POST http://localhost:8000/api/ai/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "Как настроить VPN?",
    "k": 5
  }'
```

## Получение метрик (только для админов)

```bash
curl -X GET "http://localhost:8000/api/admin/metrics?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Python примеры

```python
import requests
from supabase import create_client

# Инициализация Supabase клиента
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Получение токена
auth_response = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "password"
})
token = auth_response.session.access_token

# Создание тикета
response = requests.post(
    "http://localhost:8000/api/ingest",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "source": "portal",
        "subject": "Проблема с интернетом",
        "text": "Описание проблемы..."
    }
)
```

## JavaScript/TypeScript примеры

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Вход
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Получение токена
const token = data.session.access_token

// API запрос
const response = await fetch('http://localhost:8000/api/tickets', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})

const tickets = await response.json()
```

