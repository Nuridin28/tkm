# Переменные окружения проекта

## Общие переменные для всех компонентов

### Supabase

**URL проекта:**
- `SUPABASE_URL` - URL вашего Supabase проекта (например: `https://xxxxx.supabase.co`)

**Ключи доступа:**
- `SUPABASE_KEY` / `VITE_SUPABASE_KEY` - **anon key** (публичный ключ)
  - Используется для клиентских операций (frontend, обычные запросы backend)
  - Имеет ограниченные права доступа (согласно RLS политикам)
  
- `SUPABASE_SERVICE_KEY` / `SUPABASE_SERVICE_ROLE_KEY` - **service_role key** (административный ключ)
  - Используется для административных операций (backend, индексация документов)
  - Имеет полный доступ к базе данных (обходит RLS)
  - ⚠️ **НИКОГДА не используйте в frontend!**

### OpenAI

- `OPENAI_API_KEY` - API ключ OpenAI (начинается с `sk-`)
  - Используется для всех AI операций
  - Получите на [platform.openai.com](https://platform.openai.com/account/api-keys)

---

## Backend (`backend/.env`)

```env
# Supabase
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_KEY=ваш-anon-key
SUPABASE_SERVICE_KEY=ваш-service-role-key
DATABASE_URL=postgresql://postgres:пароль@db.supabase.co:5432/postgres

# OpenAI
OPENAI_API_KEY=sk-ваш-openai-ключ
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0

# Приложение
SECRET_KEY=любой-секретный-ключ-для-приложения
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# SLA настройки
DEFAULT_SLA_ACCEPT_MINUTES=15
DEFAULT_SLA_REMOTE_MINUTES=60

# Telegram Bot (опционально)
TELEGRAM_BOT_API_KEY=ваш-telegram-bot-api-key
```

**Описание:**
- `SUPABASE_KEY` - используется для обычных операций с БД
- `SUPABASE_SERVICE_KEY` - используется для административных операций (создание тикетов, RAG)
- `DATABASE_URL` - прямая ссылка на PostgreSQL (опционально, для прямых SQL запросов)

---

## Frontend (`frontend/.env`)

```env
VITE_SUPABASE_URL=https://ваш-проект.supabase.co
VITE_SUPABASE_KEY=ваш-anon-key
VITE_API_URL=http://localhost:8000
```

**Описание:**
- `VITE_SUPABASE_URL` - URL Supabase проекта
- `VITE_SUPABASE_KEY` - anon key (публичный ключ)
- `VITE_API_URL` - URL backend API

**⚠️ Важно:** Frontend использует только anon key для безопасности!

---

## Call Helper (`call_helper/.env`)

```env
OPENAI_API_KEY=sk-ваш-openai-ключ
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_SERVICE_ROLE_KEY=ваш-service-role-key
```

**Описание:**
- `SUPABASE_SERVICE_ROLE_KEY` - service_role key (нужен для записи chunks в БД)
- Используется только для индексации документов (скрипт `ingest.py`)

**⚠️ Важно:** Используйте service_role key, так как нужны права на запись в таблицу `chunks`!

---

## Telegram Bot (`telegram_bot/.env`)

```env
TELEGRAM_BOT_TOKEN=ваш-telegram-bot-token
API_URL=http://localhost:8000
TELEGRAM_API_KEY=ваш-telegram-api-key
```

**Описание:**
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `API_URL` - URL backend API
- `TELEGRAM_API_KEY` - ключ для аутентификации запросов от бота к backend

---

## WhatsApp Bot (`whatsapp_bot/.env`)

```env
API_URL=http://localhost:8000
```

**Описание:**
- `API_URL` - URL backend API

---

## Где получить ключи?

### Supabase

1. Откройте [Supabase Dashboard](https://app.supabase.com)
2. Выберите ваш проект
3. Перейдите в **Settings** → **API**
4. Скопируйте:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY` / `VITE_SUPABASE_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY` / `SUPABASE_SERVICE_ROLE_KEY`

### OpenAI

1. Откройте [OpenAI Platform](https://platform.openai.com)
2. Перейдите в **API keys**
3. Создайте новый ключ или используйте существующий
4. Скопируйте ключ (начинается с `sk-`)

### Telegram Bot

1. Откройте [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен

---

## Безопасность

### ✅ Правильно:
- Использовать anon key в frontend
- Использовать service_role key только в backend и скриптах
- Хранить `.env` файлы в `.gitignore`
- Не коммитить ключи в репозиторий

### ❌ Неправильно:
- Использовать service_role key в frontend
- Коммитить `.env` файлы с реальными ключами
- Делиться ключами публично

---

## Проверка конфигурации

После настройки переменных окружения проверьте:

1. **Backend:**
   ```bash
   cd backend
   python -c "from app.core.config import settings; print('✅ Config OK')"
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm run dev
   # Проверьте, что нет ошибок в консоли
   ```

3. **Call Helper:**
   ```bash
   cd call_helper
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ Config OK' if os.getenv('SUPABASE_URL') else '❌ Config missing')"
   ```

---

## Обновление ключей

Если нужно обновить ключи:

1. Обновите соответствующие `.env` файлы
2. Перезапустите все сервисы:
   - Backend
   - Frontend
   - Telegram/WhatsApp боты (если запущены)

---

## Troubleshooting

### Ошибка: "Invalid API key"
- Проверьте, что ключ скопирован полностью (без пробелов)
- Проверьте, что ключ правильный (не истек, не удален)

### Ошибка: "Permission denied"
- Проверьте, что используете правильный ключ (anon vs service_role)
- Проверьте RLS политики в Supabase

### Ошибка: "Connection refused"
- Проверьте, что URL правильный
- Проверьте, что проект активен в Supabase

