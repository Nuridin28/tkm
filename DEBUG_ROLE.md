# Отладка проблемы с ролями

## Проблема
Админ логинится, но перенаправляется на страницу департамента вместо админ панели.

## Шаги для отладки:

### 1. Проверьте консоль браузера (F12)
После логина должны быть логи:
- `"✅ User profile loaded successfully: {role: 'admin', ...}"`
- `"✅ Redirecting based on role: admin"`
- `"→ Redirecting to /admin (admin/supervisor)"`

### 2. Проверьте роль в базе данных

Выполните SQL в Supabase SQL Editor:

```sql
-- Проверить роль текущего пользователя
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    u.created_at
FROM public.users u
WHERE u.email = 'ваш-email@example.com';  -- Замените на ваш email
```

### 3. Если роль не 'admin', обновите её:

```sql
-- Обновить роль на admin
UPDATE public.users
SET role = 'admin', updated_at = NOW()
WHERE email = 'ваш-email@example.com';  -- Замените на ваш email

-- Проверить результат
SELECT id, email, name, role FROM public.users WHERE email = 'ваш-email@example.com';
```

### 4. Если профиль не загружается:

```sql
-- Создать/обновить профиль для вашего пользователя
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    id, 
    email, 
    'Администратор' as name,
    'admin' as role,
    NOW(), 
    NOW()
FROM auth.users 
WHERE email = 'ваш-email@example.com'  -- Замените на ваш email
ON CONFLICT (id) DO UPDATE 
SET 
    role = 'admin',
    name = 'Администратор',
    updated_at = NOW();
```

### 5. Проверьте RLS политики:

```sql
-- Проверить, может ли пользователь читать свой профиль
SELECT 
    policyname,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'users';
```

## Что проверить в консоли:

1. Откройте консоль браузера (F12)
2. Войдите в систему
3. Проверьте логи:
   - `"🔍 Loading user profile for: [id]"`
   - `"✅ User profile loaded successfully: {role: '...'}"`
   - `"✅ Redirecting based on role: ..."`

Если видите `"⚠️ Profile not found"` - значит профиль не создан в `public.users`.

Если роль не 'admin' - обновите её через SQL выше.

