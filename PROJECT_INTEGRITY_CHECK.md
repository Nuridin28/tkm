# Проверка целостности проекта

## ✅ Результаты проверки

### 1. База данных - Supabase

**Статус:** ✅ Все компоненты используют одну и ту же базу данных

#### Конфигурация подключения:

**Backend (`backend/.env`):**
- `SUPABASE_URL` - URL проекта Supabase
- `SUPABASE_KEY` - anon key (публичный ключ)
- `SUPABASE_SERVICE_KEY` - service_role key (административный ключ)

**Frontend (`frontend/.env`):**
- `VITE_SUPABASE_URL` - URL проекта Supabase
- `VITE_SUPABASE_KEY` - anon key (публичный ключ)

**Call Helper (`call_helper/.env`):**
- `SUPABASE_URL` - URL проекта Supabase
- `SUPABASE_SERVICE_ROLE_KEY` - service_role key (для индексации)

**Использование ключей:**
- ✅ Backend использует `SUPABASE_KEY` (anon) для обычных операций
- ✅ Backend использует `SUPABASE_SERVICE_KEY` (service_role) для административных операций
- ✅ Frontend использует `VITE_SUPABASE_KEY` (anon) для клиентских операций
- ✅ Call Helper использует `SUPABASE_SERVICE_ROLE_KEY` (service_role) для записи chunks

### 2. Структура таблиц

**Основные таблицы (миграция 001):**
- ✅ `users` - пользователи системы
- ✅ `departments` - отделы
- ✅ `clients` - клиенты
- ✅ `services` - услуги
- ✅ `tickets` - тикеты
- ✅ `messages` - сообщения в тикетах
- ✅ `faq_kb` - база знаний FAQ
- ✅ `embeddings` - векторные представления (старая таблица)
- ✅ `ai_logs` - логи работы ИИ
- ✅ `offices` - офисы
- ✅ `engineers` - инженеры
- ✅ `ticket_history` - история изменений тикетов

**Дополнительные таблицы:**
- ✅ `chunks` (миграция 009) - чанки документов для RAG
- ✅ `classification_feedback` (миграция 008) - обратная связь по классификации
- ✅ `response_times` (миграция 008) - время ответа
- ✅ `routing_errors` (миграция 008) - ошибки маршрутизации

### 3. Источники тикетов (source)

**Определены в миграциях:**
- ✅ `portal` - портал (миграция 001)
- ✅ `chat` - чат (миграция 001)
- ✅ `email` - email (миграция 001)
- ✅ `phone` - телефон (миграция 001)
- ✅ `call_agent` - оператор (миграция 001)
- ✅ `telegram` - Telegram бот (миграция 006)
- ✅ `whatsapp` - WhatsApp бот (миграция 007)

**Использование в коде:**
- ✅ `backend/app/models/schemas.py` - все источники определены в enum `TicketSource`
- ✅ Backend API поддерживает все источники

### 4. RAG система (chunks)

**Таблица chunks:**
- ✅ Создана в миграции `009_add_chunks_table.sql`
- ✅ Используется в `backend/app/api/v1/public_chat.py` через функцию `match_documents`
- ✅ Используется в `call_helper/ingest.py` для записи чанков
- ✅ Используется в `call_helper/app/api/chat/route.ts` (Next.js API)

**Функция match_documents:**
- ✅ Определена в миграции 009
- ✅ Используется в backend через `supabase.rpc("match_documents", ...)`
- ✅ Используется в call_helper через `supabase.rpc("match_documents", ...)`

**Параметры функции:**
- `query_embedding` - vector(1536)
- `match_count` - int (по умолчанию 6)
- `filter` - jsonb (для фильтрации по source_type, doc_id)

### 5. OpenAI конфигурация

**Модели:**
- ✅ `OPENAI_MODEL` = "gpt-4o-mini" (backend)
- ✅ `OPENAI_EMBEDDING_MODEL` = "text-embedding-3-small" (backend)
- ✅ `EMBED_MODEL` = "text-embedding-3-small" (call_helper)

**Использование:**
- ✅ Backend использует для классификации, генерации ответов, embeddings
- ✅ Call Helper использует для создания embeddings при индексации

