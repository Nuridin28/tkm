#!/bin/bash

# Быстрые примеры curl запросов с вашими credentials

# 1. Сохранить токен в переменную
TOKEN="eyJhbGciOiJIUzI1NiIsImtpZCI6IjJ5ZXNXV2x2ZXl5bjdlN0MiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2toZnF1dHFhZG1ucnBzeWFja2V6LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJhNTZhZTNkNS1iNzlkLTRjOWMtYjI5NS03YTJhYmI0Zjk5MWQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzY0OTM1Nzg2LCJpYXQiOjE3NjQ5MzIxODYsImVtYWlsIjoiYWRtaW5AdGVzdC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc2NDkzMjE4Nn1dLCJzZXNzaW9uX2lkIjoiN2NjZWM4MGEtNTBkZS00OGYxLWEwNzQtZGQyZDFhZmVjZWZiIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.gTE_AdcDRnr_t4MQVB77OIm7YGbvHnMd1GpBDz2_zqw"

# 2. Получить все тикеты
echo "📋 Получение тикетов..."
curl -X GET 'http://localhost:8000/api/tickets' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' | jq '.'

# 3. Создать новый тикет
echo ""
echo "➕ Создание тикета..."
curl -X POST 'http://localhost:8000/api/ingest' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "source": "portal",
    "subject": "Тестовый тикет из curl",
    "text": "Это тестовое обращение для проверки API",
    "incoming_meta": {
      "client_email": "test@example.com"
    }
  }' | jq '.'

# 4. Получить метрики (admin)
echo ""
echo "📊 Получение метрик..."
curl -X GET 'http://localhost:8000/api/admin/metrics' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' | jq '.'

# 5. Проверка здоровья API
echo ""
echo "🏥 Проверка здоровья API..."
curl -X GET 'http://localhost:8000/health' | jq '.'

