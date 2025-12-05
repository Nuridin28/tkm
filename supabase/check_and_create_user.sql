-- Проверка и создание профиля пользователя
-- Выполните этот SQL в Supabase SQL Editor

-- Шаг 1: Проверить, существует ли пользователь в auth.users
SELECT 
    id, 
    email, 
    created_at,
    raw_user_meta_data
FROM auth.users 
WHERE id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- Шаг 2: Проверить, существует ли профиль в public.users
SELECT 
    id, 
    email, 
    name, 
    role,
    created_at
FROM public.users 
WHERE id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- Шаг 3: Создать профиль, если его нет
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    au.id, 
    au.email, 
    COALESCE(au.raw_user_meta_data->>'name', 'Пользователь') as name,
    COALESCE(au.raw_user_meta_data->>'role', 'admin') as role,
    NOW(), 
    NOW()
FROM auth.users au
WHERE au.id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d'
AND NOT EXISTS (
    SELECT 1 FROM public.users pu WHERE pu.id = au.id
)
ON CONFLICT (id) DO UPDATE 
SET 
    email = EXCLUDED.email,
    updated_at = NOW();

-- Шаг 4: Проверить результат
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    u.created_at,
    u.updated_at
FROM public.users u
WHERE u.id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- Шаг 5: Проверить RLS политики
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'users';

