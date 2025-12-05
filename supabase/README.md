# Supabase Migrations

Этот каталог содержит SQL миграции для базы данных Supabase.

## Структура

- `001_initial_schema.sql` - Основные таблицы и структура БД
- `002_rls_policies.sql` - Row Level Security политики
- `003_seed_data.sql` - Начальные данные (департаменты, FAQ)

## Применение миграций

### Через Supabase CLI

```bash
supabase db push
```

### Вручную через Supabase Dashboard

1. Откройте Supabase Dashboard
2. Перейдите в SQL Editor
3. Выполните миграции по порядку

## Важные замечания

- Все timestamp поля используют `TIMESTAMPTZ` для поддержки timezone
- Включено расширение `vector` для работы с embeddings
- RLS (Row Level Security) включен на всех таблицах
- Функция `match_embeddings` используется для векторного поиска

