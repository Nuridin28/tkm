# Инструкция по настройке и запуску RAG системы

## Обзор

Проект интегрирован с RAG (Retrieval-Augmented Generation) системой из `call_helper`. Система использует:
- Таблицу `chunks` в Supabase для хранения чанков документов с embeddings
- Функцию `match_documents` для векторного поиска
- OpenAI для генерации embeddings и ответов

## Шаг 1: Настройка Supabase

### 1.1. Применение миграций

Выполните все миграции в Supabase SQL Editor по порядку:

1. `supabase/migrations/001_initial_schema.sql` - основная схема
2. `supabase/migrations/002_rls_policies.sql` - политики безопасности
3. `supabase/migrations/003_seed_data.sql` - начальные данные
4. `supabase/migrations/004_create_test_users.sql` - тестовые пользователи (опционально)
5. `supabase/migrations/005_add_department_description.sql` - описание департаментов
6. `supabase/migrations/006_add_telegram_source.sql` - источник Telegram
7. `supabase/migrations/007_add_whatsapp_source.sql` - источник WhatsApp
8. `supabase/migrations/008_add_monitoring_tables.sql` - таблицы мониторинга
9. **`supabase/migrations/009_add_chunks_table.sql`** - таблица chunks для RAG (НОВАЯ!)

### 1.2. Проверка расширений

Убедитесь, что в Supabase включены расширения:
- `uuid-ossp` (для генерации UUID)
- `vector` (для работы с embeddings) - **ОБЯЗАТЕЛЬНО!**

Проверка:
```sql
SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector');
```

## Шаг 2: Индексация документов (RAG)

### 2.1. Подготовка окружения

Перейдите в директорию `call_helper`:

```bash
cd call_helper
```

### 2.2. Установка зависимостей

```bash
# Создайте виртуальное окружение (если еще не создано)
python3 -m venv venv

# Активируйте его
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install pymupdf tiktoken supabase openai tqdm python-dotenv
```

### 2.3. Настройка переменных окружения

Создайте файл `.env` в директории `call_helper`:

```env
OPENAI_API_KEY=sk-ваш-openai-ключ
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_SERVICE_ROLE_KEY=ваш-service-role-key
```

**Важно:** Используйте `SUPABASE_SERVICE_ROLE_KEY` (service_role ключ), а не anon ключ!

### 2.4. Подготовка PDF документа

Поместите файл `Kazakhtelecom.pdf` в директорию `call_helper/` (если его еще нет).

### 2.5. Запуск индексации

```bash
# Убедитесь, что вы в директории call_helper и venv активирован
python ingest.py
```

Скрипт:
- Извлечет текст из PDF по страницам
- Разобьет на чанки (1 страница = 1 чанк)
- Создаст embeddings для каждого чанка
- Загрузит все в таблицу `chunks` в Supabase

**Время выполнения:** зависит от размера PDF (обычно 5-15 минут)

### 2.6. Проверка индексации

В Supabase SQL Editor выполните:

```sql
-- Проверка количества чанков
SELECT COUNT(*) FROM public.chunks;

-- Проверка структуры данных
SELECT doc_id, COUNT(*) as chunks_count 
FROM public.chunks 
GROUP BY doc_id;

-- Проверка метаданных
SELECT metadata->>'source_type', COUNT(*) 
FROM public.chunks 
GROUP BY metadata->>'source_type';
```

Должно быть:
- `doc_id = "kazakhtelecom-v1"`
- `source_type = "kazakhtelecom"`

## Шаг 3: Настройка Backend

### 3.1. Установка зависимостей

```bash
cd backend

# Активируйте виртуальное окружение (если еще не активировано)
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows

# Установите зависимости (включая новые для RAG)
pip install -r requirements.txt
```

### 3.2. Настройка .env

Убедитесь, что в `backend/.env` есть все необходимые переменные:

```env
SUPABASE_URL=https://ваш-проект.supabase.co
SUPABASE_KEY=ваш-anon-key
SUPABASE_SERVICE_KEY=ваш-service-role-key  # Важно для RAG!
DATABASE_URL=postgresql://postgres:пароль@db.supabase.co:5432/postgres

OPENAI_API_KEY=sk-ваш-openai-ключ
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

REDIS_URL=redis://localhost:6379/0

SECRET_KEY=любой-секретный-ключ
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

DEFAULT_SLA_ACCEPT_MINUTES=15
DEFAULT_SLA_REMOTE_MINUTES=60
```

### 3.3. Запуск Backend

