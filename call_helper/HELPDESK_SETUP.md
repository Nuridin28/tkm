# Настройка Help Desk системы с тикетами

## Шаги настройки

### 1. Создание таблицы tickets в Supabase

Выполните SQL скрипт `supabase_tickets_table.sql` в Supabase SQL Editor:

1. Откройте Supabase Dashboard
2. Перейдите в SQL Editor
3. Скопируйте содержимое файла `supabase_tickets_table.sql`
4. Выполните скрипт

### 2. Структура API запроса

API endpoint `/api/chat` теперь принимает дополнительные параметры:

```json
{
  "message": "Текст сообщения пользователя",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "user_id": "user123",  // Опционально, по умолчанию "anonymous"
  "language": "ru"       // Опционально, по умолчанию "ru" (ru|kz|en)
}
```

### 3. Структура ответа API

```json
{
  "answer": "Ответ ассистента",
  "sources": [
    {
      "content": "...",
      "page": 1,
      "source_type": "kazakhtelecom",
      "similarity": 0.85
    }
  ],
  "confidence": 0.8,
  "ticketCreated": false,
  "requiresClientType": false  // true, если нужно уточнить тип клиента
}
```

### 4. Логика работы системы

#### Определение типа клиента

Система автоматически определяет тип клиента из истории переписки:
- **Корпоративный**: "корпоратив", "бизнес", "компания", "организация", "юридическое лицо"
- **Частное лицо**: "частное лицо", "физическое лицо", "домашний", "личный"

Если тип клиента не определен, система возвращает `requiresClientType: true` и просит уточнить.

#### Создание тикета

Тикет создается автоматически, если:
- Модель определяет, что требуется вмешательство сотрудника
- Нужен выезд на объект
- Требуется решение технической проблемы
- Информации в документации недостаточно (confidence < 0.8)

#### Категории тикетов

Система автоматически определяет категорию на основе содержимого:
- **network**: проблемы с интернетом, VPN, сетью
- **telephony**: проблемы с телефонией
- **tv**: проблемы с телевидением
- **billing**: вопросы оплаты, тарифов, счетов
- **equipment**: проблемы с оборудованием
- **other**: прочее

#### Приоритеты

- **critical**: срочные проблемы, полное отсутствие связи
- **high**: важные проблемы, проблемы с оплатой
- **medium**: стандартные вопросы
- **low**: информационные запросы

### 5. Обновление фронтенда

Если вы используете `ChatInterface.tsx`, убедитесь, что он отправляет `user_id` и `language`:

```typescript
const response = await fetch("/api/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: input,
    history: messages.map(m => ({ role: m.role, content: m.content })),
    user_id: "user123",  // Добавьте user_id
    language: "ru"       // Добавьте language
  }),
});
```

### 6. Поля тикета

Каждый тикет содержит:
- `user_id`: ID пользователя
- `client_type`: "corporate" | "private"
- `language`: "ru" | "kz" | "en"
- `category`: категория проблемы
- `subcategory`: подкатегория
- `department`: отдел для обработки
- `priority`: приоритет
- `confidence`: уверенность модели (0.0-1.0)
- `content`: полный текст запроса и история переписки
- `status`: "open" | "in_progress" | "resolved" | "closed"

### 7. Просмотр тикетов

Тикеты можно просматривать в Supabase:
1. Откройте Supabase Dashboard
2. Перейдите в Table Editor
3. Выберите таблицу `tickets`

Или используйте SQL запрос:

```sql
SELECT * FROM public.tickets 
WHERE status = 'open' 
ORDER BY created_at DESC;
```

