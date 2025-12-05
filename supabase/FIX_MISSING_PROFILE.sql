-- Исправление: создание профиля в public.users для пользователя admin@test.com
-- Выполните этот SQL в Supabase SQL Editor

-- Проверить, существует ли профиль
SELECT 
    id,
    email,
    name,
    role,
    created_at
FROM public.users
WHERE email = 'admin@test.com'
   OR id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- Создать профиль, если его нет
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
  AND au.id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d'
  AND NOT EXISTS (
    SELECT 1 FROM public.users pu WHERE pu.id = au.id
  )
ON CONFLICT (id) DO UPDATE 
SET 
    role = 'admin',
    name = 'Администратор',
    updated_at = NOW();

-- Проверить результат
SELECT 
    id,
    email,
    name,
    role,
    CASE 
        WHEN role = 'admin' THEN '✅ Правильно - роль admin'
        ELSE '❌ Неправильно - роль ' || role
    END as status
FROM public.users
WHERE email = 'admin@test.com'
   OR id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

