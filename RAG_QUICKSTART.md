# Быстрый старт RAG системы

## Что было сделано

✅ Интегрирована RAG система из `call_helper` в основной проект
✅ Создана таблица `chunks` и функция `match_documents` в Supabase
✅ Обновлен backend API для работы с RAG
✅ Обновлен фронтенд для отображения источников
✅ Добавлены все необходимые зависимости

## Быстрый запуск (5 шагов)

### 1. Применить миграцию в Supabase

В Supabase SQL Editor выполните:
```sql
-- Файл: supabase/migrations/009_add_chunks_table.sql
```

### 2. Индексировать документы

```bash
cd call_helper
python3 -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install pymupdf tiktoken supabase openai tqdm python-dotenv

# Создайте .env с:
# OPENAI_API_KEY=sk-...
# SUPABASE_URL=https://...
# SUPABASE_SERVICE_ROLE_KEY=...

python3 ingest.py
```

### 3. Обновить зависимости backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Запустить backend

```bash
cd backend
uvicorn main:app --reload
```

### 5. Запустить frontend

```bash
cd frontend
npm run dev
```

## Проверка работы

1. Откройте `http://localhost:5173`
2. Перейдите на страницу "Public Support"
3. Задайте вопрос: "Какие тарифы на интернет?"

Должен прийти ответ с источниками (номера страниц)!

## Полная инструкция

См. `RAG_SETUP.md` для детальной инструкции.

