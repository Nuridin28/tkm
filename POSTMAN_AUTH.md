# Авторизация через Postman

## Шаг 1: Логин через Supabase Auth API

### Запрос 1: Получить токен (Login)

**Method:** `POST`  
**URL:** `https://YOUR_PROJECT_ID.supabase.co/auth/v1/token?grant_type=password`

**Headers:**
```
apikey: YOUR_SUPABASE_ANON_KEY
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "admin@test.com",
  "password": "admin123"
}
```

**Пример полного запроса:**
```
POST https://your-project.supabase.co/auth/v1/token?grant_type=password
Headers:
  apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  Content-Type: application/json

Body:
{
  "email": "admin@test.com",
  "password": "admin123"
}
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
    "email": "admin@test.com",
    ...
  }
}
```

**Сохраните `access_token` - он понадобится для запросов к бэкенду!**

---

## Шаг 2: Использование токена для запросов к бэкенду

### Запрос 2: Получить тикеты (пример)

**Method:** `GET`  
**URL:** `http://localhost:8000/api/tickets`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Пример:**
```
GET http://localhost:8000/api/tickets
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  Content-Type: application/json
```

---

## Настройка Postman Collection

### 1. Создать Environment Variables

Создайте Environment в Postman со следующими переменными:

```
SUPABASE_URL: https://your-project.supabase.co
SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
BACKEND_URL: http://localhost:8000
ACCESS_TOKEN: (будет установлен автоматически после логина)
```

### 2. Запрос для логина

**Request Name:** `Login`  
**Method:** `POST`  
**URL:** `{{SUPABASE_URL}}/auth/v1/token?grant_type=password`

**Headers:**
```
apikey: {{SUPABASE_ANON_KEY}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "email": "admin@test.com",
  "password": "admin123"
}
```

**Tests (Script для автоматического сохранения токена):**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("ACCESS_TOKEN", response.access_token);
    pm.environment.set("USER_ID", response.user.id);
    console.log("✅ Token saved:", response.access_token);
}
```

### 3. Запросы к бэкенду

**Request Name:** `Get Tickets`  
**Method:** `GET`  
**URL:** `{{BACKEND_URL}}/api/tickets`

**Headers:**
```
Authorization: Bearer {{ACCESS_TOKEN}}
Content-Type: application/json
```

---

## Примеры запросов к бэкенду

### Получить все тикеты
```
GET http://localhost:8000/api/tickets
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Получить тикет по ID
```
GET http://localhost:8000/api/tickets/{ticket_id}
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Создать тикет (ingest)
```
POST http://localhost:8000/api/ingest
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

Body:
{
  "source": "portal",
  "subject": "Тестовый тикет",
  "text": "Описание проблемы",
  "incoming_meta": {}
}
```

### Получить метрики (только для admin)
```
GET http://localhost:8000/api/admin/metrics
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Принять тикет
```
POST http://localhost:8000/api/tickets/{ticket_id}/accept
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## Получение Supabase credentials

### Где найти SUPABASE_URL и SUPABASE_ANON_KEY:

1. Откройте Supabase Dashboard: https://app.supabase.com
2. Выберите ваш проект
3. Перейдите в Settings → API
4. Скопируйте:
   - **Project URL** → это `SUPABASE_URL`
   - **anon/public key** → это `SUPABASE_ANON_KEY`

Или проверьте файл `frontend/.env`:
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Troubleshooting

### Ошибка 401 Unauthorized
- Проверьте, что токен не истек (токены живут 1 час)
- Выполните логин заново для получения нового токена

### Ошибка 403 Forbidden
- Проверьте роль пользователя в `public.users`
- Убедитесь, что RLS политики разрешают доступ

### Ошибка "Invalid API key"
- Проверьте правильность `SUPABASE_ANON_KEY`
- Убедитесь, что используете `anon` key, а не `service_role` key

---

## Полный пример Postman Collection (JSON)

Сохраните это как `.json` файл и импортируйте в Postman:

```json
{
  "info": {
    "name": "AI Help Desk API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 200) {",
                  "    const response = pm.response.json();",
                  "    pm.environment.set(\"ACCESS_TOKEN\", response.access_token);",
                  "    pm.environment.set(\"USER_ID\", response.user.id);",
                  "}"
                ]
              }
            }
          ],
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "apikey",
                "value": "{{SUPABASE_ANON_KEY}}",
                "type": "text"
              },
              {
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"admin@test.com\",\n  \"password\": \"admin123\"\n}"
            },
            "url": {
              "raw": "{{SUPABASE_URL}}/auth/v1/token?grant_type=password",
              "host": ["{{SUPABASE_URL}}"],
              "path": ["auth", "v1", "token"],
              "query": [
                {
                  "key": "grant_type",
                  "value": "password"
                }
              ]
            }
          }
        }
      ]
    },
    {
      "name": "Tickets",
      "item": [
        {
          "name": "Get All Tickets",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{ACCESS_TOKEN}}",
                "type": "text"
              }
            ],
            "url": {
              "raw": "{{BACKEND_URL}}/api/tickets",
              "host": ["{{BACKEND_URL}}"],
              "path": ["api", "tickets"]
            }
          }
        },
        {
          "name": "Create Ticket",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{ACCESS_TOKEN}}",
                "type": "text"
              },
              {
                "key": "Content-Type",
                "value": "application/json",
                "type": "text"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"source\": \"portal\",\n  \"subject\": \"Test ticket\",\n  \"text\": \"Test description\"\n}"
            },
            "url": {
              "raw": "{{BACKEND_URL}}/api/ingest",
              "host": ["{{BACKEND_URL}}"],
              "path": ["api", "ingest"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "SUPABASE_URL",
      "value": "https://your-project.supabase.co"
    },
    {
      "key": "SUPABASE_ANON_KEY",
      "value": "your-anon-key"
    },
    {
      "key": "BACKEND_URL",
      "value": "http://localhost:8000"
    },
    {
      "key": "ACCESS_TOKEN",
      "value": ""
    }
  ]
}
```

