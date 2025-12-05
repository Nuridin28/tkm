-- СРОЧНОЕ ОБНОВЛЕНИЕ РОЛИ ДЛЯ admin@test.com
-- Выполните этот SQL в Supabase SQL Editor

-- Обновить роль на admin для пользователя admin@test.com
UPDATE public.users
SET 
    role = 'admin',
    name = 'Администратор',
    updated_at = NOW()
WHERE email = 'admin@test.com'
   OR id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

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