### 6. Потенциальные проблемы

#### ⚠️ Дублирование таблицы embeddings

**Проблема:** Есть две таблицы для хранения embeddings:
1. `embeddings` (миграция 001) - старая таблица
2. `chunks` (миграция 009) - новая таблица для RAG

**Статус:** 
- ✅ `chunks` используется для RAG системы в `public_chat.py`
- ⚠️ `embeddings` используется в `ai_service.py` через функцию `match_embeddings`

**Найдено:**
- `backend/app/services/ai_service.py` - использует `match_embeddings` для таблицы `embeddings`
- `backend/app/api/v1/public_chat.py` - использует `match_documents` для таблицы `chunks`

**Рекомендация:** 
1. Обновить `ai_service.py` для использования `chunks` и `match_documents` вместо `embeddings`
2. Или оставить обе таблицы, если они используются для разных целей
3. Документировать разницу между таблицами

#### ⚠️ Разные названия переменных окружения

**Проблема:** В разных компонентах используются разные названия для service_role ключа:
- Backend: `SUPABASE_SERVICE_KEY`
- Call Helper: `SUPABASE_SERVICE_ROLE_KEY`

**Статус:** ⚠️ Это может привести к путанице

**Рекомендация:** Унифицировать названия или добавить алиасы.

### 7. Проверка миграций

**Порядок миграций:**
1. ✅ `001_initial_schema.sql` - основная схема
2. ✅ `002_rls_policies.sql` - политики безопасности
3. ✅ `003_seed_data.sql` - начальные данные
4. ✅ `004_create_test_users.sql` - тестовые пользователи
5. ✅ `005_add_department_description.sql` - описание департаментов
6. ✅ `006_add_telegram_source.sql` - источник Telegram
7. ✅ `007_add_whatsapp_source.sql` - источник WhatsApp
8. ✅ `008_add_monitoring_tables.sql` - таблицы мониторинга
9. ✅ `009_add_chunks_table.sql` - таблица chunks для RAG

**Статус:** ✅ Все миграции на месте и в правильном порядке

### 8. Использование таблиц в коде

**Backend использует:**
- ✅ `tickets` - основная таблица тикетов
- ✅ `messages` - сообщения
- ✅ `users` - пользователи
- ✅ `departments` - отделы
- ✅ `chunks` - для RAG (через match_documents)
- ✅ `classification_feedback` - обратная связь
- ✅ `response_times` - время ответа
- ✅ `routing_errors` - ошибки маршрутизации
- ✅ `ai_logs` - логи ИИ
- ✅ `ticket_history` - история изменений

**Call Helper использует:**
- ✅ `chunks` - для записи и чтения чанков

**Frontend использует:**
- ✅ Supabase клиент для аутентификации
- ✅ API backend для всех операций с данными

## ✅ Итоговый статус

**Целостность проекта:** ✅ **ХОРОШАЯ**

Все компоненты используют одну и ту же базу данных Supabase. Структура таблиц согласована. Есть несколько незначительных моментов для улучшения:

1. ⚠️ Унифицировать названия переменных окружения для service_role ключа
2. ⚠️ Две системы RAG работают параллельно:
   - Старая: `embeddings` + `match_embeddings` (используется в `ai_service.py`)
   - Новая: `chunks` + `match_documents` (используется в `public_chat.py`)

### Две системы RAG

**Старая система (embeddings):**
- Таблица: `embeddings`
- Функция: `match_embeddings`
- Использование: `backend/app/services/ai_service.py` → `retrieve_kb()`
- Назначение: Поиск в FAQ и других источниках

**Новая система (chunks):**
- Таблица: `chunks`
- Функция: `match_documents`
- Использование: `backend/app/api/v1/public_chat.py` → RAG для публичного чата
- Назначение: Поиск в документации Kazakhtelecom PDF

**Рекомендация:** Обе системы могут работать параллельно, но стоит документировать их различия и назначение.

## Рекомендации

1. **Создать единый файл `.env.example`** с описанием всех переменных окружения для всех компонентов
2. **Документировать использование таблиц** - какая таблица для чего используется
3. **Проверить использование таблицы `embeddings`** - используется ли она где-то еще кроме старого кода

