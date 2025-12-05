# Настройка переменных окружения для Frontend

## Проблема: "supabaseUrl is required"

Эта ошибка возникает, когда переменные окружения Supabase не настроены.

## Решение:

1. **Создайте файл `.env` в директории `frontend/`**

2. **Добавьте следующие переменные:**

```env
VITE_SUPABASE_URL=https://ваш-проект.supabase.co
VITE_SUPABASE_KEY=ваш-anon-key
VITE_API_URL=http://localhost:8000
```

3. **Где взять значения:**

   - Откройте ваш Supabase проект
   - Перейдите в **Settings** → **API**
   - Скопируйте:
     - **Project URL** → `VITE_SUPABASE_URL`
     - **anon public** key → `VITE_SUPABASE_KEY`

4. **Перезапустите dev server:**

```bash
# Остановите текущий процесс (Ctrl+C)
# Затем запустите снова:
npm run dev
```

## Пример правильного .env файла:

```env
VITE_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
VITE_SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYzODk2NzI5MCwiZXhwIjoxOTU0NTQzMjkwfQ.example
VITE_API_URL=http://localhost:8000
```

## Важно:

- ⚠️ **НЕ коммитьте `.env` файл в git** (он уже в .gitignore)
- ✅ Используйте `anon` key, а не `service_role` key
- ✅ После изменения `.env` нужно перезапустить dev server

