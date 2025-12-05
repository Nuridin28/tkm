# CURL запросы для AI Help Desk

## 1. Логин через Supabase Auth

```bash
curl -X POST 'https://khfqutqadmnrpsyackez.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtoZnF1dHFhZG1ucnBzeWFja2V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5MjYwMTIsImV4cCI6MjA4MDUwMjAxMn0.C00mtsFKftvB_JWoyvETKx6NNGmU-dTA3EwG5gILk8I' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@test.com",
    "password": "admin123"
  }'
```

**Сохранить токен автоматически:**
```bash
TOKEN=$(curl -s -X POST 'https://khfqutqadmnrpsyackez.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtoZnF1dHFhZG1ucnBzeWFja2V6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5MjYwMTIsImV4cCI6MjA4MDUwMjAxMn0.C00mtsFKftvB_JWoyvETKx6NNGmU-dTA3EwG5gILk8I' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@test.com","password":"admin123"}' | jq -r '.access_token')

echo "Token: $TOKEN"
```

**Пример с реальными значениями:**
```bash
curl -X POST 'https://abcdefghijklmnop.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@test.com",
    "password": "admin123"
  }'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "xxx",
  "user": {
    "id": "a56ae3d5-b79d-4c9c-b295-7a2abb4f991d",
    "email": "admin@test.com"
  }
}
```

**Сохраните `access_token` в переменную:**
```bash
TOKEN=$(curl -s -X POST 'https://YOUR_PROJECT_ID.supabase.co/auth/v1/token?grant_type=password' \
  -H 'apikey: YOUR_SUPABASE_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@test.com","password":"admin123"}' | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

## 2. Получить все тикеты

```bash
curl -X GET 'http://localhost:8000/api/tickets' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

**Или с токеном напрямую:**
```bash
curl -X GET 'http://localhost:8000/api/tickets' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json'
```

---

## 3. Получить тикет по ID

```bash
curl -X GET 'http://localhost:8000/api/tickets/TICKET_ID' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

**Пример:**
```bash
curl -X GET 'http://localhost:8000/api/tickets/c6977a47-761d-464d-987c-888b88e96c3b' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

---

## 4. Создать тикет (ingest)

```bash
curl -X POST 'http://localhost:8000/api/ingest' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "portal",
    "subject": "Не работает интернет",
    "text": "Добрый день, у меня пропал интернет сегодня утром.",
    "incoming_meta": {
      "client_email": "client@example.com"
    }
  }'
```

---

## 5. Обновить тикет

```bash
curl -X PATCH 'http://localhost:8000/api/tickets/TICKET_ID' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "accepted",
    "priority": "high"
  }'
```

---

## 6. Принять тикет

```bash
curl -X POST 'http://localhost:8000/api/tickets/TICKET_ID/accept' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

---

## 7. Завершить тикет удаленно

```bash
curl -X POST 'http://localhost:8000/api/tickets/TICKET_ID/complete_remote' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

---

## 8. Запросить выезд инженера

```bash
curl -X POST 'http://localhost:8000/api/tickets/TICKET_ID/request_on_site' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

---

## 9. Получить сообщения тикета

```bash
curl -X GET 'http://localhost:8000/api/tickets/TICKET_ID/messages' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

---

## 10. Получить метрики (только для admin)

```bash
curl -X GET 'http://localhost:8000/api/admin/metrics' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

**С параметрами дат:**
```bash
curl -X GET 'http://localhost:8000/api/admin/metrics?from_date=2024-01-01T00:00:00&to_date=2024-12-31T23:59:59' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json'
```

---

## 11. Обработать тикет через AI

```bash
curl -X POST 'http://localhost:8000/api/ai/process' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "ticket_id": "TICKET_ID"
  }'
```

---

## 12. Поиск в Knowledge Base

```bash
curl -X POST 'http://localhost:8000/api/ai/search' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "не работает интернет",
    "k": 5
  }'
```

---

## Полный скрипт с авторизацией

Сохраните как `test_api.sh`:

```bash
#!/bin/bash

# Настройки
SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY="YOUR_SUPABASE_ANON_KEY"
BACKEND_URL="http://localhost:8000"
EMAIL="admin@test.com"
PASSWORD="admin123"

# Логин и получение токена
echo "🔐 Logging in..."
TOKEN=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
  -H "apikey: ${SUPABASE_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  exit 1
fi

echo "✅ Token received: ${TOKEN:0:50}..."

# Получить тикеты
echo ""
echo "📋 Getting tickets..."
curl -X GET "${BACKEND_URL}/api/tickets" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'

# Создать тикет
echo ""
echo "➕ Creating ticket..."
curl -X POST "${BACKEND_URL}/api/ingest" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "portal",
    "subject": "Тестовый тикет из curl",
    "text": "Это тестовое обращение",
    "incoming_meta": {}
  }' | jq '.'

# Получить метрики
echo ""
echo "📊 Getting metrics..."
curl -X GET "${BACKEND_URL}/api/admin/metrics" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" | jq '.'
```

**Использование:**
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Быстрый тест (одной командой)

```bash
# Логин + получение тикетов
curl -X GET 'http://localhost:8000/api/tickets' \
  -H "Authorization: Bearer $(curl -s -X POST 'https://YOUR_PROJECT_ID.supabase.co/auth/v1/token?grant_type=password' \
    -H 'apikey: YOUR_SUPABASE_ANON_KEY' \
    -H 'Content-Type: application/json' \
    -d '{"email":"admin@test.com","password":"admin123"}' | jq -r '.access_token')" \
  -H 'Content-Type: application/json'
```

---

## Проверка здоровья API

```bash
curl -X GET 'http://localhost:8000/health'
```

**Ответ:**
```json
{
  "status": "healthy"
}
```

---

## Форматированный вывод (с jq)

Для красивого вывода JSON установите `jq`:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

**Пример:**
```bash
curl -X GET 'http://localhost:8000/api/tickets' \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

## Переменные окружения

Создайте файл `.env` и используйте:
```bash
source .env

curl -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}"
```

