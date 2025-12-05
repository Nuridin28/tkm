# Быстрое создание тикета

## Способ 1: Через SQL (САМЫЙ ПРОСТОЙ) ⚡

Выполните в Supabase SQL Editor:

```sql
-- Создать тестовый тикет
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
    summary,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'portal',
    'Не работает интернет',
    'Добрый день, у меня пропал интернет сегодня утром. Проверял роутер, все индикаторы горят, но подключения нет. Помогите, пожалуйста.',
    'new',
    'high',
    'network',
    'internet_connection',
    'ru',
    'Клиент сообщает о потере интернет-соединения. Роутер работает, но подключения нет.',
    NOW(),
    NOW()
);

-- Проверить созданный тикет
SELECT * FROM public.tickets ORDER BY created_at DESC LIMIT 5;
```

После выполнения обновите страницу в браузере - тикет появится!

## Способ 2: Через браузерную консоль (БЕЗ SQL) 🌐

1. Откройте консоль браузера (F12)
2. Убедитесь, что вы вошли в систему
3. Выполните этот код:

```javascript
// Получить токен
const { data: { session } } = await supabase.auth.getSession()
const token = session.access_token

// Создать тикет
const response = await fetch('http://localhost:8000/api/ingest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    source: 'portal',
    subject: 'Не работает интернет',
    text: 'Добрый день, у меня пропал интернет сегодня утром. Проверял роутер, все индикаторы горят, но подключения нет.',
    incoming_meta: {}
  })
})

const data = await response.json()
console.log('✅ Тикет создан:', data)

// Обновить страницу
window.location.reload()
```

## Способ 3: Через curl (терминал) 💻

```bash
# Сначала получите токен (замените email и password)
TOKEN=$(curl -s -X POST 'https://ваш-проект.supabase.co/auth/v1/token?grant_type=password' \
  -H "apikey: ваш-anon-key" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}' | jq -r '.access_token')

# Создать тикет
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "source": "portal",
    "subject": "Не работает интернет",
    "text": "Добрый день, у меня пропал интернет сегодня утром.",
    "incoming_meta": {}
  }'
```

## Способ 4: Создать несколько тикетов сразу (SQL)

```sql
-- Создать несколько тестовых тикетов
INSERT INTO public.tickets (
    id, source, subject, description, status, priority, 
    category, subcategory, language, created_at, updated_at
) VALUES 
(
    gen_random_uuid(),
    'portal',
    'Не работает интернет',
    'Добрый день, у меня пропал интернет сегодня утром.',
    'new',
    'high',
    'network',
    'internet_connection',
    'ru',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    'email',
    'Проблема с оплатой',
    'Не могу оплатить услуги через личный кабинет.',
    'new',
    'medium',
    'billing',
    'payment_issue',
    'ru',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    'chat',
    'Настройка VPN',
    'Помогите настроить VPN подключение.',
    'new',
    'low',
    'network',
    'vpn_access',
    'ru',
    NOW(),
    NOW()
);

-- Проверить все тикеты
SELECT id, subject, status, priority, category, created_at 
FROM public.tickets 
ORDER BY created_at DESC;
```

## Рекомендация

**Используйте Способ 1 (SQL)** - это самый быстрый и простой способ для тестирования.

После создания тикета:
1. Обновите страницу в браузере (F5)
2. Тикет появится в списке
3. Можно кликнуть на него для просмотра деталей