```bash
# Убедитесь, что вы в директории backend и venv активирован
uvicorn main:app --reload
```

Backend запустится на `http://localhost:8000`

Проверьте API:
- `http://localhost:8000/docs` - документация API
- `http://localhost:8000/health` - проверка здоровья

## Шаг 4: Настройка Frontend

### 4.1. Установка зависимостей

```bash
cd frontend
npm install
```

### 4.2. Настройка .env

Убедитесь, что в `frontend/.env` есть:

```env
VITE_SUPABASE_URL=https://ваш-проект.supabase.co
VITE_SUPABASE_KEY=ваш-anon-key
VITE_API_URL=http://localhost:8000
```

### 4.3. Запуск Frontend

```bash
npm run dev
```

Frontend запустится на `http://localhost:5173` (или другом порту)

## Шаг 5: Тестирование RAG

### 5.1. Тест через Frontend

1. Откройте `http://localhost:5173`
2. Перейдите на страницу публичной поддержки (Public Support)
3. Задайте вопрос, например:
   - "Какие тарифы на интернет?"
   - "Как подключить услугу?"
   - "Что делать, если не работает интернет?"

### 5.2. Тест через API

```bash
curl -X POST http://localhost:8000/api/public/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Какие тарифы на интернет?",
    "conversation_history": [],
    "contact_info": {"phone": "+77001234567"}
  }'
```

### 5.3. Проверка ответа

Ответ должен содержать:
- `answer` - текст ответа с форматированием Markdown
- `sources` - массив источников с информацией о страницах
- `confidence` - уверенность в ответе (0.0-1.0)
- `ticketCreated` - создан ли тикет (true/false)

## Шаг 6: Обновление документов

Если нужно обновить базу знаний:

1. Обновите `Kazakhtelecom.pdf` в `call_helper/`
2. Запустите `python ingest.py` снова
3. Скрипт автоматически удалит старые чанки и создаст новые

## Устранение неполадок

### Ошибка: "function match_documents does not exist"

**Решение:** Выполните миграцию `009_add_chunks_table.sql` в Supabase SQL Editor.

### Ошибка: "relation chunks does not exist"

**Решение:** Выполните миграцию `009_add_chunks_table.sql`.

### Ошибка: "No chunks found" или пустые ответы

**Решение:** 
1. Проверьте, что индексация выполнена: `SELECT COUNT(*) FROM public.chunks;`
2. Проверьте, что `doc_id = "kazakhtelecom-v1"` и `source_type = "kazakhtelecom"`
3. Перезапустите индексацию: `python ingest.py`

### Ошибка: "OpenAI API error"

**Решение:**
1. Проверьте баланс на [platform.openai.com](https://platform.openai.com)
2. Убедитесь, что API ключ правильный в `.env`
3. Проверьте лимиты API

### Ошибка: "Supabase connection error"

**Решение:**
1. Проверьте URL и ключи в `.env`
2. Убедитесь, что используете правильный ключ:
   - `SUPABASE_KEY` - anon key (для фронтенда)
   - `SUPABASE_SERVICE_KEY` - service_role key (для бэкенда и индексации)

### Медленные ответы

**Решение:**
1. Проверьте индексы в таблице `chunks`:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'chunks';
   ```
2. Убедитесь, что индекс на `embedding` создан (ivfflat)
3. Уменьшите `match_count` в запросе (по умолчанию 6)

## Структура данных

### Таблица chunks

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    doc_id TEXT NOT NULL,           -- ID документа (например, "kazakhtelecom-v1")
    chunk_index INTEGER NOT NULL,    -- Индекс чанка в документе
    content TEXT NOT NULL,           -- Текст чанка
    metadata JSONB,                  -- Метаданные (page, source_type, etc.)
    embedding vector(1536),          -- Embedding вектор
    created_at TIMESTAMPTZ
);
```

### Функция match_documents

```sql
match_documents(
    query_embedding vector(1536),  -- Embedding запроса
    match_count int DEFAULT 6,     -- Количество результатов
    filter jsonb DEFAULT '{}'      -- Фильтры (source_type, doc_id)
)
```

## Дополнительная информация

- **Размер embeddings:** 1536 измерений (text-embedding-3-small)
- **Модель генерации:** gpt-4o-mini
- **Chunking стратегия:** 1 страница PDF = 1 чанк
- **Максимальный размер чанка:** 8000 токенов

## Готово! ✅

Теперь ваша система полностью интегрирована с RAG и готова к использованию!

