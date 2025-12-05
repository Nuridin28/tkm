-- Быстрое создание/обновление профиля пользователя
-- Замените USER_ID на реальный ID пользователя из логов

-- Вариант 1: Создать профиль для конкретного пользователя по ID
-- (замените USER_ID на ID из консоли браузера)
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    id, 
    email, 
    COALESCE(raw_user_meta_data->>'name', 'Пользователь') as name,
    COALESCE(raw_user_meta_data->>'role', 'department_user') as role,
    NOW(), 
    NOW()
FROM auth.users 
WHERE id = 'USER_ID'  -- ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ID
ON CONFLICT (id) DO UPDATE 
SET 
    email = EXCLUDED.email,
    name = COALESCE(EXCLUDED.name, users.name),
    role = COALESCE(EXCLUDED.role, users.role),
    updated_at = NOW();

-- Вариант 2: Создать профили для ВСЕХ пользователей из auth.users, у которых нет профиля
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    au.id, 
    au.email, 
    COALESCE(au.raw_user_meta_data->>'name', 'Пользователь') as name,
    COALESCE(au.raw_user_meta_data->>'role', 'department_user') as role,
    NOW(), 
    NOW()
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL  -- Только пользователи без профиля
ON CONFLICT (id) DO NOTHING;

-- Вариант 3: Для конкретного пользователя по email (если знаете email)
-- Замените 'your-email@example.com' на реальный email
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
SELECT 
    au.id, 
    au.email, 
    'Пользователь' as name,
    'department_user' as role,
    NOW(), 
    NOW()
FROM auth.users au
WHERE au.email = 'your-email@example.com'  -- ЗАМЕНИТЕ НА РЕАЛЬНЫЙ EMAIL
ON CONFLICT (id) DO UPDATE 
SET updated_at = NOW();

-- Проверка: посмотреть всех пользователей с профилями
SELECT 
    u.id,
    u.email,
    u.name,
    u.role,
    d.name as department,
    u.created_at
FROM public.users u
LEFT JOIN public.departments d ON u.department_id = d.id
ORDER BY u.created_at DESC;

