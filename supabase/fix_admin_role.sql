-- Исправление роли для пользователя admin@test.com
-- Выполните этот SQL в Supabase SQL Editor

-- Шаг 1: Проверить текущую роль
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    u.created_at,
    u.updated_at
FROM public.users u
WHERE u.email = 'admin@test.com';

-- Шаг 2: Обновить роль на admin
UPDATE public.users
SET 
    role = 'admin',
    name = 'Администратор',
    updated_at = NOW()
WHERE email = 'admin@test.com';

-- Шаг 3: Проверить результат
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    u.updated_at
FROM public.users u
WHERE u.email = 'admin@test.com';

-- Шаг 4: Если записи нет, создать её
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    au.id, 
    au.email, 
    'Администратор' as name,
    'admin' as role,
    NOW(), 
    NOW()
FROM auth.users au
WHERE au.email = 'admin@test.com'
AND NOT EXISTS (
    SELECT 1 FROM public.users pu WHERE pu.id = au.id
)
ON CONFLICT (id) DO UPDATE 
SET 
    role = 'admin',
    name = 'Администратор',
    updated_at = NOW();

-- Финальная проверка
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    CASE 
        WHEN u.role = 'admin' THEN '✅ Правильно'
        ELSE '❌ Неправильно - должно быть admin'
    END as status
FROM public.users u
WHERE u.email = 'admin@test.com';

