-- БЫСТРОЕ СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ
-- Выполните этот SQL ПОСЛЕ создания пользователей через Supabase Dashboard
-- Authentication > Users > Add user

-- Шаг 1: Создайте пользователей через Dashboard с этими данными:
-- admin@test.com / admin123
-- operator@test.com / operator123
-- engineer@test.com / engineer123
-- agent@test.com / agent123
-- supervisor@test.com / supervisor123

-- Шаг 2: Выполните этот SQL для назначения ролей:

DO $$
DECLARE
    v_tech_support_dept_id UUID;
    v_network_dept_id UUID;
BEGIN
    -- Получаем ID департаментов
    SELECT id INTO v_tech_support_dept_id FROM public.departments WHERE name = 'TechSupport' LIMIT 1;
    SELECT id INTO v_network_dept_id FROM public.departments WHERE name = 'Network' LIMIT 1;
    
    -- Администратор
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT id, 'admin@test.com', 'Администратор', 'admin', NOW(), NOW()
    FROM auth.users WHERE email = 'admin@test.com'
    ON CONFLICT (id) DO UPDATE 
    SET name = 'Администратор', role = 'admin', updated_at = NOW();
    
    -- Оператор техподдержки
    INSERT INTO public.users (id, email, name, role, department_id, created_at, updated_at)
    SELECT id, 'operator@test.com', 'Оператор Техподдержки', 'department_user', v_tech_support_dept_id, NOW(), NOW()
    FROM auth.users WHERE email = 'operator@test.com'
    ON CONFLICT (id) DO UPDATE 
    SET name = 'Оператор Техподдержки', role = 'department_user', 
        department_id = v_tech_support_dept_id, updated_at = NOW();
    
    -- Инженер
    INSERT INTO public.users (id, email, name, role, department_id, created_at, updated_at)
    SELECT id, 'engineer@test.com', 'Инженер', 'engineer', v_network_dept_id, NOW(), NOW()
    FROM auth.users WHERE email = 'engineer@test.com'
    ON CONFLICT (id) DO UPDATE 
    SET name = 'Инженер', role = 'engineer', 
        department_id = v_network_dept_id, updated_at = NOW();
    
    -- Call Agent
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT id, 'agent@test.com', 'Оператор Колл-центра', 'call_agent', NOW(), NOW()
    FROM auth.users WHERE email = 'agent@test.com'
    ON CONFLICT (id) DO UPDATE 
    SET name = 'Оператор Колл-центра', role = 'call_agent', updated_at = NOW();
    
    -- Супервизор
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT id, 'supervisor@test.com', 'Супервизор', 'supervisor', NOW(), NOW()
    FROM auth.users WHERE email = 'supervisor@test.com'
    ON CONFLICT (id) DO UPDATE 
    SET name = 'Супервизор', role = 'supervisor', updated_at = NOW();
    
    RAISE NOTICE '✅ Пользователи созданы/обновлены успешно!';
END $$;

-- Проверка созданных пользователей
SELECT 
    u.email,
    u.name,
    u.role,
    d.name as department,
    u.created_at
FROM public.users u
LEFT JOIN public.departments d ON u.department_id = d.id
ORDER BY u.role, u.email;

