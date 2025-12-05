# Создание тестового тикета

## Способ 1: Через API (curl)

```bash
# Получите токен из браузера (F12 → Application → Local Storage → supabase.auth.token)
# Или используйте этот скрипт:

curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "source": "portal",
    "subject": "Не работает интернет",
    "text": "Добрый день, у меня пропал интернет сегодня утром. Проверял роутер, все индикаторы горят, но подключения нет.",
    "incoming_meta": {
      "client_email": "test@example.com"
    }
  }'
```

## Способ 2: Через Supabase SQL (прямо в базу)

```sql
-- Создать тестовый тикет напрямую в базу
INSERT INTO public.tickets (
    id,
    source,
    subject,
    description,
    status,
    priority,
    category,
    subcategory,
    language,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'portal',
    'Не работает интернет',
    'Добрый день, у меня пропал интернет сегодня утром. Проверял роутер, все индикаторы горят, но подключения нет.',
    'new',
    'high',
    'network',
    'internet_connection',
    'ru',
    NOW(),
    NOW()
);

-- Проверить созданный тикет
SELECT * FROM public.tickets ORDER BY created_at DESC LIMIT 5;
```

## Способ 3: Через Python скрипт

Создайте файл `create_test_ticket.py`:

```python
import requests
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Получить токен
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
auth_response = supabase.auth.sign_in_with_password({
    "email": "admin@test.com",
    "password": "admin123"
})
token = auth_response.session.access_token

# Создать тикет
response = requests.post(
    "http://localhost:8000/api/ingest",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "source": "portal",
        "subject": "Тестовый тикет",
        "text": "Это тестовое обращение для проверки системы",
        "incoming_meta": {}
    }
)

print("Response:", response.json())
```

Запустите:
```bash
python create_test_ticket.py
```

## Способ 4: Через браузерную консоль

Откройте консоль браузера (F12) на странице приложения и выполните:

```javascript
// Получить токен
const { data: { session } } = await supabase.auth.getSession()
const token = session.access_token

// Создать тикет
fetch('http://localhost:8000/api/ingest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    source: 'portal',
    subject: 'Тестовый тикет из браузера',
    text: 'Это тестовое обращение',
    incoming_meta: {}
  })
})
.then(r => r.json())
.then(data => {
  console.log('Тикет создан:', data)
  // Обновить страницу
  window.location.reload()
})
```

## Проверка тикетов

После создания тикета обновите страницу в браузере - тикет должен появиться в списке.

