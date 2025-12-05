# Инструкция по развертыванию

## Предварительные требования

1. **Python 3.11+**
2. **Node.js 18+**
3. **Docker & Docker Compose** (опционально)
4. **Supabase аккаунт** - создайте проект на [supabase.com](https://supabase.com)
5. **OpenAI API ключ** - получите на [platform.openai.com](https://platform.openai.com)

## Шаг 1: Настройка Supabase

1. Создайте новый проект в Supabase
2. Перейдите в SQL Editor
3. Выполните миграции по порядку:
   - `supabase/migrations/001_initial_schema.sql`
   - `supabase/migrations/002_rls_policies.sql`
   - `supabase/migrations/003_seed_data.sql`
4. Включите расширение `vector` в Database > Extensions
5. Скопируйте URL проекта и API ключи из Settings > API

## Шаг 2: Настройка Backend

1. Перейдите в директорию `backend`:
   ```bash
   cd backend
   ```

2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` в директории `backend`:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
   
   OPENAI_API_KEY=sk-your-openai-api-key
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   
   REDIS_URL=redis://localhost:6379/0
   
   SECRET_KEY=your-secret-key-here
   ENVIRONMENT=development
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   
   DEFAULT_SLA_ACCEPT_MINUTES=15
   DEFAULT_SLA_REMOTE_MINUTES=60
   ```

5. Запустите backend:
   ```bash
   uvicorn main:app --reload
   ```

Backend будет доступен на `http://localhost:8000`
API документация: `http://localhost:8000/docs`

## Шаг 3: Настройка Frontend

1. Перейдите в директорию `frontend`:
   ```bash
   cd frontend
   ```

2. Установите зависимости:
   ```bash
   npm install
   ```

3. Создайте файл `.env` в директории `frontend`:
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_KEY=your-anon-key
   VITE_API_URL=http://localhost:8000
   ```

4. Запустите frontend:
   ```bash
   npm run dev
   ```

Frontend будет доступен на `http://localhost:3000`

## Шаг 4: Настройка Redis (опционально, для очередей)

Если планируете использовать Celery для фоновых задач:

1. Установите Redis:
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Linux
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. Redis будет доступен на `localhost:6379`

## Шаг 5: Создание первого пользователя

1. Откройте Supabase Dashboard
2. Перейдите в Authentication > Users
3. Создайте нового пользователя вручную или через Sign Up
4. Обновите роль пользователя в таблице `users`:
   ```sql
   UPDATE public.users 
   SET role = 'admin' 
   WHERE email = 'your-email@example.com';
   ```

## Развертывание с Docker

1. Создайте `.env` файлы для backend и frontend (см. выше)

2. Запустите через Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Backend: `http://localhost:8000`
4. Frontend: запустите отдельно через `npm run dev`

## Проверка работоспособности

1. Откройте `http://localhost:3000`
2. Войдите с созданным пользователем
3. Создайте тестовый тикет через API:
   ```bash
   curl -X POST http://localhost:8000/api/ingest \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "source": "portal",
       "subject": "Тестовая заявка",
       "text": "Не работает интернет",
       "incoming_meta": {}
     }'
   ```

## Troubleshooting

### Проблемы с подключением к Supabase
- Проверьте правильность URL и ключей в `.env`
- Убедитесь, что RLS политики применены

### Проблемы с OpenAI
- Проверьте баланс API ключа
- Убедитесь, что модель доступна в вашем регионе

### Проблемы с миграциями
- Убедитесь, что расширение `vector` установлено
- Проверьте логи в Supabase Dashboard > Logs

## Production развертывание

### Backend
- Используйте процесс-менеджер (PM2, systemd)
- Настройте reverse proxy (Nginx)
- Используйте переменные окружения из secrets manager
- Настройте мониторинг и логирование

### Frontend
- Соберите production build: `npm run build`
- Разверните на Vercel, Netlify или другом хостинге
- Настройте переменные окружения в панели хостинга

### Database
- Используйте managed Supabase или собственный PostgreSQL
- Настройте регулярные бэкапы
- Мониторьте производительность

