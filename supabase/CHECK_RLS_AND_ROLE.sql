-- Проверка RLS политик и роли пользователя
-- Выполните этот SQL в Supabase SQL Editor

-- 1. Проверить роль напрямую в базе
SELECT 
    id,
    email,
    name,
    role,
    created_at,
    updated_at
FROM public.users
WHERE email = 'admin@test.com'
   OR id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- 2. Проверить RLS политики для таблицы users
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
WHERE schemaname = 'public' 
  AND tablename = 'users';

-- 3. Проверить, включен ли RLS
SELECT 
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public' 
  AND tablename = 'users';

-- 4. Проверить текущего пользователя auth
SELECT 
    auth.uid() as current_user_id,
    auth.email() as current_user_email;

-- 5. Симуляция запроса с RLS (от имени пользователя)
-- Это покажет, что вернет запрос с учетом RLS
SET LOCAL request.jwt.claim.sub = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

SELECT 
    id,
    email,
    name,
    role
FROM public.users
WHERE id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- 6. Принудительно обновить роль (на случай если есть скрытые символы)
UPDATE public.users
SET 
    role = TRIM(BOTH FROM 'admin'),
    updated_at = NOW()
WHERE email = 'admin@test.com'
   OR id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

-- 7. Финальная проверка
SELECT 
    id,
    email,
    name,
    role,
    LENGTH(role) as role_length,
    ASCII(role) as role_first_char_ascii,
    CASE 
        WHEN role = 'admin' THEN '✅ Правильно'
        WHEN TRIM(role) = 'admin' THEN '⚠️ Есть пробелы: ' || role
        ELSE '❌ Неправильно: ' || role
    END as status
FROM public.users
WHERE email = 'admin@test.com'
   OR id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

