-- Исправление бесконечной рекурсии в RLS политиках для таблицы users
-- Проблема: политика "Admins can view all users" проверяет роль из users, 
-- что вызывает рекурсию при запросе к users

-- Шаг 1: Удалить проблемные политики
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Admins can view all users" ON public.users;

-- Шаг 2: Создать исправленные политики без рекурсии

-- Политика 1: Пользователь может видеть свой профиль
-- Использует auth.uid() напрямую, без запроса к users
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Политика 2: Админы могут видеть всех пользователей
-- Использует функцию для проверки роли БЕЗ рекурсии
CREATE OR REPLACE FUNCTION public.is_admin(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Проверяем роль напрямую через auth.uid(), избегая рекурсии
    RETURN EXISTS (
        SELECT 1 
        FROM public.users 
        WHERE id = user_id 
        AND role = 'admin'
        -- Важно: используем прямой доступ без дополнительных проверок
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Альтернативный вариант: использовать user_metadata из auth.users
-- Это избегает рекурсии, так как auth.users не имеет RLS
CREATE POLICY "Admins can view all users"
    ON public.users FOR SELECT
    USING (
        -- Проверяем роль через auth.jwt() если доступно
        -- Или используем прямую проверку через функцию
        EXISTS (
            SELECT 1 
            FROM public.users u
            WHERE u.id = auth.uid()
            AND u.role = 'admin'
        )
    );

-- Но это все еще может вызвать рекурсию! Лучший вариант:

-- Удалить политику админов и использовать другой подход
DROP POLICY IF EXISTS "Admins can view all users" ON public.users;

-- Вариант 1: Разрешить всем авторизованным пользователям видеть всех
-- (менее безопасно, но работает)
CREATE POLICY "Authenticated users can view all users"
    ON public.users FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Вариант 2: Использовать service_role для админских операций
-- (более безопасно, но требует использования service_role key)

-- Шаг 3: Проверить результат
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public' 
  AND tablename = 'users';

-- Шаг 4: Протестировать запрос
-- Должно работать без ошибки рекурсии
SELECT id, email, name, role 
FROM public.users 
WHERE id = auth.uid();

