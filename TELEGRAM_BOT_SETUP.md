# Telegram Bot Setup Guide

## Обзор

Telegram бот для приема обращений от пользователей с автоматической обработкой через RAG/AI систему.

## Возможности

✅ **Сбор контактной информации:**
- Номер телефона (обязательно)
- Email (опционально)
- Полное имя (обязательно)
- Тип лица: физическое или юридическое

✅ **Автоматическая обработка:**
- Анализ обращения через RAG/AI
- Автоматический ответ на простые вопросы
- Создание тикета для сложных вопросов
- Автоматическая классификация и маршрутизация

## Установка

### 1. Создание бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "Help Desk Support")
   - Введите username бота (например: "your_helpdesk_bot")
4. Сохраните токен бота (выглядит как: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Настройка Backend

Добавьте в `backend/.env`:
```env
TELEGRAM_BOT_API_KEY=your_secret_api_key_here
```

Этот ключ используется для аутентификации запросов от бота к backend. 
**Важно:** Используйте сложный случайный ключ в продакшене!

### 3. Настройка Telegram Bot

1. Перейдите в папку `telegram_bot`:
   ```bash
   cd telegram_bot
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Создайте файл `.env`:
   ```bash
   cp .env.example .env
   ```

4. Отредактируйте `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   API_URL=http://localhost:8000
   TELEGRAM_BOT_API_KEY=your_secret_api_key_here  # Должен совпадать с backend/.env
   ```

### 4. Запуск

**Убедитесь, что backend запущен!**

Запустите бота:
```bash
python bot.py
```

Или используйте скрипт:
```bash
./run.sh
```

## Использование

1. Пользователь отправляет `/start` боту
2. Бот запрашивает контактную информацию:
   - Номер телефона (можно отправить контакт или ввести вручную)
   - Email (опционально, можно пропустить)
   - Полное имя
   - Тип лица (физическое/юридическое)
   - Для юридических лиц - название компании
3. Пользователь описывает проблему
4. Система анализирует:
   - Если может ответить сразу (confidence > 0.7) → отправляет ответ
   - Если нет → создает тикет и уведомляет пользователя

## API Endpoints

Бот использует следующие endpoints backend:

### POST `/api/telegram/analyze`
Анализирует сообщение через RAG/AI.

**Request:**
```json
{
  "text": "Текст обращения",
  "contact_info": {
    "phone": "+7...",
    "email": "user@example.com",
    "full_name": "Иван Иванов",
    "user_type": "individual"
  }
}
```

**Response:**
```json
{
  "can_answer": true,
  "answer": "Ответ на вопрос...",
  "category": "network",
  "priority": "medium",
  "department": "TechSupport",
  "subject": "Краткое описание..."
}
```

### POST `/api/telegram/create-ticket`
Создает тикет из Telegram.

**Request:**
```json
{
  "source": "telegram",
  "subject": "Тема обращения",
  "text": "Описание проблемы",
  "contact_info": {...},
  "telegram_user_id": 123456789,
  "telegram_chat_id": 123456789,
  "telegram_username": "username"
}
```

**Response:**
```json
{
  "ticket_id": "uuid",
  "status": "created",
  "priority": "medium",
  "department": "department_id"
}
```

## Безопасность

- Все запросы от бота к backend защищены API ключом (`X-Telegram-API-Key` header)
- Контактная информация передается только в backend, не хранится в боте
- В продакшене рекомендуется использовать более сложную систему аутентификации

## Troubleshooting

**Бот не отвечает:**
- Проверьте токен бота в `telegram_bot/.env`
- Убедитесь, что backend запущен и доступен по `API_URL`
- Проверьте логи бота на наличие ошибок

**Ошибки при создании тикетов:**
- Проверьте `TELEGRAM_BOT_API_KEY` в обоих `.env` файлах (должны совпадать)
- Убедитесь, что backend endpoint `/api/telegram/create-ticket` доступен
- Проверьте логи backend на наличие ошибок

**Ошибки анализа:**
- Проверьте, что OpenAI API ключ настроен в backend
- Убедитесь, что RAG система работает корректно
- Проверьте наличие данных в knowledge base

## Структура проекта

```
telegram_bot/
├── bot.py              # Основной файл бота с conversation handler
├── api_client.py       # Клиент для API backend
├── models.py           # Модели данных (ContactInfo, UserSession, etc.)
├── config.py           # Конфигурация (загрузка из .env)
├── requirements.txt    # Python зависимости
├── run.sh              # Скрипт запуска
└── README.md          # Документация
```

## Разработка

Для разработки можно использовать:
- `python-telegram-bot` версии 20.x для работы с Telegram API
- `httpx` для асинхронных HTTP запросов к backend
- `pydantic` для валидации данных

## Примеры использования

### Тестирование бота

1. Запустите бота
2. Найдите вашего бота в Telegram по username
3. Отправьте `/start`
4. Следуйте инструкциям бота

### Тестирование API напрямую

```bash
curl -X POST http://localhost:8000/api/telegram/analyze \
  -H "Content-Type: application/json" \
  -H "X-Telegram-API-Key: your_secret_api_key" \
  -d '{
    "text": "У меня не работает интернет",
    "contact_info": {
      "phone": "+79001234567",
      "full_name": "Иван Иванов",
      "user_type": "individual"
    }
  }'
```

