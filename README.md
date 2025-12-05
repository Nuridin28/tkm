# ИИ Help Desk System

Интеллектуальная система обработки обращений клиентов с использованием OpenAI для автоматической классификации, маршрутизации и решения заявок.

## Технологический стек

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL + Auth + Storage + Vectors)
- **AI**: OpenAI (GPT-4o-mini, text-embedding-3-small)
- **Queue**: Redis + Celery (опционально)
- **Deployment**: Docker

## Основные возможности

✅ **Автоматическая классификация** тикетов с помощью OpenAI  
✅ **RAG (Retrieval Augmented Generation)** для поиска по базе знаний  
✅ **Автоматическое решение** простых тикетов  
✅ **SLA мониторинг** и автоматическая эскалация  
✅ **Ролевая модель доступа** (RBAC)  
✅ **Мультиязычность** (RU/KZ)  
✅ **Дашборды** для разных ролей (Admin, Department, Engineer)  

## Структура проекта

```
.
├── backend/              # FastAPI приложение
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Конфигурация, auth, database
│   │   ├── models/      # Pydantic схемы
│   │   ├── services/    # Бизнес-логика (AI, Tickets, SLA)
│   │   └── tasks/       # Фоновые задачи
│   ├── main.py
│   └── requirements.txt
├── frontend/             # React приложение
│   ├── src/
│   │   ├── components/  # React компоненты
│   │   ├── pages/       # Страницы приложения
│   │   ├── services/    # API клиент
│   │   ├── contexts/    # React контексты (Auth)
│   │   └── styles/      # CSS стили
│   └── package.json
├── supabase/            # Database migrations
│   └── migrations/
├── docker-compose.yml
└── README.md
```

## Быстрый старт

Подробные инструкции по развертыванию см. в [DEPLOYMENT.md](./DEPLOYMENT.md)

### Краткая версия:

1. **Настройте Supabase**:
   - Создайте проект
   - Выполните миграции из `supabase/migrations/`

2. **Настройте Backend**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   # Создайте .env файл с настройками
   uvicorn main:app --reload
   ```

3. **Настройте Frontend**:
   ```bash
   cd frontend
   npm install
   # Создайте .env файл с настройками
   npm run dev
   ```

## API Endpoints

Основные endpoints:

- `POST /api/ingest` - Прием обращений
- `POST /api/ai/process` - Обработка тикета ИИ
- `GET /api/tickets` - Список тикетов
- `GET /api/tickets/{id}` - Детали тикета
- `PATCH /api/tickets/{id}` - Обновление тикета
- `GET /api/admin/metrics` - Метрики (только для админов)

Полная документация доступна после запуска backend: `http://localhost:8000/docs`

## Роли пользователей

- **admin** - Полный доступ ко всем функциям
- **supervisor** - Просмотр метрик и управление несколькими отделами
- **department_user** - Работа с тикетами своего отдела
- **operator** - Оператор техподдержки
- **call_agent** - Создание тикетов из звонков
- **engineer** - Инженер для выездных работ
- **manager** - Менеджер отдела

## База данных

Схема БД включает следующие основные таблицы:

- `users` - Пользователи системы
- `departments` - Отделы с настройками SLA
- `clients` - Клиенты компании
- `tickets` - Тикеты/обращения
- `messages` - Сообщения в тикетах
- `faq_kb` - База знаний
- `embeddings` - Векторные представления для RAG
- `ai_logs` - Логи работы ИИ

## AI Pipeline

Система использует OpenAI для:

1. **Определения языка** (RU/KZ)
2. **Классификации** тикета (категория, приоритет, отдел)
3. **Поиска** релевантных статей в KB (RAG)
4. **Генерации ответов** клиентам
5. **Резюмирования** обращений

## SLA и эскалация

- Автоматический расчет дедлайнов на основе настроек отделов
- Мониторинг нарушений SLA
- Автоматическая эскалация просроченных тикетов
- Флаг для выездных работ при превышении remote SLA

## Лицензия

MIT

