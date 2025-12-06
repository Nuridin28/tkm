# Email Bot для Help Desk

Email бот для автоматической обработки входящих писем через AI с RAG.

## Возможности

- ✅ Автоматическая обработка входящих email писем
- ✅ Интеграция с backend API для RAG поиска
- ✅ Автоматическое создание тикетов при необходимости
- ✅ Сохранение истории разговора для контекста
- ✅ Отправка ответов по email
- ✅ Отслеживание обработанных писем (избежание дубликатов)

## Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте конфигурацию:
```bash
cp .env.example .env
# Отредактируйте .env файл и заполните необходимые переменные
```

## Конфигурация

### Email настройки

Для Gmail:
1. Включите двухфакторную аутентификацию
2. Создайте App Password: https://myaccount.google.com/apppasswords
3. Используйте App Password в `EMAIL_PASSWORD`

### Переменные окружения

- `EMAIL_IMAP_SERVER` - IMAP сервер (по умолчанию: imap.gmail.com)
- `EMAIL_IMAP_PORT` - IMAP порт (по умолчанию: 993)
- `EMAIL_SMTP_SERVER` - SMTP сервер (по умолчанию: smtp.gmail.com)
- `EMAIL_SMTP_PORT` - SMTP порт (по умолчанию: 587)
- `EMAIL_USERNAME` - Email адрес для входа
- `EMAIL_PASSWORD` - Пароль или App Password
- `EMAIL_FROM` - Email адрес отправителя
- `EMAIL_FROM_NAME` - Имя отправителя
- `CHECK_INTERVAL` - Интервал проверки новых писем в секундах (по умолчанию: 60)
- `API_URL` - URL backend API (по умолчанию: http://localhost:8000)
- `EMAIL_BOT_API_KEY` - API ключ для аутентификации в backend (опционально)

## Запуск

```bash
./run.sh
```

Или вручную:
```bash
source venv/bin/activate
python3 bot.py
```

## Остановка

```bash
./stop.sh
```

## Как это работает

1. Бот подключается к IMAP серверу и проверяет новые непрочитанные письма
2. Для каждого нового письма:
   - Извлекает текст из письма
   - Отправляет запрос в backend API (`/api/public/chat`)
   - Получает ответ от AI с RAG
   - Если ответ найден - отправляет его по email
   - Если ответ не найден или требуется вмешательство - создает тикет
3. Сохраняет историю разговора для контекста в следующих сообщениях
4. Отслеживает обработанные письма в SQLite базе данных

## Логи

Логи сохраняются в файл `bot.log` в директории бота.

## Интеграция с Backend

Бот использует тот же API endpoint, что и Telegram/WhatsApp боты:
- `POST /api/public/chat` - для анализа сообщений и получения ответов
- `POST /api/public/chat/create-ticket` - для создания тикетов

## Структура проекта

```
email_bot/
├── bot.py              # Основной файл бота
├── api_client.py        # Клиент для backend API
├── config.py           # Конфигурация
├── models.py           # Модели данных
├── requirements.txt    # Зависимости
├── .env.example        # Пример конфигурации
├── run.sh              # Скрипт запуска
├── stop.sh             # Скрипт остановки
└── README.md           # Документация
```

## Примечания

- Бот обрабатывает только plain text и HTML письма
- Вложения игнорируются
- Письма помечаются как обработанные в локальной SQLite базе
- История разговора хранится в памяти (сессии по email адресу)

