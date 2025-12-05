# Подключение Telegram и WhatsApp ботов с RAG

## ✅ Что было сделано

### 1. Обновлен Telegram endpoint (`/api/telegram/analyze`)
- ✅ Использует RAG логику из `public_chat.py`
- ✅ Поиск в базе знаний через `match_documents`
- ✅ Генерация ответов с использованием найденной информации
- ✅ Определение типа клиента (корпоративный/частный)
- ✅ Автоматическая категоризация тикетов

### 2. Создан WhatsApp endpoint (`/api/whatsapp/analyze`)
- ✅ Полная интеграция с RAG
- ✅ Та же логика что и в Telegram и публичном чате
- ✅ Создание тикетов при необходимости

### 3. Обновлены боты
- ✅ `telegram_bot/bot.py` - использует RAG через API
- ✅ `telegram_bot/api_client.py` - обновлен для передачи conversation_history
- ✅ `whatsapp_bot/bot.js` - полностью переписан с использованием RAG

## Настройка

### 1. Backend (.env)

Добавьте в `backend/.env`:

```env
# Telegram Bot
TELEGRAM_BOT_API_KEY=your_secret_key_here

# WhatsApp Bot (опционально)
WHATSAPP_BOT_API_KEY=your_secret_key_here
```

### 2. Telegram Bot

1. **Установите зависимости:**
   ```bash
   cd telegram_bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Настройте `.env`:**
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   API_URL=http://localhost:8000
   TELEGRAM_BOT_API_KEY=your_secret_api_key_for_backend_auth
   ```

3. **Запустите бота:**
   ```bash
   python bot.py
   ```

### 3. WhatsApp Bot

1. **Установите зависимости:**
   ```bash
   cd whatsapp_bot
   npm install
   ```

2. **Настройте переменные окружения:**
   ```bash
   export API_URL=http://localhost:8000
   export WHATSAPP_BOT_API_KEY=your_secret_key_here
   ```

   Или создайте `.env` файл (если используете dotenv)

3. **Запустите бота:**
   ```bash
   npm start
   ```

   При первом запуске отсканируйте QR-код для авторизации в WhatsApp.

## API Endpoints

### Telegram

**POST `/api/telegram/analyze`**
```json
{
  "text": "Какие тарифы на интернет?",
  "contact_info": {
    "phone": "+77001234567"
  },
  "conversation_history": [
    {"role": "user", "content": "Здравствуйте"},
    {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}
  ]
}
```

**Ответ:**
```json
{
  "can_answer": true,
  "answer": "## Доступные тарифы...",
  "category": "billing",
  "subcategory": "tariffs",
  "priority": "medium",
  "department": "Sales",
  "subject": "Какие тарифы на интернет?",
  "confidence": 0.85
}
```

**POST `/api/telegram/create-ticket`**
```json
{
  "source": "telegram",
  "subject": "Не работает интернет",
  "text": "У меня не работает интернет уже 2 дня",
  "contact_info": {
    "phone": "+77001234567",
    "full_name": "Иван Иванов"
  },
  "telegram_user_id": 123456789,
  "telegram_chat_id": 123456789,
  "telegram_username": "ivan_ivanov"
}
```

### WhatsApp

**POST `/api/whatsapp/analyze`**
```json
{
  "text": "Какие тарифы на интернет?",
  "from_number": "+77001234567",
  "conversation_history": [],
  "contact_info": {
    "phone": "+77001234567"
  }
}
```

**POST `/api/whatsapp/create-ticket`**
```json
{
  "source": "whatsapp",
  "subject": "Не работает интернет",
  "text": "У меня не работает интернет",
  "contact_info": {
    "phone": "+77001234567"
  },
  "whatsapp_number": "+77001234567"
}
```

## Как это работает

### 1. Пользователь отправляет сообщение

### 2. Бот анализирует через RAG:
- Создает embedding для запроса
- Ищет в базе знаний (`chunks` таблица)
- Генерирует ответ используя найденную информацию
- Определяет категорию и приоритет

### 3. Если может ответить:
- Отправляет ответ пользователю
- Сохраняет в conversation_history

### 4. Если не может ответить:
- Предлагает создать тикет
- Создает тикет с автоматической классификацией
- Отправляет подтверждение пользователю

## Особенности

- ✅ **Единая RAG логика** - все боты используют одну и ту же логику из `public_chat.py`
- ✅ **История разговора** - боты помнят контекст диалога
- ✅ **Автоматическая классификация** - тикеты автоматически классифицируются
- ✅ **Определение типа клиента** - корпоративный/частный
- ✅ **Создание тикетов** - автоматическое создание при необходимости

## Проверка работы

1. **Запустите backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Запустите Telegram бота:**
   ```bash
   cd telegram_bot
   source venv/bin/activate
   python bot.py
   ```

3. **Запустите WhatsApp бота:**
   ```bash
   cd whatsapp_bot
   npm start
   ```

4. **Отправьте сообщение боту:**
   - Telegram: найдите вашего бота и отправьте сообщение
   - WhatsApp: отправьте сообщение на номер бота

5. **Проверьте логи:**
   - Backend должен показывать запросы к `/api/telegram/analyze` или `/api/whatsapp/analyze`
   - Боты должны отвечать используя RAG

## Troubleshooting

### Telegram бот не отвечает
- Проверьте `TELEGRAM_BOT_TOKEN` в `.env`
- Проверьте что backend запущен и доступен
- Проверьте `TELEGRAM_BOT_API_KEY` совпадает в backend и боте

### WhatsApp бот не отвечает
- Проверьте что отсканировали QR-код
- Проверьте `API_URL` и `WHATSAPP_BOT_API_KEY`
- Проверьте что backend запущен

### RAG не работает
- Убедитесь что база знаний заполнена (запустите `ingest.py`)
- Проверьте `OPENAI_API_KEY` в backend `.env`
- Проверьте что таблица `chunks` содержит данные

## Готово! ✅

Теперь оба бота подключены к вашему бэкенду с RAG и используют единую логику для ответов на вопросы пользователей.

