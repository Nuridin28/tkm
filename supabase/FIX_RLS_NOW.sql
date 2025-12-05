-- СРОЧНОЕ ИСПРАВЛЕНИЕ: Устранение бесконечной рекурсии в RLS политиках
-- Выполните этот SQL в Supabase SQL Editor

-- Шаг 1: Удалить проблемные политики
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Admins can view all users" ON public.users;

-- Шаг 2: Создать исправленные политики БЕЗ рекурсии

-- Политика 1: Пользователь может видеть свой профиль
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Политика 2: Все авторизованные пользователи могут видеть всех
-- (Исправлено: убрана проверка роли через users, чтобы избежать рекурсии)
CREATE POLICY "Authenticated users can view all users"
    ON public.users FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- Шаг 3: Проверить политики
SELECT 
    policyname,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public' 
  AND tablename = 'users';

-- Шаг 4: Протестировать запрос (должно работать без ошибки)
SELECT id, email, name, role 
FROM public.users 
WHERE id = 'a56ae3d5-b79d-4c9c-b295-7a2abb4f991d';

