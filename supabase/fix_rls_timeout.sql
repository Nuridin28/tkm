-- Исправление проблемы с таймаутом запросов к public.users
-- Проблема: RLS политика может блокировать запросы или создавать циклические зависимости

-- Вариант 1: Временно отключить RLS для тестирования (НЕ для production!)
-- ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;

-- Вариант 2: Упростить RLS политику (РЕКОМЕНДУЕТСЯ)
-- Удалить старую политику и создать более простую

-- Удалить старые политики
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Admins can view all users" ON public.users;

-- Создать упрощенную политику для просмотра своего профиля
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Создать политику для админов (без циклической зависимости)
CREATE POLICY "Admins can view all users"
    ON public.users FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM auth.users
            WHERE auth.users.id = auth.uid()
            AND (
                auth.users.raw_user_meta_data->>'role' = 'admin'
                OR auth.users.email LIKE '%admin%'
            )
        )
    );

-- Вариант 3: Создать профиль пользователя напрямую (если RLS блокирует)
-- Используйте service_role key для этого запроса
INSERT INTO public.users (id, email, name, role, created_at, updated_at)
VALUES (
    'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d',
    (SELECT email FROM auth.users WHERE id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d'),
    'Пользователь',
    'admin',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE 
SET updated_at = NOW();

-- Проверка: посмотреть все политики
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'users';

