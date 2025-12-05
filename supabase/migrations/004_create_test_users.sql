-- Создание тестовых пользователей
-- ВНИМАНИЕ: Эти пользователи создаются для разработки и тестирования
-- В production используйте Supabase Auth UI или API для регистрации

-- Функция для создания пользователя с автоматическим созданием записи в public.users
CREATE OR REPLACE FUNCTION create_test_user(
    p_email TEXT,
    p_password TEXT,
    p_name TEXT,
    p_role TEXT
) RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    -- Создаем пользователя в auth.users через Supabase Auth
    -- ВНИМАНИЕ: В Supabase это обычно делается через API или Dashboard
    -- Здесь мы создаем только запись в public.users, предполагая что auth пользователь уже создан
    
    -- Генерируем UUID для пользователя
    v_user_id := gen_random_uuid();
    
    -- Вставляем запись в public.users
    -- В реальности auth.uid() будет использоваться из auth.users
    -- Для тестирования используем сгенерированный UUID
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    VALUES (v_user_id, p_email, p_name, p_role, NOW(), NOW())
    ON CONFLICT (id) DO UPDATE
    SET email = p_email, name = p_name, role = p_role, updated_at = NOW();
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Альтернативный подход: создание пользователей через Supabase Auth Admin API
-- Используйте этот SQL только если у вас есть доступ к auth.users напрямую

-- Создание тестовых пользователей (требует выполнения через Supabase Dashboard или Admin API)
-- Для создания через SQL нужно использовать Supabase Auth Admin функции

-- ВАРИАНТ 1: Создание через Supabase Dashboard (рекомендуется)
-- 1. Перейдите в Authentication > Users > Add user
-- 2. Создайте пользователей с этими данными:
--    - admin@test.com / password: admin123
--    - operator@test.com / password: operator123
--    - engineer@test.com / password: engineer123
--    - agent@test.com / password: agent123
-- 3. Затем выполните SQL ниже для обновления ролей

-- ВАРИАНТ 2: SQL для обновления ролей после создания через Dashboard
-- Выполните после создания пользователей через Dashboard

-- Получаем ID департаментов для назначения
DO $$
DECLARE
    v_tech_support_dept_id UUID;
    v_network_dept_id UUID;
    v_sales_dept_id UUID;
    v_admin_user_id UUID;
    v_operator_user_id UUID;
    v_engineer_user_id UUID;
    v_agent_user_id UUID;
BEGIN
    -- Получаем ID департаментов
    SELECT id INTO v_tech_support_dept_id FROM public.departments WHERE name = 'TechSupport' LIMIT 1;
    SELECT id INTO v_network_dept_id FROM public.departments WHERE name = 'Network' LIMIT 1;
    SELECT id INTO v_sales_dept_id FROM public.departments WHERE name = 'Sales' LIMIT 1;
    
    -- Создаем/обновляем пользователей в public.users
    -- Замените UUID на реальные ID из auth.users после создания через Dashboard
    
    -- Администратор
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT 
        id,
        'admin@test.com',
        'Администратор',
        'admin',
        NOW(),
        NOW()
    FROM auth.users
    WHERE email = 'admin@test.com'
    ON CONFLICT (id) DO UPDATE
    SET name = 'Администратор', role = 'admin', updated_at = NOW();
    
    -- Оператор техподдержки
    INSERT INTO public.users (id, email, name, role, department_id, created_at, updated_at)
    SELECT 
        id,
        'operator@test.com',
        'Оператор Техподдержки',
        'department_user',
        v_tech_support_dept_id,
        NOW(),
        NOW()
    FROM auth.users
    WHERE email = 'operator@test.com'
    ON CONFLICT (id) DO UPDATE
    SET name = 'Оператор Техподдержки', role = 'department_user', 
        department_id = v_tech_support_dept_id, updated_at = NOW();
    
    -- Инженер
    INSERT INTO public.users (id, email, name, role, department_id, created_at, updated_at)
    SELECT 
        id,
        'engineer@test.com',
        'Инженер',
        'engineer',
        v_network_dept_id,
        NOW(),
        NOW()
    FROM auth.users
    WHERE email = 'engineer@test.com'
    ON CONFLICT (id) DO UPDATE
    SET name = 'Инженер', role = 'engineer', 
        department_id = v_network_dept_id, updated_at = NOW();
    
    -- Call Agent
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT 
        id,
        'agent@test.com',
        'Оператор Колл-центра',
        'call_agent',
        NOW(),
        NOW()
    FROM auth.users
    WHERE email = 'agent@test.com'
    ON CONFLICT (id) DO UPDATE
    SET name = 'Оператор Колл-центра', role = 'call_agent', updated_at = NOW();
    
    -- Супервизор
    INSERT INTO public.users (id, email, name, role, created_at, updated_at)
    SELECT 
        id,
        'supervisor@test.com',
        'Супервизор',
        'supervisor',
        NOW(),
        NOW()
    FROM auth.users
    WHERE email = 'supervisor@test.com'
    ON CONFLICT (id) DO UPDATE
    SET name = 'Супервизор', role = 'supervisor', updated_at = NOW();
END $$;

-- ВАРИАНТ 3: Быстрое создание через SQL (если есть прямой доступ к auth.users)
-- ⚠️ ВНИМАНИЕ: Это работает только если у вас есть права на создание в auth.users
-- Обычно это требует использования Supabase Admin API или Dashboard

-- Для создания паролей используйте Supabase Dashboard или этот Python скрипт:
/*
import hashlib
import secrets

def generate_password_hash(password):
    # Supabase использует bcrypt, но для простоты можно использовать SHA256
    return hashlib.sha256(password.encode()).hexdigest()

# Пароли для тестовых пользователей:
# admin@test.com: admin123
# operator@test.com: operator123  
# engineer@test.com: engineer123
# agent@test.com: agent123
# supervisor@test.com: supervisor123
*/

