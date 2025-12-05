-- Создание профиля для пользователя a56ae3d5-b79d-4c9c-b295-7a2abb4f991d
-- Выполните этот SQL в Supabase SQL Editor

INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    id, 
    email, 
    COALESCE(raw_user_meta_data->>'name', 'Пользователь') as name,
    COALESCE(raw_user_meta_data->>'role', 'admin') as role,  -- По умолчанию admin, измените если нужно
    NOW(), 
    NOW()
FROM auth.users 
WHERE id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d'
ON CONFLICT (id) DO UPDATE 
SET 
    email = EXCLUDED.email,
    name = COALESCE(EXCLUDED.name, users.name),
    role = COALESCE(EXCLUDED.role, users.role),
    updated_at = NOW();

-- Проверка: посмотреть созданный профиль
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    d.name as department,
    u.created_at
FROM public.users u
LEFT JOIN public.departments d ON u.department_id = d.id
WHERE u.id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

